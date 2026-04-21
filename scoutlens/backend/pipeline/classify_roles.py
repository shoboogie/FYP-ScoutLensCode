"""Step 6: Role classification via hierarchical clustering.

Ward's method on z-scored 42-feature vectors → 14 functional role labels.
Silhouette-guided cluster count selection within TARGET_CLUSTER_RANGE.

Output:
  - data/features/feature_matrix.parquet (updated with role_label, role_confidence)
  - data/models/role_model.pkl
"""

from __future__ import annotations

import logging
import pickle
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import fcluster, linkage
from sklearn.metrics import silhouette_samples, silhouette_score
from sklearn.preprocessing import StandardScaler

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from app.utils.constants import (  # noqa: E402
    FEATURE_NAMES,
    POSITION_GROUPS,
    ROLE_LABELS,
    TARGET_CLUSTER_RANGE,
)

logger = logging.getLogger(__name__)

FEATURES_DIR = Path(__file__).resolve().parents[1].parent / "data" / "features"
MODELS_DIR = Path(__file__).resolve().parents[1].parent / "data" / "models"

# Build reverse lookup: position_name → position_group
_POSITION_TO_GROUP: dict[str, str] = {}
for group_name, group_info in POSITION_GROUPS.items():
    for pos in group_info["positions"]:
        _POSITION_TO_GROUP[pos] = group_name

# Build reverse lookup: position_group → allowed roles
_GROUP_TO_ROLES: dict[str, list[str]] = {
    group_name: group_info["roles"]
    for group_name, group_info in POSITION_GROUPS.items()
}


def _score_role(role: str, z: np.ndarray, fi: dict[str, int]) -> float:
    """Score how well a player's z-profile matches a given role archetype."""
    if role == "Ball-Playing CB":
        return (z[fi["progressive_passes_per90"]] + z[fi["passes_under_pressure_pct"]]
                + z[fi["progressive_carries_per90"]] - z[fi["clearances_per90"]] * 0.5)

    elif role == "Aerial/Stopper CB":
        return (z[fi["aerial_win_pct"]] + z[fi["interceptions_per90"]]
                + z[fi["blocks_per90"]] + z[fi["clearances_per90"]])

    elif role == "Attacking Full-Back":
        return (z[fi["crosses_per90"]] + z[fi["key_passes_per90"]]
                + z[fi["progressive_carries_per90"]] + z[fi["carries_into_box_per90"]])

    elif role == "Inverted Full-Back":
        return (z[fi["passes_attempted_per90"]] + z[fi["pass_completion_pct"]]
                + z[fi["progressive_passes_per90"]] - z[fi["crosses_per90"]])

    elif role == "Deep-Lying Playmaker":
        return (z[fi["progressive_pass_distance_per90"]] + z[fi["passes_attempted_per90"]]
                + z[fi["switches_per90"]] + z[fi["long_pass_completion_pct"]])

    elif role == "Ball-Winning Midfielder":
        return (z[fi["tackles_per90"]] + z[fi["interceptions_per90"]]
                + z[fi["ball_recoveries_per90"]] + z[fi["pressures_per90"]])

    elif role == "Box-to-Box Midfielder":
        return (z[fi["progressive_carries_per90"]] + z[fi["touches_in_box_per90"]]
                + z[fi["pressures_per90"]] + z[fi["ball_recoveries_per90"]])

    elif role == "Advanced Playmaker":
        return (z[fi["xa_per90"]] + z[fi["through_balls_per90"]]
                + z[fi["key_passes_per90"]] + z[fi["passes_into_box_per90"]])

    elif role == "Inside Forward":
        return (z[fi["xg_per90"]] + z[fi["shots_per90"]]
                + z[fi["progressive_carries_per90"]] - z[fi["crosses_per90"]])

    elif role == "Touchline Winger":
        return (z[fi["crosses_per90"]] + z[fi["dribbles_attempted_per90"]]
                + z[fi["progressive_carries_per90"]] - z[fi["shots_per90"]] * 0.5)

    elif role == "Complete Forward":
        return (z[fi["xg_per90"]] + z[fi["key_passes_per90"]]
                + z[fi["ball_receipts_per90"]] + z[fi["aerial_win_pct"]])

    elif role == "Poacher":
        return (z[fi["goals_per90"]] + z[fi["xg_per_shot"]]
                + z[fi["touches_in_box_per90"]] - z[fi["progressive_passes_per90"]])

    elif role == "Target Forward":
        return (z[fi["aerial_duels_per90"]] + z[fi["aerial_win_pct"]]
                + z[fi["fouls_won_per90"]] - z[fi["dribbles_attempted_per90"]])

    elif role == "Pressing Forward":
        return (z[fi["pressures_per90"]] + z[fi["ball_recoveries_per90"]]
                + z[fi["xa_per90"]] - z[fi["goals_per90"]] * 0.3)

    return 0.0


def classify_roles(force: bool = False) -> Path:
    """Run hierarchical clustering to assign role labels.

    Returns:
        Path to updated feature matrix.
    """
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    feature_path = FEATURES_DIR / "feature_matrix.parquet"
    model_path = MODELS_DIR / "role_model.pkl"

    if not feature_path.exists():
        logger.error("Feature matrix not found — run engineer_features first.")
        return feature_path

    if model_path.exists() and not force:
        logger.info("Skipping role classification — cached at %s", model_path)
        return feature_path

    df = pd.read_parquet(feature_path)
    logger.info("Loaded feature matrix: %d players", len(df))

    # Extract feature matrix
    X = df[FEATURE_NAMES].values.astype(np.float64)

    # Z-score standardisation
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Ward's hierarchical clustering
    logger.info("Computing Ward's linkage on %d x %d matrix…", *X_scaled.shape)
    Z = linkage(X_scaled, method="ward", metric="euclidean")

    # Try different numbers of clusters and pick best silhouette
    min_k, max_k = TARGET_CLUSTER_RANGE
    best_k = min_k
    best_score = -1.0

    for k in range(min_k, max_k + 1):
        labels = fcluster(Z, t=k, criterion="maxclust")
        score = silhouette_score(X_scaled, labels)
        logger.info("  k=%d: silhouette=%.4f", k, score)
        if score > best_score:
            best_score = score
            best_k = k

    logger.info("Best k=%d with silhouette=%.4f", best_k, best_score)

    # Final clustering
    cluster_labels = fcluster(Z, t=best_k, criterion="maxclust")
    df["cluster_id"] = cluster_labels

    # Per-player silhouette scores (role confidence)
    sil_samples = silhouette_samples(X_scaled, cluster_labels)
    df["role_confidence"] = sil_samples

    # Per-player role assignment — constrained by position group.
    # Each player is assigned the best-fitting role from their position
    # group's candidate roles, scored against their individual z-profile.
    fi = {name: i for i, name in enumerate(FEATURE_NAMES)}
    role_labels_out: list[str] = []

    for idx, row in df.iterrows():
        pos = row.get("primary_position")
        group = _POSITION_TO_GROUP.get(pos, "Unknown") if pos else "Unknown"
        candidates = _GROUP_TO_ROLES.get(group, ROLE_LABELS)

        if len(candidates) == 1:
            role_labels_out.append(candidates[0])
            continue

        player_z = X_scaled[len(role_labels_out)]
        best_role = candidates[0]
        best_score = -999.0

        for role in candidates:
            score = _score_role(role, player_z, fi)
            if score > best_score:
                best_score = score
                best_role = role

        role_labels_out.append(best_role)

    df["role_label"] = role_labels_out

    # Log role distribution per position group
    for group_name in _GROUP_TO_ROLES:
        group_positions = POSITION_GROUPS[group_name]["positions"]
        group_players = df[df["primary_position"].isin(group_positions)]
        if len(group_players) > 0:
            dist = group_players["role_label"].value_counts().to_dict()
            logger.info("  %s: %s", group_name, dist)

    model = {
        "linkage": Z,
        "scaler_mean": scaler.mean_,
        "scaler_scale": scaler.scale_,
        "best_k": best_k,
        "best_silhouette": best_score,
        "feature_names": FEATURE_NAMES,
    }
    with open(model_path, "wb") as f:
        pickle.dump(model, f)
    logger.info("Role model saved to %s", model_path)

    # Save updated feature matrix
    df.to_parquet(feature_path, index=False)
    logger.info("Feature matrix updated with role labels → %s", feature_path)

    # Summary stats
    role_dist = df["role_label"].value_counts()
    logger.info("Role distribution:\n%s", role_dist.to_string())

    return feature_path


def run(force: bool = False) -> None:
    """Run role classification step."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    )
    logger.info("=== Step 6: Role classification ===")
    t0 = time.perf_counter()
    classify_roles(force=force)
    logger.info("Role classification complete in %.1fs", time.perf_counter() - t0)


if __name__ == "__main__":
    run(force="--force" in sys.argv)
