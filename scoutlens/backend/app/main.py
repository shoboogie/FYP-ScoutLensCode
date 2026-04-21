"""FastAPI application factory and startup configuration."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

import pandas as pd
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import auth, players, shortlist, similarity
from app.services.similarity_service import load_index
from app.utils.constants import FEATURE_NAMES

logger = logging.getLogger(__name__)

# In-memory metadata cache for FAISS post-filtering.
# Keyed by player_id → {player_name, team_name, league, age, ...}
player_metadata_cache: dict[int, dict] = {}


def _load_metadata_cache() -> None:
    """Populate the metadata cache from the feature matrix parquet."""
    # Resolve relative to project root (one level above backend/)
    project_root = Path(__file__).resolve().parents[2]
    feature_path = project_root / "data" / "features" / "feature_matrix.parquet"
    if not feature_path.exists():
        logger.warning("Feature matrix not found — metadata cache empty")
        return

    df = pd.read_parquet(feature_path)

    for i, (_, row) in enumerate(df.iterrows(), start=1):
        pid = int(row["player_id"])
        player_metadata_cache[pid] = {
            "player_id": pid,
            "player_season_id": i,  # sequential until DB seeding assigns real IDs
            "player_name": row.get("player_name", ""),
            "team_name": row.get("team_name", ""),
            "league": row.get("league", ""),
            "primary_position": row.get("primary_position"),
            "role_label": row.get("role_label"),
            "role_confidence": row.get("role_confidence"),
            "minutes_played": int(row.get("total_minutes", 0)),
            "matches_played": int(row.get("matches_played", 0)),
            "age": int(row.get("age", 0)) if pd.notna(row.get("age")) else 0,
        }

    logger.info("Metadata cache loaded: %d players", len(player_metadata_cache))


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: load FAISS index and metadata. Shutdown: cleanup."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    )
    load_index()
    _load_metadata_cache()
    yield


app = FastAPI(
    title="ScoutLens API",
    description=(
        "Role-aware player similarity search engine for football scouting. "
        "Powered by StatsBomb Open Data (2015/16), FAISS vector search, "
        "and hierarchical role clustering."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers under /api/v1
app.include_router(auth.router, prefix="/api/v1")
app.include_router(players.router, prefix="/api/v1")
app.include_router(similarity.router, prefix="/api/v1")
app.include_router(shortlist.router, prefix="/api/v1")


@app.get("/api/v1/health")
async def health():
    from app.services.similarity_service import _index
    return {
        "status": "ok",
        "players_cached": len(player_metadata_cache),
        "index_loaded": _index is not None,
    }
