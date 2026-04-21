"""Player search and profile retrieval from the database."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.player import Player, PlayerFeature, PlayerSeason
from app.models.team import Team
from app.utils.constants import (
    DIMENSION_GROUPS,
    FEATURE_NAMES,
    ROLE_RADAR_AXES,
    ROLE_SUMMARY_TEMPLATES,
)


async def search_players(
    db: AsyncSession,
    q: str,
    league: str | None = None,
    position: str | None = None,
    age_min: int | None = None,
    age_max: int | None = None,
    min_minutes: int = 900,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[PlayerSeason], int]:
    """Search player-seasons by name with optional filters.

    Returns (matching rows, total count).
    """
    stmt = (
        select(PlayerSeason)
        .join(Player)
        .join(Team)
        .where(Player.player_name.ilike(f"%{q}%"))
        .where(PlayerSeason.minutes_played >= min_minutes)
    )

    if league:
        stmt = stmt.where(Team.league == league)
    if position:
        stmt = stmt.where(Player.primary_position == position)
    if age_min is not None:
        stmt = stmt.where(PlayerSeason.age >= age_min)
    if age_max is not None:
        stmt = stmt.where(PlayerSeason.age <= age_max)

    # Total count before pagination
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    stmt = stmt.order_by(Player.player_name).offset(offset).limit(limit)
    stmt = stmt.options(joinedload(PlayerSeason.player), joinedload(PlayerSeason.team))

    result = await db.execute(stmt)
    return result.scalars().unique().all(), total


async def get_player_profile(
    db: AsyncSession, player_season_id: int,
) -> PlayerSeason | None:
    """Load a full player-season with features, team, and player info."""
    stmt = (
        select(PlayerSeason)
        .where(PlayerSeason.id == player_season_id)
        .options(
            joinedload(PlayerSeason.player),
            joinedload(PlayerSeason.team),
            joinedload(PlayerSeason.features),
        )
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


def compute_dimension_scores(
    features: PlayerFeature,
    role_label: str | None,
) -> list[dict[str, float]]:
    """Compute average percentile per dimension from feature values.

    For now, returns raw averages within each dimension group.
    Percentile computation against role peers requires the full dataset.
    """
    scores = []
    for dim_name, indices in DIMENSION_GROUPS.items():
        feat_names = [FEATURE_NAMES[i] for i in indices]
        values = [getattr(features, fn, 0.0) or 0.0 for fn in feat_names]
        avg = sum(values) / len(values) if values else 0.0
        scores.append({"dimension": dim_name, "percentile": round(avg, 4)})
    return scores


def get_role_summary(role_label: str | None) -> str | None:
    if not role_label:
        return None
    return ROLE_SUMMARY_TEMPLATES.get(role_label)


def get_radar_axes(role_label: str | None) -> list[str] | None:
    if not role_label:
        return None
    return ROLE_RADAR_AXES.get(role_label)
