"""Step 1: Ingest StatsBomb Open Data for the Big Five leagues (2015/16).

Downloads competition events, match metadata, and lineup data via
statsbombpy, then caches everything as parquet files in data/raw/.
Subsequent runs skip already-cached leagues.
"""

from __future__ import annotations

import logging
import sys
import time
from pathlib import Path

import pandas as pd
from statsbombpy import sb

# ---------------------------------------------------------------------------
# Add project root so we can import app.utils.constants
# ---------------------------------------------------------------------------
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from app.utils.constants import BIG_FIVE_COMPETITIONS  # noqa: E402

logger = logging.getLogger(__name__)

RAW_DIR = Path(__file__).resolve().parents[1].parent / "data" / "raw"

# Map competition_id → (country, division) for sb.competition_events()
_COMP_LOOKUP: dict[int, tuple[str, str]] = {
    2:  ("England", "Premier League"),
    11: ("Spain", "La Liga"),
    9:  ("Germany", "1. Bundesliga"),
    12: ("Italy", "Serie A"),
    7:  ("France", "Ligue 1"),
}

MAX_RETRIES = 3
RETRY_DELAY_SECS = 5


def _sanitise_for_parquet(df: pd.DataFrame) -> pd.DataFrame:
    """Convert columns containing lists or dicts to JSON strings.

    Parquet cannot store Python lists/dicts natively. We serialise them
    here so the raw cache is always writable. The normalise step (Step 2)
    will parse and split these back into typed columns.
    """
    import json

    df = df.copy()
    for col in df.columns:
        sample = df[col].dropna().head(20)
        if len(sample) > 0 and isinstance(sample.iloc[0], (list, dict)):
            df[col] = df[col].apply(
                lambda v: json.dumps(v) if isinstance(v, (list, dict)) else v
            )
    return df


def _load_with_retry(func, *args, retries: int = MAX_RETRIES, **kwargs) -> pd.DataFrame:
    """Call a statsbombpy function with retry logic for network errors."""
    for attempt in range(1, retries + 1):
        try:
            return func(*args, **kwargs)
        except Exception as exc:
            if attempt == retries:
                raise
            logger.warning(
                "Attempt %d/%d failed for %s: %s — retrying in %ds",
                attempt, retries, func.__name__, exc, RETRY_DELAY_SECS,
            )
            time.sleep(RETRY_DELAY_SECS)
    # Unreachable, but keeps type-checkers happy
    return pd.DataFrame()


def ingest_events(force: bool = False) -> dict[str, Path]:
    """Download and cache competition events for all Big Five leagues.

    Args:
        force: Re-download even if cached parquet already exists.

    Returns:
        Dict mapping league name to its cached parquet path.
    """
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    cached: dict[str, Path] = {}

    for comp in BIG_FIVE_COMPETITIONS:
        comp_id = comp["competition_id"]
        name = comp["name"]
        out_path = RAW_DIR / f"events_{name.lower().replace(' ', '_')}.parquet"

        if out_path.exists() and not force:
            logger.info("Skipping %s — cached at %s", name, out_path)
            cached[name] = out_path
            continue

        country, division = _COMP_LOOKUP[comp_id]
        logger.info("Loading events for %s (%s)…", name, division)
        t0 = time.perf_counter()

        events = _load_with_retry(
            sb.competition_events,
            country=country,
            division=division,
            season="2015/2016",
            gender="male",
        )

        elapsed = time.perf_counter() - t0
        logger.info(
            "  %s: %d events loaded in %.1fs", name, len(events), elapsed,
        )

        # Ligue 1 warning for 3 missing matches
        if comp_id == 7 and len(events) < 500_000:
            logger.warning(
                "Ligue 1 has fewer events than expected — likely due to "
                "3 known missing matches (Bastia v Gazelec 22/11/15, "
                "Saint-Etienne v PSG 31/01/16, Troyes v Bordeaux 30/04/16)."
            )

        events = _sanitise_for_parquet(events)
        events.to_parquet(out_path, index=False)
        cached[name] = out_path

    return cached


def ingest_matches(force: bool = False) -> dict[str, Path]:
    """Download and cache match metadata for all Big Five leagues.

    Returns:
        Dict mapping league name to its cached parquet path.
    """
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    cached: dict[str, Path] = {}

    for comp in BIG_FIVE_COMPETITIONS:
        comp_id = comp["competition_id"]
        season_id = comp["season_id"]
        name = comp["name"]
        out_path = RAW_DIR / f"matches_{name.lower().replace(' ', '_')}.parquet"

        if out_path.exists() and not force:
            logger.info("Skipping matches for %s — cached", name)
            cached[name] = out_path
            continue

        logger.info("Loading match metadata for %s…", name)
        matches = _load_with_retry(sb.matches, competition_id=comp_id, season_id=season_id)
        matches = _sanitise_for_parquet(matches)
        matches.to_parquet(out_path, index=False)
        logger.info("  %s: %d matches", name, len(matches))
        cached[name] = out_path

    return cached


def ingest_lineups(match_ids: list[int] | None = None, force: bool = False) -> Path:
    """Download and cache lineup data.

    If *match_ids* is None, loads match IDs from cached match metadata.
    Lineups are concatenated into a single parquet file.

    Returns:
        Path to the cached lineups parquet.
    """
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RAW_DIR / "lineups_all.parquet"

    if out_path.exists() and not force:
        logger.info("Skipping lineups — cached at %s", out_path)
        return out_path

    # Gather match IDs from cached match metadata if not provided
    if match_ids is None:
        match_ids = []
        for comp in BIG_FIVE_COMPETITIONS:
            name = comp["name"]
            match_path = RAW_DIR / f"matches_{name.lower().replace(' ', '_')}.parquet"
            if match_path.exists():
                mdf = pd.read_parquet(match_path)
                match_ids.extend(mdf["match_id"].tolist())

    if not match_ids:
        logger.error("No match IDs available — run ingest_matches() first.")
        return out_path

    logger.info("Loading lineups for %d matches…", len(match_ids))
    all_lineups: list[pd.DataFrame] = []
    t0 = time.perf_counter()

    for i, mid in enumerate(match_ids, 1):
        if i % 200 == 0 or i == 1:
            logger.info("  Lineups progress: %d / %d", i, len(match_ids))
        try:
            lineup = _load_with_retry(sb.lineups, match_id=mid, retries=2)
            # sb.lineups returns a dict of {team_name: DataFrame}
            for team_name, team_df in lineup.items():
                team_df = team_df.copy()
                team_df["match_id"] = mid
                team_df["team_name"] = team_name
                all_lineups.append(team_df)
        except Exception as exc:
            logger.warning("Failed to load lineup for match %d: %s", mid, exc)

    if all_lineups:
        lineups_df = pd.concat(all_lineups, ignore_index=True)
        lineups_df = _sanitise_for_parquet(lineups_df)
        lineups_df.to_parquet(out_path, index=False)
        elapsed = time.perf_counter() - t0
        logger.info("Lineups: %d rows saved in %.1fs", len(lineups_df), elapsed)
    else:
        logger.error("No lineup data collected.")

    return out_path


def run(force: bool = False) -> None:
    """Run the full ingestion step."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    )
    logger.info("=== Step 1: StatsBomb data ingestion ===")
    t0 = time.perf_counter()

    ingest_events(force=force)
    ingest_matches(force=force)
    ingest_lineups(force=force)

    elapsed = time.perf_counter() - t0
    logger.info("Ingestion complete in %.1fs", elapsed)


if __name__ == "__main__":
    run(force="--force" in sys.argv)
