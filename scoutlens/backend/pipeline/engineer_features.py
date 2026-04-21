"""Step 5: Compute 42 per-90 features for every qualified player.

Reads events_normalised.parquet and qualified_players.parquet, then
computes features across 6 dimensions (Attacking, Chance Creation,
Passing, Carrying, Defending, Aerial/Physical).

All count-based features are per-90 normalised.
All ratio features default to 0.0 when the denominator is zero.
No NaN or Inf values in the output matrix.

Output: data/features/feature_matrix.parquet
"""

from __future__ import annotations

import logging
import math
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from app.utils.constants import (  # noqa: E402
    FEATURE_NAMES,
    GOAL_X,
    GOAL_Y,
    LONG_PASS_THRESHOLD,
    OPP_BOX_X_MIN,
    OPP_BOX_Y_MAX,
    OPP_BOX_Y_MIN,
    PROGRESSIVE_THRESHOLD,
    SWITCH_Y_THRESHOLD,
)

logger = logging.getLogger(__name__)

PROCESSED_DIR = Path(__file__).resolve().parents[1].parent / "data" / "processed"
FEATURES_DIR = Path(__file__).resolve().parents[1].parent / "data" / "features"


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _safe_ratio(numerator: float, denominator: float) -> float:
    """Compute ratio, returning 0.0 when denominator is zero."""
    if denominator == 0:
        return 0.0
    return numerator / denominator


def _per90(count: float, minutes: float) -> float:
    """Convert a raw count to per-90 rate."""
    if minutes == 0:
        return 0.0
    return (count / minutes) * 90


def _is_progressive(start_x: float, start_y: float, end_x: float, end_y: float) -> bool:
    """Check whether an action moves the ball progressively toward goal.

    An action is progressive if it moves the ball at least 10 metres
    closer to the opponent's goal centre (120, 40) on the StatsBomb
    120x80 pitch coordinate system.
    """
    start_dist = math.sqrt((GOAL_X - start_x) ** 2 + (GOAL_Y - start_y) ** 2)
    end_dist = math.sqrt((GOAL_X - end_x) ** 2 + (GOAL_Y - end_y) ** 2)
    return (start_dist - end_dist) >= PROGRESSIVE_THRESHOLD


def _in_opp_box(x: float, y: float) -> bool:
    """Check whether a coordinate is inside the opponent's penalty area."""
    return x > OPP_BOX_X_MIN and OPP_BOX_Y_MIN < y < OPP_BOX_Y_MAX


def _euclidean_distance(x1: float, y1: float, x2: float, y2: float) -> float:
    """Compute Euclidean distance between two points."""
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)


# ---------------------------------------------------------------------------
# Feature computation per player
# ---------------------------------------------------------------------------

def _compute_player_features(
    player_events: pd.DataFrame, minutes: float,
) -> dict[str, float]:
    """Compute all 42 features for a single player's season events.

    Args:
        player_events: All events for this player across the season.
        minutes: Total season minutes played.

    Returns:
        Dict mapping feature name to value.
    """
    features: dict[str, float] = {}

    # Pre-filter common event types
    shots = player_events[player_events["type_name"] == "Shot"]
    passes = player_events[player_events["type_name"] == "Pass"]
    carries = player_events[player_events["type_name"] == "Carry"]
    dribbles = player_events[player_events["type_name"] == "Dribble"]
    pressures = player_events[player_events["type_name"] == "Pressure"]

    # Completed passes: pass_outcome_name is NaN for completions
    completed_passes = passes[passes["pass_outcome_name"].isna()]

    # ── Dimension 1: Attacking Contribution (7) ─────────────────────

    total_xg = shots["shot_statsbomb_xg"].sum()
    total_shots = len(shots)
    shots_on_target = shots[shots["shot_outcome_name"].isin(["Saved", "Goal"])]
    goals = shots[shots["shot_outcome_name"] == "Goal"]
    non_penalty_shots = shots[shots["shot_type_name"] != "Penalty"]
    npxg = non_penalty_shots["shot_statsbomb_xg"].sum()

    # Touches in opponent's box — any event with location in opp box
    player_with_loc = player_events[
        player_events["location_x"].notna() & player_events["location_y"].notna()
    ]
    touches_in_box = player_with_loc.apply(
        lambda r: _in_opp_box(r["location_x"], r["location_y"]), axis=1
    ).sum()

    features["xg_per90"] = _per90(total_xg, minutes)
    features["shots_per90"] = _per90(total_shots, minutes)
    features["shots_on_target_per90"] = _per90(len(shots_on_target), minutes)
    features["goals_per90"] = _per90(len(goals), minutes)
    features["npxg_per90"] = _per90(npxg, minutes)
    features["touches_in_box_per90"] = _per90(touches_in_box, minutes)
    features["xg_per_shot"] = _safe_ratio(total_xg, total_shots)

    # ── Dimension 2: Chance Creation (7) ────────────────────────────

    shot_assists = passes[passes["pass_shot_assist"] == True]  # noqa: E712
    goal_assists = passes[passes["pass_goal_assist"] == True]  # noqa: E712

    # xA: count of shot-creating passes as proxy. True xA requires
    # cross-referencing the assisted shot's xG from a different player's
    # events, which isn't available in a single-player groupby. The
    # shot-assist count is a standard proxy used by FBref and StatsBomb IQ.
    xa = float(len(shot_assists))

    # Passes into box: completed passes ending in opponent box
    passes_with_end = completed_passes[
        completed_passes["pass_end_location_x"].notna()
        & completed_passes["pass_end_location_y"].notna()
    ]
    passes_into_box = passes_with_end.apply(
        lambda r: _in_opp_box(r["pass_end_location_x"], r["pass_end_location_y"]),
        axis=1,
    ).sum()

    # Through balls — spec: pass_technique_name == "Through Ball"
    through_balls = 0
    if "pass_technique_name" in passes.columns:
        through_balls = (passes["pass_technique_name"] == "Through Ball").sum()
    elif "pass_through_ball" in passes.columns:
        through_balls = (passes["pass_through_ball"] == True).sum()  # noqa: E712

    # Progressive passes: completed passes that move ball >=10m closer to goal
    prog_passes = 0
    if len(passes_with_end) > 0:
        prog_mask = passes_with_end.apply(
            lambda r: _is_progressive(
                r.get("location_x", 0) or 0, r.get("location_y", 0) or 0,
                r["pass_end_location_x"], r["pass_end_location_y"],
            )
            if pd.notna(r.get("location_x")) and pd.notna(r.get("location_y"))
            else False,
            axis=1,
        )
        prog_passes = prog_mask.sum()

    # Crosses — boolean column, must filter for True not just non-null
    crosses = 0
    if "pass_cross" in passes.columns:
        crosses = (passes["pass_cross"] == True).sum()  # noqa: E712

    features["xa_per90"] = _per90(xa, minutes)
    features["key_passes_per90"] = _per90(len(shot_assists), minutes)
    features["assists_per90"] = _per90(len(goal_assists), minutes)
    features["passes_into_box_per90"] = _per90(passes_into_box, minutes)
    features["through_balls_per90"] = _per90(through_balls, minutes)
    features["progressive_passes_per90"] = _per90(prog_passes, minutes)
    features["crosses_per90"] = _per90(crosses, minutes)

    # ── Dimension 3: Passing & Ball Control (7) ─────────────────────

    total_passes = len(passes)
    completed_count = len(completed_passes)

    # Progressive pass distance
    prog_pass_dist = 0.0
    if len(passes_with_end) > 0:
        for _, r in passes_with_end.iterrows():
            if pd.notna(r.get("location_x")) and pd.notna(r.get("location_y")):
                if _is_progressive(
                    r["location_x"], r["location_y"],
                    r["pass_end_location_x"], r["pass_end_location_y"],
                ):
                    # Forward distance = reduction in distance to goal
                    start_d = math.sqrt(
                        (GOAL_X - r["location_x"]) ** 2
                        + (GOAL_Y - r["location_y"]) ** 2
                    )
                    end_d = math.sqrt(
                        (GOAL_X - r["pass_end_location_x"]) ** 2
                        + (GOAL_Y - r["pass_end_location_y"]) ** 2
                    )
                    prog_pass_dist += start_d - end_d

    # Long passes
    long_passes = passes[passes["pass_length"] > LONG_PASS_THRESHOLD] if "pass_length" in passes.columns else pd.DataFrame()
    long_pass_total = len(long_passes)
    long_pass_completed = len(long_passes[long_passes["pass_outcome_name"].isna()]) if long_pass_total > 0 else 0

    # Switches of play: non-cross passes with abs(y-distance) > 40
    switches = 0
    if "pass_switch" in passes.columns:
        switches = (passes["pass_switch"] == True).sum()  # noqa: E712
    elif len(passes_with_end) > 0:
        non_cross = passes_with_end
        if "pass_cross" in non_cross.columns:
            non_cross = non_cross[non_cross["pass_cross"].isna()]
        if len(non_cross) > 0 and "location_y" in non_cross.columns:
            y_dist = (non_cross["pass_end_location_y"] - non_cross["location_y"]).abs()
            switches = (y_dist > SWITCH_Y_THRESHOLD).sum()

    # Passes under pressure completion %
    pressured_passes = passes[passes["under_pressure"] == True] if "under_pressure" in passes.columns else pd.DataFrame()  # noqa: E712
    pressured_completed = pressured_passes[pressured_passes["pass_outcome_name"].isna()] if len(pressured_passes) > 0 else pd.DataFrame()

    features["passes_attempted_per90"] = _per90(total_passes, minutes)
    features["pass_completion_pct"] = _safe_ratio(completed_count, total_passes) * 100
    features["progressive_pass_distance_per90"] = _per90(prog_pass_dist, minutes)
    features["long_passes_per90"] = _per90(long_pass_total, minutes)
    features["long_pass_completion_pct"] = _safe_ratio(long_pass_completed, long_pass_total) * 100
    features["switches_per90"] = _per90(switches, minutes)
    features["passes_under_pressure_pct"] = _safe_ratio(len(pressured_completed), len(pressured_passes)) * 100

    # ── Dimension 4: Ball Carrying (7) ──────────────────────────────

    carries_with_end = carries[
        carries["carry_end_location_x"].notna()
        & carries["carry_end_location_y"].notna()
        & carries["location_x"].notna()
        & carries["location_y"].notna()
    ]

    # Progressive carries
    prog_carries = 0
    carry_distance = 0.0
    prog_carry_distance = 0.0
    carries_into_box = 0

    for _, r in carries_with_end.iterrows():
        dist = _euclidean_distance(
            r["location_x"], r["location_y"],
            r["carry_end_location_x"], r["carry_end_location_y"],
        )
        carry_distance += dist

        if _is_progressive(
            r["location_x"], r["location_y"],
            r["carry_end_location_x"], r["carry_end_location_y"],
        ):
            prog_carries += 1
            start_d = math.sqrt(
                (GOAL_X - r["location_x"]) ** 2
                + (GOAL_Y - r["location_y"]) ** 2
            )
            end_d = math.sqrt(
                (GOAL_X - r["carry_end_location_x"]) ** 2
                + (GOAL_Y - r["carry_end_location_y"]) ** 2
            )
            prog_carry_distance += start_d - end_d

        if _in_opp_box(r["carry_end_location_x"], r["carry_end_location_y"]):
            carries_into_box += 1

    # Dribbles
    total_dribbles = len(dribbles)
    successful_dribbles = len(
        dribbles[dribbles["dribble_outcome_name"] == "Complete"]
    ) if total_dribbles > 0 else 0

    # Ball receipts
    ball_receipts = len(
        player_events[player_events["type_name"] == "Ball Receipt*"]
    )

    features["progressive_carries_per90"] = _per90(prog_carries, minutes)
    features["carry_distance_per90"] = _per90(carry_distance, minutes)
    features["progressive_carry_distance_per90"] = _per90(prog_carry_distance, minutes)
    features["carries_into_box_per90"] = _per90(carries_into_box, minutes)
    features["dribbles_attempted_per90"] = _per90(total_dribbles, minutes)
    features["dribble_success_pct"] = _safe_ratio(successful_dribbles, total_dribbles) * 100
    features["ball_receipts_per90"] = _per90(ball_receipts, minutes)

    # ── Dimension 5: Defending & Pressing (8) ───────────────────────

    total_pressures = len(pressures)
    # Successful pressures — counterpress or pressure leading to turnover
    # StatsBomb doesn't have a clean "success" flag; we approximate
    # by checking if counterpress is True
    successful_pressures = 0
    if "counterpress" in pressures.columns:
        successful_pressures = pressures["counterpress"].notna().sum()
    else:
        successful_pressures = int(total_pressures * 0.3)  # rough fallback

    # Tackles
    duels = player_events[player_events["type_name"].isin(["Duel"])]
    if "duel_type_name" in player_events.columns:
        tackles = player_events[
            (player_events["duel_type_name"] == "Tackle")
        ]
    else:
        tackles = pd.DataFrame()

    total_tackles = len(tackles)
    won_tackles = 0
    if total_tackles > 0 and "duel_outcome_name" in tackles.columns:
        won_tackles = len(tackles[tackles["duel_outcome_name"].isin(
            ["Won", "Success", "Success In Play"]
        )])

    # Interceptions, blocks, recoveries, clearances
    interceptions = len(player_events[player_events["type_name"] == "Interception"])
    blocks = len(player_events[player_events["type_name"] == "Block"])
    ball_recoveries = len(player_events[player_events["type_name"] == "Ball Recovery"])
    clearances = len(player_events[player_events["type_name"] == "Clearance"])

    features["pressures_per90"] = _per90(total_pressures, minutes)
    features["pressure_success_pct"] = _safe_ratio(successful_pressures, total_pressures) * 100
    features["tackles_per90"] = _per90(total_tackles, minutes)
    features["tackle_success_pct"] = _safe_ratio(won_tackles, total_tackles) * 100
    features["interceptions_per90"] = _per90(interceptions, minutes)
    features["blocks_per90"] = _per90(blocks, minutes)
    features["ball_recoveries_per90"] = _per90(ball_recoveries, minutes)
    features["clearances_per90"] = _per90(clearances, minutes)

    # ── Dimension 6: Aerial & Physical (6) ──────────────────────────

    # Aerial duels from duel_type_name
    aerial_won = 0
    aerial_lost = 0
    ground_won = 0
    ground_lost = 0

    if "duel_type_name" in player_events.columns and "duel_outcome_name" in player_events.columns:
        duel_events = player_events[player_events["type_name"] == "Duel"]

        # Aerial duels
        aerial_duels_df = duel_events[duel_events["duel_type_name"] == "Aerial Lost"]
        # StatsBomb marks aerial duels as "Aerial Lost" for the loser
        aerial_lost = len(aerial_duels_df)

        # Also check shots/clearances with aerial_won flags
        if "clearance_aerial_won" in player_events.columns:
            aerial_won += player_events["clearance_aerial_won"].notna().sum()
        if "shot_aerial_won" in player_events.columns:
            aerial_won += player_events["shot_aerial_won"].notna().sum()
        if "pass_aerial_won" in player_events.columns:
            aerial_won += player_events["pass_aerial_won"].notna().sum()
        if "miscontrol_aerial_won" in player_events.columns:
            aerial_won += player_events["miscontrol_aerial_won"].notna().sum()

        # Ground duels — non-aerial duels
        non_aerial = duel_events[duel_events["duel_type_name"] != "Aerial Lost"]
        ground_total = len(non_aerial)
        ground_won = len(non_aerial[non_aerial["duel_outcome_name"].isin(
            ["Won", "Success", "Success In Play"]
        )])
        ground_lost = ground_total - ground_won

    total_aerial = aerial_won + aerial_lost
    total_ground = ground_won + ground_lost

    # Fouls won
    fouls_won = len(player_events[player_events["type_name"] == "Foul Won"])

    # Dispossessed
    dispossessed = len(player_events[player_events["type_name"] == "Dispossessed"])

    features["aerial_duels_per90"] = _per90(total_aerial, minutes)
    features["aerial_win_pct"] = _safe_ratio(aerial_won, total_aerial) * 100
    features["ground_duels_per90"] = _per90(total_ground, minutes)
    features["ground_duel_win_pct"] = _safe_ratio(ground_won, total_ground) * 100
    features["fouls_won_per90"] = _per90(fouls_won, minutes)
    features["dispossessed_per90"] = _per90(dispossessed, minutes)

    return features


# ---------------------------------------------------------------------------
# Main pipeline step
# ---------------------------------------------------------------------------

def engineer_features(force: bool = False) -> Path:
    """Compute 42-feature matrix for all qualified players.

    Returns:
        Path to the output feature_matrix.parquet.
    """
    FEATURES_DIR.mkdir(parents=True, exist_ok=True)
    out_path = FEATURES_DIR / "feature_matrix.parquet"

    if out_path.exists() and not force:
        logger.info("Skipping feature engineering — cached at %s", out_path)
        return out_path

    # Load inputs
    events_path = PROCESSED_DIR / "events_normalised.parquet"
    players_path = PROCESSED_DIR / "qualified_players.parquet"

    events = pd.read_parquet(events_path)
    players = pd.read_parquet(players_path)

    logger.info("Loaded %d events and %d qualified players", len(events), len(players))

    # Filter events to only qualified players
    qualified_ids = set(players["player_id"].tolist())
    events = events[events["player_id"].isin(qualified_ids)]
    logger.info("Filtered to %d events for qualified players", len(events))

    # Build minutes lookup
    minutes_lookup: dict[int, int] = dict(
        zip(players["player_id"], players["total_minutes"])
    )

    # Compute features per player
    results: list[dict] = []
    player_groups = events.groupby("player_id")
    total = len(qualified_ids)

    for i, (pid, group) in enumerate(player_groups, 1):
        if i % 100 == 0 or i == 1:
            logger.info("Feature engineering: %d / %d players", i, total)

        pid = int(pid)
        mins = minutes_lookup.get(pid, 0)
        if mins == 0:
            continue

        feats = _compute_player_features(group, mins)
        feats["player_id"] = pid
        results.append(feats)

    feature_df = pd.DataFrame(results)

    # Ensure column ordering matches FEATURE_NAMES
    meta_cols = ["player_id"]
    feature_df = feature_df[meta_cols + FEATURE_NAMES]

    # Merge player metadata
    feature_df = feature_df.merge(
        players[["player_id", "player_name", "team_name", "league",
                 "primary_position", "total_minutes", "matches_played"]],
        on="player_id",
        how="left",
    )

    # Sanity checks
    nan_count = feature_df[FEATURE_NAMES].isna().sum().sum()
    inf_count = np.isinf(feature_df[FEATURE_NAMES].values).sum()

    if nan_count > 0:
        logger.warning("Found %d NaN values — filling with 0.0", nan_count)
        feature_df[FEATURE_NAMES] = feature_df[FEATURE_NAMES].fillna(0.0)

    if inf_count > 0:
        logger.warning("Found %d Inf values — replacing with 0.0", inf_count)
        feature_df[FEATURE_NAMES] = feature_df[FEATURE_NAMES].replace(
            [np.inf, -np.inf], 0.0
        )

    feature_df.to_parquet(out_path, index=False)
    logger.info(
        "Feature matrix saved: %d players × %d features → %s",
        len(feature_df), len(FEATURE_NAMES), out_path,
    )

    return out_path


def run(force: bool = False) -> None:
    """Run feature engineering step."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    )
    logger.info("=== Step 5: Feature engineering ===")
    t0 = time.perf_counter()
    engineer_features(force=force)
    logger.info("Feature engineering complete in %.1fs", time.perf_counter() - t0)


if __name__ == "__main__":
    run(force="--force" in sys.argv)
