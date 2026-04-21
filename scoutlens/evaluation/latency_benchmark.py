"""Query latency benchmark — FAISS vs brute-force numpy.

Runs 500 random similarity queries and reports p50, p95, p99 latencies.
Target from spec: p95 < 100ms.
"""

from __future__ import annotations

import logging
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

_PROJECT_ROOT = Path(__file__).resolve().parents[0].parent / "backend"
sys.path.insert(0, str(_PROJECT_ROOT))

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


def benchmark(n_queries: int = 500, k: int = 10, seed: int = 42) -> dict[str, float]:
    """Time n_queries FAISS similarity searches.

    Returns percentile latencies in milliseconds.
    """
    load_index()
    metadata = _build_metadata()
    player_ids = list(metadata.keys())

    rng = np.random.default_rng(seed)
    query_ids = rng.choice(player_ids, size=min(n_queries, len(player_ids)), replace=False)

    latencies: list[float] = []

    # Warmup
    for qid in query_ids[:5]:
        search_similar(int(qid), k=k, role_filter=True, player_metadata=metadata)

    for qid in query_ids:
        t0 = time.perf_counter()
        search_similar(int(qid), k=k, role_filter=True, player_metadata=metadata)
        elapsed_ms = (time.perf_counter() - t0) * 1000
        latencies.append(elapsed_ms)

    arr = np.array(latencies)
    stats = {
        "n_queries": n_queries,
        "p50_ms": float(np.percentile(arr, 50)),
        "p95_ms": float(np.percentile(arr, 95)),
        "p99_ms": float(np.percentile(arr, 99)),
        "mean_ms": float(arr.mean()),
        "max_ms": float(arr.max()),
    }

    return stats


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    print("\n=== FAISS Query Latency Benchmark ===")
    stats = benchmark()
    for key, val in stats.items():
        if key == "n_queries":
            print(f"  Queries:  {int(val)}")
        else:
            print(f"  {key:10s}  {val:.2f}")

    if stats["p95_ms"] < 100:
        print("\n  PASS: p95 < 100ms")
    else:
        print(f"\n  FAIL: p95 = {stats['p95_ms']:.1f}ms (target < 100ms)")
