"""Player search and profile endpoints.

Reads from the in-memory metadata cache loaded at startup from the
feature matrix parquet. No database dependency for core functionality.
"""

from fastapi import APIRouter, HTTPException, Query

from app.schemas.player import (
    DimensionScore,
    FeatureValues,
    PlayerCard,
    PlayerProfile,
    PlayerSearchResponse,
)
from app.services.player_service import (
    get_radar_axes,
    get_role_summary,
)
from app.utils.constants import DIMENSION_GROUPS, FEATURE_NAMES

router = APIRouter(tags=["players"])


def _get_cache() -> dict[int, dict]:
    from app.main import player_metadata_cache
    return player_metadata_cache


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
):
    cache = _get_cache()
    q_lower = q.lower()

    matches = []
    for meta in cache.values():
        if q_lower not in meta["player_name"].lower():
            continue
        if league and meta.get("league") != league:
            continue
        if position and meta.get("primary_position") != position:
            continue
        if age_min and meta.get("age", 0) < age_min:
            continue
        if age_max and meta.get("age", 99) > age_max:
            continue
        if meta.get("minutes_played", 0) < min_minutes:
            continue
        matches.append(meta)

    # Sort by name
    matches.sort(key=lambda m: m["player_name"])
    total = len(matches)
    page = matches[offset:offset + limit]

    results = [
        PlayerCard(
            player_season_id=m["player_season_id"],
            player_id=m["player_id"],
            player_name=m["player_name"],
            team_name=m.get("team_name", ""),
            league=m.get("league", ""),
            age=m.get("age", 25),
            minutes_played=m.get("minutes_played", 0),
            matches_played=m.get("matches_played", 0),
            primary_position=m.get("primary_position"),
            role_label=m.get("role_label"),
            role_confidence=m.get("role_confidence"),
        )
        for m in page
    ]

    return PlayerSearchResponse(results=results, total=total)


@router.get("/player/{player_season_id}", response_model=PlayerProfile)
async def player_profile(player_season_id: int):
    cache = _get_cache()

    # Find the player by player_season_id
    meta = None
    for m in cache.values():
        if m["player_season_id"] == player_season_id:
            meta = m
            break

    if not meta:
        raise HTTPException(status_code=404, detail="Player season not found")

    feature_dict = {fn: meta.get(fn, 0.0) for fn in FEATURE_NAMES}
    role = meta.get("role_label")

    # Dimension scores — average of raw values per dimension
    dim_scores = []
    for dim_name, indices in DIMENSION_GROUPS.items():
        feat_names = [FEATURE_NAMES[i] for i in indices]
        values = [meta.get(fn, 0.0) for fn in feat_names]
        avg = sum(values) / len(values) if values else 0.0
        dim_scores.append({"dimension": dim_name, "percentile": round(avg, 4)})

    return PlayerProfile(
        player_season_id=meta["player_season_id"],
        player_id=meta["player_id"],
        player_name=meta["player_name"],
        team_name=meta.get("team_name", ""),
        league=meta.get("league", ""),
        season=meta.get("season", "2015/2016"),
        age=meta.get("age", 25),
        minutes_played=meta.get("minutes_played", 0),
        matches_played=meta.get("matches_played", 0),
        primary_position=meta.get("primary_position"),
        role_label=role,
        role_confidence=meta.get("role_confidence"),
        role_summary=get_role_summary(role),
        features=FeatureValues(**feature_dict),
        dimension_scores=[DimensionScore(**d) for d in dim_scores],
        radar_axes=get_radar_axes(role),
    )
