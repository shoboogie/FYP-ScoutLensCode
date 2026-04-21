"""Similarity search and explanation endpoints.

Uses the in-memory FAISS index and metadata cache — no database needed.
"""

from fastapi import APIRouter, HTTPException, Query
import numpy as np

from app.schemas.explain import ExplanationResponse, FeatureContribution
from app.schemas.similarity import (
    SimilarityRequest,
    SimilarityResponse,
    SimilarPlayerResult,
)
from app.services.similarity_service import search_similar
from app.services.explain_service import explain_similarity

router = APIRouter(tags=["similarity"])


def _get_cache() -> dict[int, dict]:
    from app.main import player_metadata_cache
    return player_metadata_cache


def _find_by_season_id(cache: dict[int, dict], ps_id: int) -> dict | None:
    for m in cache.values():
        if m["player_season_id"] == ps_id:
            return m
    return None


@router.post("/similar/{player_season_id}", response_model=SimilarityResponse)
async def find_similar(player_season_id: int, body: SimilarityRequest):
    cache = _get_cache()
    meta = _find_by_season_id(cache, player_season_id)
    if not meta:
        raise HTTPException(status_code=404, detail="Player season not found")

    matches = search_similar(
        player_id=meta["player_id"],
        k=body.k,
        role_filter=body.role_filter,
        feature_weights=body.feature_weights,
        player_metadata=cache,
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
            age=m.get("age", 25),
            minutes_played=m.get("minutes_played", 0),
            role_label=m.get("role_label"),
            similarity_score=m["similarity_score"],
        )
        for m in matches
    ]

    return SimilarityResponse(
        query_player_id=meta["player_id"],
        query_player_name=meta["player_name"],
        query_role=meta.get("role_label"),
        results=results,
        total=len(results),
    )


@router.get("/explain/{player_season_id}")
async def explain(
    player_season_id: int,
    target_id: int = Query(..., description="Target player_season_id to compare against"),
):
    """Per-feature cosine decomposition between two players."""
    from app.services.similarity_service import _index, _player_ids

    if _index is None or _player_ids is None:
        raise HTTPException(status_code=503, detail="Index not loaded")

    cache = _get_cache()
    query_meta = _find_by_season_id(cache, player_season_id)
    target_meta = _find_by_season_id(cache, target_id)

    if not query_meta or not target_meta:
        raise HTTPException(status_code=404, detail="Player not found")

    # Reconstruct vectors from FAISS index
    q_idx = int(np.where(_player_ids == query_meta["player_id"])[0][0])
    t_idx = int(np.where(_player_ids == target_meta["player_id"])[0][0])

    q_vec = np.zeros(_index.d, dtype=np.float32)
    t_vec = np.zeros(_index.d, dtype=np.float32)
    _index.reconstruct(q_idx, q_vec)
    _index.reconstruct(t_idx, t_vec)

    explanation = explain_similarity(
        q_vec.astype(np.float64),
        t_vec.astype(np.float64),
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
