"""Pydantic schemas for shortlist management endpoints."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class ShortlistCreate(BaseModel):
    player_season_id: int
    notes: str = ""


class ShortlistUpdate(BaseModel):
    notes: str


class ShortlistEntry(BaseModel):
    id: int
    player_season_id: int
    player_name: str
    team_name: str
    league: str
    role_label: str | None
    notes: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ShortlistResponse(BaseModel):
    entries: list[ShortlistEntry]
    total: int
