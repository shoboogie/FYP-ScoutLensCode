"""Percentile computation within role groups.

Computes where a player ranks relative to peers with the same role
label, returning a value between 0 and 100 for each feature.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from app.utils.constants import FEATURE_NAMES


def compute_percentiles(
    player_features: dict[str, float],
    all_features: pd.DataFrame,
    role_label: str | None = None,
) -> dict[str, float]:
    """Rank each feature as a percentile within the role group.

    If role_label is provided, percentiles are computed against peers
    with the same label. Otherwise, against the full population.
    """
    if role_label and "role_label" in all_features.columns:
        peers = all_features[all_features["role_label"] == role_label]
        if len(peers) < 5:
            peers = all_features  # fall back if too few role peers
    else:
        peers = all_features

    percentiles: dict[str, float] = {}
    for feat in FEATURE_NAMES:
        if feat not in peers.columns:
            percentiles[feat] = 50.0
            continue
        value = player_features.get(feat, 0.0)
        peer_values = peers[feat].dropna().values
        if len(peer_values) == 0:
            percentiles[feat] = 50.0
            continue
        percentiles[feat] = float(stats.percentileofscore(peer_values, value, kind="rank"))

    return percentiles


def percentile_colour(pct: float) -> str:
    """Return a CSS class name for traffic-light percentile colouring."""
    if pct < 25:
        return "percentile-bar-red"
    elif pct < 50:
        return "percentile-bar-orange"
    elif pct < 75:
        return "percentile-bar-green"
    return "percentile-bar-elite"
