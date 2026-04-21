"""Pydantic schemas for the similarity explanation endpoint."""

from __future__ import annotations

from pydantic import BaseModel


class FeatureContribution(BaseModel):
    """Per-feature contribution to overall cosine similarity."""
    feature: str
    dimension: str
    contribution: float
    query_value: float
    target_value: float


class ExplanationResponse(BaseModel):
    """Cosine decomposition explaining why two players are similar."""
    query_player_id: int
    target_player_id: int
    overall_similarity: float
    dimension_similarities: dict[str, float]
    top_contributions: list[FeatureContribution]
