"""Shared test fixtures for the ScoutLens backend test suite."""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure the backend directory is on sys.path so imports work
_BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))
