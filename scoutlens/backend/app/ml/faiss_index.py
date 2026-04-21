"""FAISS index query interface for the API layer.

Wraps the similarity_service singleton with a cleaner interface
for use in route handlers.
"""

from __future__ import annotations

from app.services.similarity_service import (
    _get_player_index,
    _index,
    _player_ids,
    load_index,
    search_similar,
)


def is_loaded() -> bool:
    """Check whether the FAISS index is ready for queries."""
    return _index is not None and _player_ids is not None


def total_vectors() -> int:
    """Number of vectors in the loaded index."""
    return _index.ntotal if _index else 0


def player_exists(player_id: int) -> bool:
    """Check whether a player_id exists in the index."""
    return _get_player_index(player_id) is not None
