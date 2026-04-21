"""Generate dissertation evaluation tables.

Runs all evaluation metrics and outputs formatted tables for
inclusion in the dissertation (Chapter 6: Evaluation).
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[0].parent / "backend"
sys.path.insert(0, str(_PROJECT_ROOT))

logger = logging.getLogger(__name__)


def generate_all() -> None:
    """Run all evaluations and print formatted results."""

    print("=" * 65)
    print("  ScoutLens Evaluation Results")
    print("=" * 65)

    # 1. Role Consistency
    print("\n--- Table 6.1: Role Consistency at k ---")
    try:
        from evaluation.role_consistency import evaluate_rc_at_k
        rc_filtered = evaluate_rc_at_k(n_queries=100, role_filter=True)
        rc_unfiltered = evaluate_rc_at_k(n_queries=100, role_filter=False)
        print(f"{'Condition':<30} {'RC@5':>8} {'RC@10':>8}")
        print("-" * 48)
        print(f"{'A: Cosine (no role filter)':<30} {rc_unfiltered.get(5, 0):.4f}   {rc_unfiltered.get(10, 0):.4f}")
        print(f"{'B: Cosine + role filter':<30} {rc_filtered.get(5, 0):.4f}   {rc_filtered.get(10, 0):.4f}")
    except Exception as e:
        print(f"  Skipped: {e}")

    # 2. Latency
    print("\n--- Table 6.2: Query Latency (ms) ---")
    try:
        from evaluation.latency_benchmark import benchmark
        stats = benchmark(n_queries=500)
        print(f"{'Metric':<12} {'Value':>10}")
        print("-" * 24)
        for key in ["p50_ms", "p95_ms", "p99_ms", "mean_ms", "max_ms"]:
            print(f"  {key:<10} {stats[key]:>8.2f}")
    except Exception as e:
        print(f"  Skipped: {e}")

    # 3. Temporal Stability
    print("\n--- Table 6.3: Temporal Stability ---")
    try:
        from evaluation.temporal_stability import evaluate_stability
        stab = evaluate_stability()
        print(f"  Mean Pearson r:   {stab['mean_r']:.4f}")
        print(f"  Median Pearson r: {stab['median_r']:.4f}")
    except Exception as e:
        print(f"  Skipped: {e}")

    # 4. Ablation
    print("\n--- Table 6.4: Dimension Ablation (RC@10 drop) ---")
    try:
        from evaluation.ablation_study import run_ablation
        drops = run_ablation(n_queries=100)
        print(f"{'Dimension':<20} {'RC@10 Drop':>12}")
        print("-" * 34)
        for dim, drop in sorted(drops.items(), key=lambda x: x[1], reverse=True):
            print(f"  {dim:<18} {drop:>+10.4f}")
    except Exception as e:
        print(f"  Skipped: {e}")

    # 5. SUS
    print("\n--- Table 6.5: System Usability Scale ---")
    try:
        from evaluation.sus_analysis import analyse_sus
        sus = analyse_sus()
        print(f"  Participants: {int(sus['n_participants'])}")
        print(f"  Mean SUS:     {sus['mean_sus']:.1f}")
        print(f"  Grade:        {sus['grade']}")
    except Exception as e:
        print(f"  Skipped: {e}")

    # 6. Data summary
    print("\n--- Table 6.6: Dataset Summary ---")
    try:
        import pandas as pd
        features_path = Path(__file__).resolve().parents[0].parent / "data" / "features" / "feature_matrix.parquet"
        df = pd.read_parquet(features_path)
        print(f"  Total players:    {len(df)}")
        print(f"  Features:         {len([c for c in df.columns if c in __import__('app.utils.constants', fromlist=['FEATURE_NAMES']).FEATURE_NAMES])}")
        print(f"  Leagues:          {df['league'].nunique()}")
        print(f"  Roles assigned:   {df['role_label'].nunique()}")
        league_counts = df["league"].value_counts()
        for league, count in league_counts.items():
            print(f"    {league}: {count}")
    except Exception as e:
        print(f"  Skipped: {e}")

    print("\n" + "=" * 65)


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
    generate_all()
