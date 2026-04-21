"""Pydantic schemas for player endpoints."""

from __future__ import annotations

from pydantic import BaseModel


class PlayerCard(BaseModel):
    """Compact player summary for search results and lists."""
    player_season_id: int
    player_id: int
    player_name: str
    team_name: str
    league: str
    age: int
    minutes_played: int
    matches_played: int
    primary_position: str | None
    role_label: str | None
    role_confidence: float | None


class PlayerSearchResponse(BaseModel):
    results: list[PlayerCard]
    total: int


class FeatureValues(BaseModel):
    """All 42 per-90 features for a single player-season."""
    xg_per90: float
    shots_per90: float
    shots_on_target_per90: float
    goals_per90: float
    npxg_per90: float
    touches_in_box_per90: float
    xg_per_shot: float
    xa_per90: float
    key_passes_per90: float
    assists_per90: float
    passes_into_box_per90: float
    through_balls_per90: float
    progressive_passes_per90: float
    crosses_per90: float
    passes_attempted_per90: float
    pass_completion_pct: float
    progressive_pass_distance_per90: float
    long_passes_per90: float
    long_pass_completion_pct: float
    switches_per90: float
    passes_under_pressure_pct: float
    progressive_carries_per90: float
    carry_distance_per90: float
    progressive_carry_distance_per90: float
    carries_into_box_per90: float
    dribbles_attempted_per90: float
    dribble_success_pct: float
    ball_receipts_per90: float
    pressures_per90: float
    pressure_success_pct: float
    tackles_per90: float
    tackle_success_pct: float
    interceptions_per90: float
    blocks_per90: float
    ball_recoveries_per90: float
    clearances_per90: float
    aerial_duels_per90: float
    aerial_win_pct: float
    ground_duels_per90: float
    ground_duel_win_pct: float
    fouls_won_per90: float
    dispossessed_per90: float


class DimensionScore(BaseModel):
    """Aggregated percentile for a single dimension (e.g. Attacking)."""
    dimension: str
    percentile: float


class PlayerProfile(BaseModel):
    """Full player profile with stats, percentiles, and dimension scores."""
    player_season_id: int
    player_id: int
    player_name: str
    team_name: str
    league: str
    season: str
    age: int
    minutes_played: int
    matches_played: int
    primary_position: str | None
    role_label: str | None
    role_confidence: float | None
    role_summary: str | None
    features: FeatureValues
    dimension_scores: list[DimensionScore]
    radar_axes: list[str] | None
