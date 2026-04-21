"""Shortlist CRUD endpoints — requires JWT authentication."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.shortlist import (
    ShortlistCreate,
    ShortlistEntry,
    ShortlistResponse,
    ShortlistUpdate,
)
from app.services.auth_service import decode_token
from app.services.shortlist_service import (
    add_to_shortlist,
    get_user_shortlist,
    remove_from_shortlist,
    update_shortlist_notes,
)

router = APIRouter(prefix="/shortlist", tags=["shortlist"])
security = HTTPBearer()


def _get_user_id(credentials: HTTPAuthorizationCredentials) -> int:
    """Extract user_id from JWT, raising 401 on failure."""
    payload = decode_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return int(payload["sub"])


@router.get("", response_model=ShortlistResponse)
async def list_shortlist(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
):
    user_id = _get_user_id(credentials)
    entries = await get_user_shortlist(db, user_id)

    items = []
    for e in entries:
        ps = e.player_season
        items.append(ShortlistEntry(
            id=e.id,
            player_season_id=e.player_season_id,
            player_name=ps.player.player_name if ps and ps.player else "",
            team_name=ps.team.team_name if ps and ps.team else "",
            league=ps.team.league if ps and ps.team else "",
            role_label=ps.role_label if ps else None,
            notes=e.notes,
            created_at=e.created_at,
        ))

    return ShortlistResponse(entries=items, total=len(items))


@router.post("", response_model=ShortlistEntry, status_code=status.HTTP_201_CREATED)
async def add_shortlist(
    body: ShortlistCreate,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
):
    user_id = _get_user_id(credentials)
    try:
        entry = await add_to_shortlist(db, user_id, body.player_season_id, body.notes)
    except Exception:
        raise HTTPException(status_code=409, detail="Already on shortlist")

    # Reload with relationships
    entries = await get_user_shortlist(db, user_id)
    for e in entries:
        if e.id == entry.id:
            ps = e.player_season
            return ShortlistEntry(
                id=e.id,
                player_season_id=e.player_season_id,
                player_name=ps.player.player_name if ps and ps.player else "",
                team_name=ps.team.team_name if ps and ps.team else "",
                league=ps.team.league if ps and ps.team else "",
                role_label=ps.role_label if ps else None,
                notes=e.notes,
                created_at=e.created_at,
            )

    raise HTTPException(status_code=500, detail="Failed to create shortlist entry")


@router.patch("/{shortlist_id}", response_model=ShortlistEntry)
async def update_shortlist(
    shortlist_id: int,
    body: ShortlistUpdate,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
):
    user_id = _get_user_id(credentials)
    entry = await update_shortlist_notes(db, shortlist_id, user_id, body.notes)
    if not entry:
        raise HTTPException(status_code=404, detail="Shortlist entry not found")

    # Reload for response
    entries = await get_user_shortlist(db, user_id)
    for e in entries:
        if e.id == entry.id:
            ps = e.player_season
            return ShortlistEntry(
                id=e.id,
                player_season_id=e.player_season_id,
                player_name=ps.player.player_name if ps and ps.player else "",
                team_name=ps.team.team_name if ps and ps.team else "",
                league=ps.team.league if ps and ps.team else "",
                role_label=ps.role_label if ps else None,
                notes=e.notes,
                created_at=e.created_at,
            )


@router.delete("/{shortlist_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_shortlist(
    shortlist_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
):
    user_id = _get_user_id(credentials)
    removed = await remove_from_shortlist(db, shortlist_id, user_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Shortlist entry not found")
