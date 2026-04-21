"""Player search and profile endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.player import (
    DimensionScore,
    FeatureValues,
    PlayerCard,
    PlayerProfile,
    PlayerSearchResponse,
)
from app.services.player_service import (
    compute_dimension_scores,
    get_player_profile,
    get_radar_axes,
    get_role_summary,
    search_players,
)
from app.utils.constants import FEATURE_NAMES

router = APIRouter(tags=["players"])


@router.get("/search", response_model=PlayerSearchResponse)
async def search(
    q: str = Query(..., min_length=1, description="Player name search term"),
    league: str | None = None,
    position: str | None = None,
    age_min: int | None = None,
    age_max: int | None = None,
    min_minutes: int = 900,
    limit: int = Query(default=50, le=200),
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    rows, total = await search_players(
        db, q, league, position, age_min, age_max, min_minutes, limit, offset,
    )

    results = []
    for ps in rows:
        results.append(PlayerCard(
            player_season_id=ps.id,
            player_id=ps.player_id,
            player_name=ps.player.player_name,
            team_name=ps.team.team_name if ps.team else "Unknown",
            league=ps.team.league if ps.team else "Unknown",
            age=ps.age,
            minutes_played=ps.minutes_played,
            matches_played=ps.matches_played,
            primary_position=ps.player.primary_position,
            role_label=ps.role_label,
            role_confidence=ps.role_confidence,
        ))

    return PlayerSearchResponse(results=results, total=total)


@router.get("/player/{player_season_id}", response_model=PlayerProfile)
async def player_profile(
    player_season_id: int,
    db: AsyncSession = Depends(get_db),
):
    ps = await get_player_profile(db, player_season_id)
    if not ps:
        raise HTTPException(status_code=404, detail="Player season not found")

    feat = ps.features
    if not feat:
        raise HTTPException(status_code=404, detail="Features not available for this player")

    feature_dict = {fn: getattr(feat, fn, 0.0) for fn in FEATURE_NAMES}
    dim_scores = compute_dimension_scores(feat, ps.role_label)

    return PlayerProfile(
        player_season_id=ps.id,
        player_id=ps.player_id,
        player_name=ps.player.player_name,
        team_name=ps.team.team_name if ps.team else "Unknown",
        league=ps.team.league if ps.team else "Unknown",
        season=ps.season,
        age=ps.age,
        minutes_played=ps.minutes_played,
        matches_played=ps.matches_played,
        primary_position=ps.player.primary_position,
        role_label=ps.role_label,
        role_confidence=ps.role_confidence,
        role_summary=get_role_summary(ps.role_label),
        features=FeatureValues(**feature_dict),
        dimension_scores=[DimensionScore(**d) for d in dim_scores],
        radar_axes=get_radar_axes(ps.role_label),
    )
