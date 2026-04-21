"""Step 2: Normalise the raw StatsBomb event schema.

Reads cached parquet files from data/raw/, then:
  - Parses JSON-string location columns back into _x / _y floats
  - Standardises all column names to snake_case
  - Merges position data from lineups where position_name is null
  - Outputs a single events_normalised.parquet in data/processed/
"""

from __future__ import annotations

import json
import logging
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from app.utils.constants import BIG_FIVE_COMPETITIONS  # noqa: E402

logger = logging.getLogger(__name__)

RAW_DIR = Path(__file__).resolve().parents[1].parent / "data" / "raw"
PROCESSED_DIR = Path(__file__).resolve().parents[1].parent / "data" / "processed"

# Columns that contain serialised [x, y] lists we need to split
LOCATION_COLUMNS: list[str] = [
    "location",
    "pass_end_location",
    "carry_end_location",
    "shot_end_location",
    "goalkeeper_end_location",
]


def _parse_location(val: str | list | float) -> list | None:
    """Parse a location value that may be a JSON string, a list, or NaN."""
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return None
    if isinstance(val, list):
        return val
    if isinstance(val, str):
        try:
            parsed = json.loads(val)
            if isinstance(parsed, list):
                return parsed
        except (json.JSONDecodeError, TypeError):
            pass
    return None


def _split_location_column(df: pd.DataFrame, col: str) -> pd.DataFrame:
    """Split a location column into {col}_x and {col}_y float columns."""
    if col not in df.columns:
        return df

    parsed = df[col].apply(_parse_location)
    df[f"{col}_x"] = parsed.apply(lambda v: float(v[0]) if v and len(v) >= 2 else np.nan)
    df[f"{col}_y"] = parsed.apply(lambda v: float(v[1]) if v and len(v) >= 2 else np.nan)
    df = df.drop(columns=[col])
    return df


def _load_lineups() -> pd.DataFrame | None:
    """Load cached lineup data for position backfill."""
    lineup_path = RAW_DIR / "lineups_all.parquet"
    if not lineup_path.exists():
        logger.warning("No lineups file found at %s — skipping position merge", lineup_path)
        return None

    lineups = pd.read_parquet(lineup_path)
    logger.info("Loaded lineups: %d rows", len(lineups))
    return lineups


def _build_position_lookup(lineups: pd.DataFrame) -> dict[tuple[int, int], str]:
    """Build (player_id, match_id) → position_name lookup from lineups.

    StatsBomb lineups store positions as a list of dicts in a 'positions'
    column. We extract the most common position per player per match.
    """
    lookup: dict[tuple[int, int], str] = {}

    if "positions" not in lineups.columns:
        logger.warning("Lineups missing 'positions' column — cannot build lookup")
        return lookup

    for _, row in lineups.iterrows():
        pid = row.get("player_id")
        mid = row.get("match_id")
        positions_raw = row.get("positions")

        if pid is None or mid is None or positions_raw is None:
            continue

        # Parse positions — may be a JSON string or already a list
        if isinstance(positions_raw, str):
            try:
                positions_raw = json.loads(positions_raw)
            except (json.JSONDecodeError, TypeError):
                continue

        if isinstance(positions_raw, list) and len(positions_raw) > 0:
            # Take the first position (starting position) as canonical
            first_pos = positions_raw[0]
            if isinstance(first_pos, dict) and "position" in first_pos:
                pos_name = first_pos["position"]
                if isinstance(pos_name, dict):
                    pos_name = pos_name.get("name", "")
                if pos_name:
                    lookup[(int(pid), int(mid))] = pos_name

    logger.info("Position lookup built: %d entries", len(lookup))
    return lookup


def normalise(force: bool = False) -> Path:
    """Run schema normalisation on all cached event parquets.

    Returns:
        Path to the output normalised parquet.
    """
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    out_path = PROCESSED_DIR / "events_normalised.parquet"

    if out_path.exists() and not force:
        logger.info("Skipping normalisation — cached at %s", out_path)
        return out_path

    # Load all league event parquets
    frames: list[pd.DataFrame] = []
    for comp in BIG_FIVE_COMPETITIONS:
        name = comp["name"]
        parquet_path = RAW_DIR / f"events_{name.lower().replace(' ', '_')}.parquet"
        if not parquet_path.exists():
            logger.error("Missing events parquet for %s at %s", name, parquet_path)
            continue
        df = pd.read_parquet(parquet_path)
        df["league"] = name
        frames.append(df)
        logger.info("Loaded %s: %d events", name, len(df))

    if not frames:
        logger.error("No event data found — run ingest first.")
        return out_path

    events = pd.concat(frames, ignore_index=True)
    logger.info("Combined events: %d rows, %d columns", len(events), len(events.columns))

    # Rename columns to match CLAUDE.md spec (sb.competition_events uses
    # shorter names than the per-match sb.events() function)
    _RENAME_MAP = {
        "type": "type_name",
        "player": "player_name",
        "position": "position_name",
        "team": "team_name",
        "shot_outcome": "shot_outcome_name",
        "shot_type": "shot_type_name",
        "pass_outcome": "pass_outcome_name",
        "pass_technique": "pass_technique_name",
        "duel_type": "duel_type_name",
        "duel_outcome": "duel_outcome_name",
        "dribble_outcome": "dribble_outcome_name",
        "goalkeeper_position": "goalkeeper_position_name",
        "bad_behaviour_card": "bad_behaviour_card_name",
        "foul_committed_card": "foul_committed_card_name",
        "substitution_replacement": "substitution_replacement_name",
    }
    renames = {k: v for k, v in _RENAME_MAP.items() if k in events.columns}
    events = events.rename(columns=renames)
    logger.info("Renamed %d columns to match spec: %s", len(renames), list(renames.keys()))

    # Split location columns into _x / _y
    for col in LOCATION_COLUMNS:
        events = _split_location_column(events, col)
        logger.info("Split %s → %s_x, %s_y", col, col, col)

    # Merge position data from lineups where position_name is null
    lineups = _load_lineups()
    if lineups is not None:
        pos_lookup = _build_position_lookup(lineups)
        if pos_lookup:
            null_mask = events["position_name"].isna()
            null_count_before = null_mask.sum()

            def _fill_position(row: pd.Series) -> str | None:
                if pd.isna(row["position_name"]):
                    key = (int(row["player_id"]), int(row["match_id"]))
                    return pos_lookup.get(key)
                return row["position_name"]

            # Only apply to rows with null positions that have player_id and match_id
            valid_mask = null_mask & events["player_id"].notna() & events["match_id"].notna()
            if valid_mask.any():
                events.loc[valid_mask, "position_name"] = events.loc[valid_mask].apply(
                    _fill_position, axis=1,
                )
            null_count_after = events["position_name"].isna().sum()
            logger.info(
                "Position backfill: %d nulls before → %d after (%d filled)",
                null_count_before, null_count_after,
                null_count_before - null_count_after,
            )

    # Drop heavy columns not needed for feature engineering
    drop_cols = [
        "shot_freeze_frame", "related_events", "tactics",
        "shot_end_location_x", "shot_end_location_y",
        "goalkeeper_end_location_x", "goalkeeper_end_location_y",
    ]
    existing_drops = [c for c in drop_cols if c in events.columns]
    if existing_drops:
        events = events.drop(columns=existing_drops)
        logger.info("Dropped heavy columns: %s", existing_drops)

    events.to_parquet(out_path, index=False)
    logger.info("Normalised events saved: %d rows → %s", len(events), out_path)
    return out_path


def run(force: bool = False) -> None:
    """Run normalisation step."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    )
    logger.info("=== Step 2: Schema normalisation ===")
    t0 = time.perf_counter()
    normalise(force=force)
    logger.info("Normalisation complete in %.1fs", time.perf_counter() - t0)


if __name__ == "__main__":
    run(force="--force" in sys.argv)
