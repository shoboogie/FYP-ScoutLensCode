"""Step 3: Compute per-player per-match minutes played.

Uses normalised events and match metadata to calculate actual minutes
for each player in each match, handling:
  - Starting XI (minute 0 → substitution off or match end)
  - Substitutes (sub-on minute → sub-off or match end)
  - Red cards (minutes end at the sending-off event)

Output: data/processed/player_minutes.parquet
"""

from __future__ import annotations

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

DEFAULT_MATCH_DURATION = 95  # Minutes including average stoppage time


def _load_match_durations() -> dict[int, float]:
    """Build match_id → duration (minutes) from match metadata.

    Uses the last event minute + extra time as a proxy when explicit
    duration is unavailable. Falls back to DEFAULT_MATCH_DURATION.
    """
    durations: dict[int, float] = {}

    for comp in BIG_FIVE_COMPETITIONS:
        name = comp["name"]
        path = RAW_DIR / f"matches_{name.lower().replace(' ', '_')}.parquet"
        if not path.exists():
            continue
        mdf = pd.read_parquet(path)
        for _, row in mdf.iterrows():
            mid = int(row["match_id"])
            # StatsBomb match metadata doesn't always have explicit duration
            # We'll refine from events later if needed
            durations[mid] = DEFAULT_MATCH_DURATION

    logger.info("Match durations initialised for %d matches", len(durations))
    return durations


def _refine_durations_from_events(
    events: pd.DataFrame, durations: dict[int, float],
) -> dict[int, float]:
    """Refine match durations using the maximum event minute per match."""
    max_minutes = events.groupby("match_id")["minute"].max()
    for mid, max_min in max_minutes.items():
        mid = int(mid)
        # Use max event minute + 1 as a floor, but at least 90
        refined = max(float(max_min) + 1, 90.0)
        durations[mid] = max(durations.get(mid, DEFAULT_MATCH_DURATION), refined)
    return durations


def compute_minutes(force: bool = False) -> Path:
    """Compute per-player per-match minutes and save to parquet.

    Returns:
        Path to the output parquet.
    """
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    out_path = PROCESSED_DIR / "player_minutes.parquet"

    if out_path.exists() and not force:
        logger.info("Skipping minutes computation — cached at %s", out_path)
        return out_path

    events_path = PROCESSED_DIR / "events_normalised.parquet"
    if not events_path.exists():
        logger.error("Normalised events not found — run normalise_schema first.")
        return out_path

    events = pd.read_parquet(events_path)
    logger.info("Loaded normalised events: %d rows", len(events))

    # Load and refine match durations
    durations = _load_match_durations()
    durations = _refine_durations_from_events(events, durations)

    # ---- Identify player appearances per match ----
    # Starting XI: type_name == "Starting XI" contains lineup info
    # but individual players appear from minute 0
    # Substitutions: type_name == "Substitution"

    # Get unique (match_id, player_id, player_name, team_name) from events
    player_events = events[
        events["player_id"].notna()
    ][["match_id", "player_id", "player_name", "team_name", "league",
       "type_name", "minute", "position_name"]].copy()

    # Find substitution events
    subs = player_events[player_events["type_name"] == "Substitution"].copy()

    # Find players subbed OFF (the player in a Substitution event is the one going off)
    sub_off = subs.groupby(["match_id", "player_id"])["minute"].min().reset_index()
    sub_off.columns = ["match_id", "player_id", "sub_off_minute"]

    # Find players subbed ON via the substitution_replacement columns
    # In StatsBomb, 'substitution_replacement_name' / 'substitution_replacement_id'
    # tells us who came on
    sub_on_records: list[dict] = []
    if "substitution_replacement_id" in events.columns:
        sub_events = events[events["type_name"] == "Substitution"].copy()
        sub_events = sub_events[sub_events["substitution_replacement_id"].notna()]
        for _, row in sub_events.iterrows():
            sub_on_records.append({
                "match_id": row["match_id"],
                "player_id": int(row["substitution_replacement_id"]),
                "sub_on_minute": row["minute"],
            })
    sub_on = pd.DataFrame(sub_on_records)
    if not sub_on.empty:
        sub_on = sub_on.groupby(["match_id", "player_id"])["sub_on_minute"].min().reset_index()

    # Red cards — player's minutes end at the sending-off event.
    # Build separate masks for Foul Committed reds and Bad Behaviour reds,
    # then OR them together.
    red_card_types = ["Red Card", "Second Yellow"]
    foul_red_mask = pd.Series(False, index=events.index)
    behaviour_red_mask = pd.Series(False, index=events.index)

    if "foul_committed_card_name" in events.columns:
        foul_red_mask = (
            (events["type_name"] == "Foul Committed")
            & events["foul_committed_card_name"].isin(red_card_types)
        )
    if "bad_behaviour_card_name" in events.columns:
        behaviour_red_mask = (
            (events["type_name"] == "Bad Behaviour")
            & events["bad_behaviour_card_name"].isin(red_card_types)
        )

    red_cards_mask = foul_red_mask | behaviour_red_mask

    red_cards = events[red_cards_mask][["match_id", "player_id", "minute"]].copy()
    if not red_cards.empty:
        red_cards = red_cards.groupby(["match_id", "player_id"])["minute"].min().reset_index()
        red_cards.columns = ["match_id", "player_id", "red_card_minute"]

    # ---- Build per-player per-match records ----
    # Get each player's first and last event per match
    player_match = (
        player_events
        .groupby(["match_id", "player_id", "player_name", "team_name", "league"])
        .agg(
            first_minute=("minute", "min"),
            last_minute=("minute", "max"),
            primary_position=("position_name", lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else None),
        )
        .reset_index()
    )

    # Merge sub-on info
    if not sub_on.empty:
        player_match = player_match.merge(sub_on, on=["match_id", "player_id"], how="left")
    else:
        player_match["sub_on_minute"] = np.nan

    # Merge sub-off info
    player_match = player_match.merge(sub_off, on=["match_id", "player_id"], how="left")

    # Merge red card info
    if not red_cards.empty:
        player_match = player_match.merge(red_cards, on=["match_id", "player_id"], how="left")
    else:
        player_match["red_card_minute"] = np.nan

    # Determine start and end minutes
    # Start: sub_on_minute if subbed on, else 0 (starter)
    player_match["start_minute"] = player_match["sub_on_minute"].fillna(0)

    # End: earliest of sub_off, red_card, or match duration
    player_match["match_duration"] = player_match["match_id"].map(durations).fillna(DEFAULT_MATCH_DURATION)

    end_candidates = pd.DataFrame({
        "sub_off": player_match["sub_off_minute"],
        "red_card": player_match["red_card_minute"],
        "match_end": player_match["match_duration"],
    })
    player_match["end_minute"] = end_candidates.min(axis=1)

    # Compute minutes played
    player_match["minutes_played"] = (
        player_match["end_minute"] - player_match["start_minute"]
    ).clip(lower=0).round(0).astype(int)

    # Determine if player started
    player_match["started"] = player_match["sub_on_minute"].isna()

    # ---- QA check: per-team per-match totals ----
    team_totals = (
        player_match
        .groupby(["match_id", "team_name"])["minutes_played"]
        .sum()
        .reset_index()
    )
    team_totals = team_totals.merge(
        player_match[["match_id", "match_duration"]].drop_duplicates(),
        on="match_id",
    )
    team_totals["expected"] = team_totals["match_duration"] * 11
    team_totals["deviation_pct"] = (
        (team_totals["minutes_played"] - team_totals["expected"]).abs()
        / team_totals["expected"]
        * 100
    )

    outliers = team_totals[team_totals["deviation_pct"] > 5]
    if len(outliers) > 0:
        logger.warning(
            "%d team-match records deviate >5%% from expected (11 x duration). "
            "Median deviation: %.1f%%. This is often due to red cards or data gaps.",
            len(outliers), outliers["deviation_pct"].median(),
        )
    else:
        logger.info("QA check passed: all team-match totals within 5%% of expected.")

    # Select output columns
    output = player_match[[
        "player_id", "player_name", "match_id", "team_name",
        "league", "minutes_played", "started", "primary_position",
    ]].copy()

    # Ensure integer types
    output["player_id"] = output["player_id"].astype(int)
    output["match_id"] = output["match_id"].astype(int)
    output["minutes_played"] = output["minutes_played"].astype(int)

    output.to_parquet(out_path, index=False)
    logger.info(
        "Player minutes saved: %d records, %d unique players → %s",
        len(output), output["player_id"].nunique(), out_path,
    )

    return out_path


def run(force: bool = False) -> None:
    """Run minutes computation step."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    )
    logger.info("=== Step 3: Minutes computation ===")
    t0 = time.perf_counter()
    compute_minutes(force=force)
    logger.info("Minutes computation complete in %.1fs", time.perf_counter() - t0)


if __name__ == "__main__":
    run(force="--force" in sys.argv)
