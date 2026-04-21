"""System Usability Scale (SUS) analysis.

Processes SUS questionnaire responses from user study participants.
Computes individual SUS scores and the group mean.

Target from spec: mean SUS >= 70 (above average usability).

SUS scoring:
  - 10 questions, each 1-5 Likert scale
  - Odd questions (1,3,5,7,9): score = response - 1
  - Even questions (2,4,6,8,10): score = 5 - response
  - SUS = sum(scores) * 2.5 → range 0–100
"""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

EXPORTS_DIR = Path(__file__).resolve().parents[0].parent / "data" / "exports"


def compute_sus_scores(responses: pd.DataFrame) -> pd.Series:
    """Compute SUS score for each participant.

    Expects a DataFrame with columns Q1–Q10 (values 1–5).
    """
    scores = pd.Series(0.0, index=responses.index)

    for q in range(1, 11):
        col = f"Q{q}"
        if col not in responses.columns:
            continue
        if q % 2 == 1:  # odd: positive phrasing
            scores += responses[col] - 1
        else:           # even: negative phrasing
            scores += 5 - responses[col]

    return scores * 2.5


def analyse_sus(csv_path: str | None = None) -> dict[str, float]:
    """Load SUS responses and compute statistics.

    If no CSV provided, generates example data for demonstration.
    """
    if csv_path and Path(csv_path).exists():
        df = pd.read_csv(csv_path)
    else:
        # Demonstration data — replace with actual user study responses
        logger.info("No SUS data file found — using demonstration data")
        rng = np.random.default_rng(42)
        n = 10
        data = {}
        for q in range(1, 11):
            if q % 2 == 1:
                data[f"Q{q}"] = rng.integers(3, 6, size=n)  # positive Qs skew high
            else:
                data[f"Q{q}"] = rng.integers(1, 3, size=n)  # negative Qs skew low
        df = pd.DataFrame(data)

    scores = compute_sus_scores(df)

    stats = {
        "n_participants": len(scores),
        "mean_sus": float(scores.mean()),
        "median_sus": float(scores.median()),
        "std_sus": float(scores.std()),
        "min_sus": float(scores.min()),
        "max_sus": float(scores.max()),
    }

    # SUS grade boundaries (Bangor, Kortum & Miller, 2009)
    mean = stats["mean_sus"]
    if mean >= 80.3:
        stats["grade"] = "A"
    elif mean >= 68:
        stats["grade"] = "B"
    elif mean >= 51:
        stats["grade"] = "C"
    else:
        stats["grade"] = "D/F"

    return stats


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    print("\n=== SUS Analysis ===")

    # Check for actual data first
    csv = EXPORTS_DIR / "sus_responses.csv"
    result = analyse_sus(str(csv) if csv.exists() else None)

    for key, val in result.items():
        if key == "grade":
            print(f"  Grade:         {val}")
        elif key == "n_participants":
            print(f"  Participants:  {int(val)}")
        else:
            print(f"  {key:15s} {val:.1f}")

    if result["mean_sus"] >= 70:
        print(f"\n  PASS: SUS {result['mean_sus']:.1f} >= 70 (Grade {result['grade']})")
    else:
        print(f"\n  BELOW TARGET: SUS {result['mean_sus']:.1f} (target >= 70)")
