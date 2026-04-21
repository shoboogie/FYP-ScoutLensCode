"""Pydantic schemas for the similarity search endpoint."""

from __future__ import annotations

from pydantic import BaseModel, Field


class SimilarityRequest(BaseModel):
    """POST body for /similar/{player_season_id}."""
    k: int = Field(default=10, ge=1, le=50)
    league_filter: str | None = None
    age_min: int | None = None
    age_max: int | None = None
    min_minutes: int = 900
    role_filter: bool = True
    feature_weights: dict[str, float] | None = None


class SimilarPlayerResult(BaseModel):
    """A single match in the similarity results list."""
    player_season_id: int
    player_id: int
    player_name: str
    team_name: str
    league: str
    age: int
    minutes_played: int
    role_label: str | None
    similarity_score: float
    dimension_scores: dict[str, float] | None = None


class SimilarityResponse(BaseModel):
    query_player_id: int
    query_player_name: str
    query_role: str | None
    results: list[SimilarPlayerResult]
    total: int
