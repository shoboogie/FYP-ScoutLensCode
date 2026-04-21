"""CRUD operations for user shortlists."""

from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.shortlist import Shortlist
from app.models.player import PlayerSeason
from app.models.team import Team


async def get_user_shortlist(db: AsyncSession, user_id: int) -> list[Shortlist]:
    stmt = (
        select(Shortlist)
        .where(Shortlist.user_id == user_id)
        .options(
            joinedload(Shortlist.player_season)
            .joinedload(PlayerSeason.player),
            joinedload(Shortlist.player_season)
            .joinedload(PlayerSeason.team),
        )
        .order_by(Shortlist.created_at.desc())
    )
    result = await db.execute(stmt)
    return result.scalars().unique().all()


async def add_to_shortlist(
    db: AsyncSession, user_id: int, player_season_id: int, notes: str = "",
) -> Shortlist:
    entry = Shortlist(
        user_id=user_id,
        player_season_id=player_season_id,
        notes=notes,
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return entry


async def update_shortlist_notes(
    db: AsyncSession, shortlist_id: int, user_id: int, notes: str,
) -> Shortlist | None:
    stmt = select(Shortlist).where(
        Shortlist.id == shortlist_id, Shortlist.user_id == user_id,
    )
    result = await db.execute(stmt)
    entry = result.scalar_one_or_none()
    if entry is None:
        return None
    entry.notes = notes
    await db.commit()
    await db.refresh(entry)
    return entry


async def remove_from_shortlist(
    db: AsyncSession, shortlist_id: int, user_id: int,
) -> bool:
    stmt = delete(Shortlist).where(
        Shortlist.id == shortlist_id, Shortlist.user_id == user_id,
    )
    result = await db.execute(stmt)
    await db.commit()
    return result.rowcount > 0
