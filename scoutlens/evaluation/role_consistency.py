"""RC@k — Role Consistency at k.

Measures what percentage of top-k similar players share the query
player's role label. Run across 100 random queries for k=5 and k=10.

Target from spec: RC@10 >= 0.75 with role filtering enabled.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_PROJECT_ROOT = Path(__file__).resolve().parents[0].parent / "backend"
sys.path.insert(0, str(_PROJECT_ROOT))

from app.utils.constants import FEATURE_NAMES
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


def evaluate_rc_at_k(
    n_queries: int = 100,
    k_values: list[int] | None = None,
    role_filter: bool = True,
    seed: int = 42,
) -> dict[int, float]:
    """Compute RC@k across random queries.

    Returns {k: mean_rc_score} for each k in k_values.
    """
    if k_values is None:
        k_values = [5, 10]

    load_index()
    metadata = _build_metadata()
    player_ids = list(metadata.keys())

    rng = np.random.default_rng(seed)
    query_ids = rng.choice(player_ids, size=min(n_queries, len(player_ids)), replace=False)

    results: dict[int, list[float]] = {k: [] for k in k_values}

    for qid in query_ids:
        query_role = metadata[qid].get("role_label")
        if not query_role:
            continue

        for k in k_values:
            matches = search_similar(
                player_id=qid,
                k=k,
                role_filter=role_filter,
                player_metadata=metadata,
            )
            if not matches:
                continue

            same_role = sum(1 for m in matches if m.get("role_label") == query_role)
            rc = same_role / len(matches)
            results[k].append(rc)

    scores = {}
    for k in k_values:
        scores[k] = float(np.mean(results[k])) if results[k] else 0.0
        logger.info("RC@%d = %.4f (n=%d queries)", k, scores[k], len(results[k]))

    return scores


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    print("\n=== Role Consistency (role_filter=True) ===")
    rc_filtered = evaluate_rc_at_k(role_filter=True)
    for k, score in rc_filtered.items():
        print(f"  RC@{k} = {score:.4f}")

    print("\n=== Role Consistency (role_filter=False) ===")
    rc_unfiltered = evaluate_rc_at_k(role_filter=False)
    for k, score in rc_unfiltered.items():
        print(f"  RC@{k} = {score:.4f}")
