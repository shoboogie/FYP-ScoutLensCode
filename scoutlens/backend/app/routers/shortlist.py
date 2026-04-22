"""Shortlist CRUD endpoints — requires JWT authentication.

Uses in-memory storage so shortlists work without PostgreSQL.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.schemas.shortlist import (
    ShortlistCreate,
    ShortlistEntry,
    ShortlistResponse,
    ShortlistUpdate,
)
from app.services.auth_service import decode_token

router = APIRouter(prefix="/shortlist", tags=["shortlist"])
security = HTTPBearer()

# In-memory shortlist store: {user_id: [entry_dict, ...]}
_shortlists: dict[int, list[dict]] = {}
_next_id = 1


def _get_user_id(credentials: HTTPAuthorizationCredentials) -> int:
    payload = decode_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return int(payload["sub"])


def _get_cache() -> dict[int, dict]:
    from app.main import player_metadata_cache
    return player_metadata_cache


def _find_player_by_season_id(ps_id: int) -> dict | None:
    cache = _get_cache()
    for m in cache.values():
        if m["player_season_id"] == ps_id:
            return m
    return None


def _to_entry(e: dict) -> ShortlistEntry:
    return ShortlistEntry(
        id=e["id"],
        player_season_id=e["player_season_id"],
        player_name=e["player_name"],
        team_name=e["team_name"],
        league=e["league"],
        role_label=e.get("role_label"),
        notes=e["notes"],
        created_at=e["created_at"],
    )


@router.get("", response_model=ShortlistResponse)
async def list_shortlist(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    user_id = _get_user_id(credentials)
    entries = _shortlists.get(user_id, [])
    return ShortlistResponse(
        entries=[_to_entry(e) for e in entries],
        total=len(entries),
    )


@router.post("", response_model=ShortlistEntry, status_code=status.HTTP_201_CREATED)
async def add_shortlist(
    body: ShortlistCreate,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    global _next_id
    user_id = _get_user_id(credentials)

    # Check for duplicates
    user_entries = _shortlists.get(user_id, [])
    for e in user_entries:
        if e["player_season_id"] == body.player_season_id:
            raise HTTPException(status_code=409, detail="Already on shortlist")

    # Look up player metadata
    player = _find_player_by_season_id(body.player_season_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    entry = {
        "id": _next_id,
        "player_season_id": body.player_season_id,
        "player_name": player.get("player_name", ""),
        "team_name": player.get("team_name", ""),
        "league": player.get("league", ""),
        "role_label": player.get("role_label"),
        "notes": body.notes,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    _next_id += 1

    if user_id not in _shortlists:
        _shortlists[user_id] = []
    _shortlists[user_id].append(entry)

    return _to_entry(entry)


@router.patch("/{shortlist_id}", response_model=ShortlistEntry)
async def update_shortlist(
    shortlist_id: int,
    body: ShortlistUpdate,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    user_id = _get_user_id(credentials)
    for e in _shortlists.get(user_id, []):
        if e["id"] == shortlist_id:
            e["notes"] = body.notes
            return _to_entry(e)

    raise HTTPException(status_code=404, detail="Shortlist entry not found")


@router.delete("/{shortlist_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_shortlist(
    shortlist_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    user_id = _get_user_id(credentials)
    entries = _shortlists.get(user_id, [])
    for i, e in enumerate(entries):
        if e["id"] == shortlist_id:
            entries.pop(i)
            return

    raise HTTPException(status_code=404, detail="Shortlist entry not found")
