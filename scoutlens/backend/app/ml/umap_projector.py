"""UMAP 2D projection for the style map visualisation.

Projects the 42-d feature space into 2D for scatter plot display,
preserving local neighbourhood structure so similar players cluster
visually.
"""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from umap import UMAP

from app.utils.constants import FEATURE_NAMES

logger = logging.getLogger(__name__)


def compute_umap_projection(
    feature_matrix: pd.DataFrame,
    n_neighbours: int = 15,
    min_dist: float = 0.1,
    random_state: int = 42,
) -> np.ndarray:
    """Project the feature matrix to 2D via UMAP.

    Returns an (n_players, 2) array of [x, y] coordinates.
    """
    X = feature_matrix[FEATURE_NAMES].values.astype(np.float64)
    X_scaled = StandardScaler().fit_transform(X)

    reducer = UMAP(
        n_components=2,
        n_neighbors=n_neighbours,
        min_dist=min_dist,
        random_state=random_state,
        metric="cosine",
    )
    coords = reducer.fit_transform(X_scaled)
    logger.info("UMAP projection complete: %d points", len(coords))
    return coords.astype(np.float64)
