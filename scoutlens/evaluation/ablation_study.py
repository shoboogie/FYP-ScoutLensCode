"""Ablation study — measure RC@10 impact of removing each dimension.

For each of the 6 feature dimensions, zero out those features in the
query vector and re-run the similarity search. Comparing RC@10 with
and without each dimension reveals which dimensions are most critical
for role-consistent retrieval.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_PROJECT_ROOT = Path(__file__).resolve().parents[0].parent / "backend"
sys.path.insert(0, str(_PROJECT_ROOT))

from app.utils.constants import DIMENSION_GROUPS, FEATURE_NAMES
from app.services.similarity_service import load_index, search_similar

logger = logging.getLogger(__name__)

FEATURES_DIR = Path(__file__).resolve().parents[0].parent / "data" / "features"


def _build_metadata() -> dict[int, dict]:
    df = pd.read_parquet(FEATURES_DIR / "feature_matrix.parquet")
    meta = {}
    for i, (_, row) in enumerate(df.iterrows(), start=1):
        pid = int(row["player_id"])
        meta[pid] = {
            "player_id": pid,
            "player_season_id": i,
            "player_name": row.get("player_name", ""),
            "team_name": row.get("team_name", ""),
            "league": row.get("league", ""),
            "role_label": row.get("role_label"),
            "minutes_played": int(row.get("total_minutes", 0)),
            "age": int(row.get("age", 25)),
        }
    return meta


def run_ablation(n_queries: int = 100, k: int = 10, seed: int = 42) -> dict[str, float]:
    """Run ablation: compute RC@k with each dimension zeroed out.

    Returns {dimension_name: RC@k_drop} where drop = baseline - ablated.
    """
    load_index()
    metadata = _build_metadata()
    player_ids = list(metadata.keys())

    rng = np.random.default_rng(seed)
    query_ids = rng.choice(player_ids, size=min(n_queries, len(player_ids)), replace=False)

    # Baseline RC@k (no ablation)
    baseline_scores: list[float] = []
    for qid in query_ids:
        query_role = metadata[qid].get("role_label")
        if not query_role:
            continue
        matches = search_similar(qid, k=k, role_filter=False, player_metadata=metadata)
        if matches:
            same = sum(1 for m in matches if m.get("role_label") == query_role)
            baseline_scores.append(same / len(matches))

    baseline = float(np.mean(baseline_scores)) if baseline_scores else 0.0
    logger.info("Baseline RC@%d = %.4f", k, baseline)

    # Ablate each dimension by setting its weight to 0
    drops: dict[str, float] = {}
    for dim_name in DIMENSION_GROUPS:
        # Build weights that zero out this dimension
        weights = {}
        from app.utils.constants import DIMENSION_KEY_MAP
        inv_map = {v: k for k, v in DIMENSION_KEY_MAP.items()}
        for d in DIMENSION_GROUPS:
            short = inv_map.get(d, d[:3].upper())
            weights[short] = 0.0 if d == dim_name else 1.0

        ablated_scores: list[float] = []
        for qid in query_ids:
            query_role = metadata[qid].get("role_label")
            if not query_role:
                continue
            matches = search_similar(
                qid, k=k, role_filter=False,
                feature_weights=weights, player_metadata=metadata,
            )
            if matches:
                same = sum(1 for m in matches if m.get("role_label") == query_role)
                ablated_scores.append(same / len(matches))

        ablated = float(np.mean(ablated_scores)) if ablated_scores else 0.0
        drop = baseline - ablated
        drops[dim_name] = round(drop, 4)
        logger.info("  Without %-18s: RC@%d = %.4f (drop = %+.4f)", dim_name, k, ablated, drop)

    return drops


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    print("\n=== Ablation Study: RC@10 impact per dimension ===")
    drops = run_ablation()
    print("\nSummary (positive = dimension helps role consistency):")
    for dim, drop in sorted(drops.items(), key=lambda x: x[1], reverse=True):
        print(f"  {dim:20s}  {drop:+.4f}")
