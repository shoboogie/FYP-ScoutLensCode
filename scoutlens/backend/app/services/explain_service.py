"""Cosine decomposition for explaining similarity between two players.

Each feature's contribution = query_norm[i] * target_norm[i].
The sum across all features equals the total cosine similarity.
Sorted by |contribution| descending to highlight the most important features.
"""

from __future__ import annotations

import numpy as np

from app.utils.constants import DIMENSION_GROUPS, FEATURE_NAMES


def _feature_to_dimension(feature: str) -> str:
    """Map a feature name to its parent dimension."""
    for dim_name, indices in DIMENSION_GROUPS.items():
        dim_features = [FEATURE_NAMES[i] for i in indices]
        if feature in dim_features:
            return dim_name
    return "Unknown"


def explain_similarity(
    query_vector: np.ndarray,
    target_vector: np.ndarray,
) -> dict:
    """Decompose cosine similarity into per-feature contributions.

    Both vectors must already be L2-normalised (unit length).

    Returns dict with overall_similarity, dimension_similarities,
    and top_contributions sorted by absolute contribution.
    """
    contributions = query_vector * target_vector
    overall = float(contributions.sum())

    # Per-dimension aggregation
    dim_sims: dict[str, float] = {}
    for dim_name, indices in DIMENSION_GROUPS.items():
        dim_sims[dim_name] = round(float(contributions[indices].sum()), 4)

    # Per-feature breakdown, sorted by impact
    feature_contribs = []
    for i, feat_name in enumerate(FEATURE_NAMES):
        feature_contribs.append({
            "feature": feat_name,
            "dimension": _feature_to_dimension(feat_name),
            "contribution": round(float(contributions[i]), 6),
            "query_value": round(float(query_vector[i]), 6),
            "target_value": round(float(target_vector[i]), 6),
        })

    feature_contribs.sort(key=lambda x: abs(x["contribution"]), reverse=True)

    return {
        "overall_similarity": round(overall, 4),
        "dimension_similarities": dim_sims,
        "top_contributions": feature_contribs[:20],  # top 20 by impact
    }
