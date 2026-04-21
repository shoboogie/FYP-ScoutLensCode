"""Similarity search and explanation endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.explain import ExplanationResponse, FeatureContribution
from app.schemas.similarity import (
    SimilarityRequest,
    SimilarityResponse,
    SimilarPlayerResult,
)
from app.services.similarity_service import search_similar
from app.services.explain_service import explain_similarity

router = APIRouter(tags=["similarity"])


def _build_metadata_cache(db_results) -> dict[int, dict]:
    """Build an in-memory lookup for post-filtering in the FAISS layer.

    In a production system this would be pre-cached. For the dissertation
    scope we load from the feature matrix parquet on startup.
    """
    # Loaded at app startup and cached — see main.py
    from app.services.similarity_service import _player_ids
    return {}


@router.post("/similar/{player_season_id}", response_model=SimilarityResponse)
async def find_similar(
    player_season_id: int,
    body: SimilarityRequest,
    db: AsyncSession = Depends(get_db),
):
    # Look up the player_id from player_season_id
    from app.models.player import PlayerSeason
    from sqlalchemy import select
    from sqlalchemy.orm import joinedload

    stmt = (
        select(PlayerSeason)
        .where(PlayerSeason.id == player_season_id)
        .options(joinedload(PlayerSeason.player), joinedload(PlayerSeason.team))
    )
    result = await db.execute(stmt)
    ps = result.scalar_one_or_none()
    if not ps:
        raise HTTPException(status_code=404, detail="Player season not found")

    # Load metadata cache for post-filtering
    from app.main import player_metadata_cache

    matches = search_similar(
        player_id=ps.player_id,
        k=body.k,
        role_filter=body.role_filter,
        feature_weights=body.feature_weights,
        player_metadata=player_metadata_cache,
        league_filter=body.league_filter,
        age_min=body.age_min,
        age_max=body.age_max,
        min_minutes=body.min_minutes,
    )

    results = [
        SimilarPlayerResult(
            player_season_id=m.get("player_season_id", 0),
            player_id=m["player_id"],
            player_name=m.get("player_name", ""),
            team_name=m.get("team_name", ""),
            league=m.get("league", ""),
            age=m.get("age", 0),
            minutes_played=m.get("minutes_played", 0),
            role_label=m.get("role_label"),
            similarity_score=m["similarity_score"],
        )
        for m in matches
    ]

    return SimilarityResponse(
        query_player_id=ps.player_id,
        query_player_name=ps.player.player_name,
        query_role=ps.role_label,
        results=results,
        total=len(results),
    )


@router.get("/explain/{player_season_id}")
async def explain(
    player_season_id: int,
    target_id: int = Query(..., description="Target player_season_id to compare against"),
    db: AsyncSession = Depends(get_db),
):
    """Per-feature cosine decomposition between two players."""
    from app.models.player import PlayerVector
    from sqlalchemy import select
    import numpy as np

    # Load both vectors
    stmt_q = select(PlayerVector).where(PlayerVector.player_season_id == player_season_id)
    stmt_t = select(PlayerVector).where(PlayerVector.player_season_id == target_id)

    q_result = await db.execute(stmt_q)
    t_result = await db.execute(stmt_t)

    q_vec = q_result.scalar_one_or_none()
    t_vec = t_result.scalar_one_or_none()

    if not q_vec or not t_vec:
        raise HTTPException(status_code=404, detail="Vector not found for one or both players")

    explanation = explain_similarity(
        np.array(q_vec.vector, dtype=np.float64),
        np.array(t_vec.vector, dtype=np.float64),
    )

    return ExplanationResponse(
        query_player_id=player_season_id,
        target_player_id=target_id,
        overall_similarity=explanation["overall_similarity"],
        dimension_similarities=explanation["dimension_similarities"],
        top_contributions=[
            FeatureContribution(**c) for c in explanation["top_contributions"]
        ],
    )
