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


def _label_cluster(
    cluster_members: pd.DataFrame,
    centroid_z: np.ndarray,
    feature_names: list[str],
) -> str:
    """Assign a role label to a cluster based on its centroid profile.

    Uses the position distribution of cluster members and the centroid's
    z-score signature to find the best matching role label.
    """
    # Determine the dominant position group in this cluster
    positions = cluster_members["primary_position"].dropna()
    group_counts: dict[str, int] = {}
    for pos in positions:
        group = _POSITION_TO_GROUP.get(pos, "Unknown")
        group_counts[group] = group_counts.get(group, 0) + 1

    if not group_counts:
        return "Unknown"

    dominant_group = max(group_counts, key=group_counts.get)
    candidate_roles = _GROUP_TO_ROLES.get(dominant_group, [])

    if not candidate_roles:
        return dominant_group

    if len(candidate_roles) == 1:
        return candidate_roles[0]

    # Disambiguate within the group using centroid z-scores and
    # signature stats for each candidate role
    role_scores: dict[str, float] = {}

    # Feature index lookup
    fi = {name: i for i, name in enumerate(feature_names)}

    for role in candidate_roles:
        score = 0.0

        if role == "Ball-Playing CB":
            score += centroid_z[fi["progressive_passes_per90"]]
            score += centroid_z[fi["passes_under_pressure_pct"]]
            score += centroid_z[fi["progressive_carries_per90"]]
            score -= centroid_z[fi["clearances_per90"]] * 0.5

        elif role == "Aerial/Stopper CB":
            score += centroid_z[fi["aerial_win_pct"]]
            score += centroid_z[fi["interceptions_per90"]]
            score += centroid_z[fi["blocks_per90"]]
            score += centroid_z[fi["clearances_per90"]]

        elif role == "Attacking Full-Back":
            score += centroid_z[fi["crosses_per90"]]
            score += centroid_z[fi["key_passes_per90"]]
            score += centroid_z[fi["progressive_carries_per90"]]
            score += centroid_z[fi["carries_into_box_per90"]]

        elif role == "Inverted Full-Back":
            score += centroid_z[fi["passes_attempted_per90"]]
            score += centroid_z[fi["pass_completion_pct"]]
            score += centroid_z[fi["progressive_passes_per90"]]
            score -= centroid_z[fi["crosses_per90"]]

        elif role == "Deep-Lying Playmaker":
            score += centroid_z[fi["progressive_pass_distance_per90"]]
            score += centroid_z[fi["passes_attempted_per90"]]
            score += centroid_z[fi["switches_per90"]]
            score += centroid_z[fi["long_pass_completion_pct"]]

        elif role == "Ball-Winning Midfielder":
            score += centroid_z[fi["tackles_per90"]]
            score += centroid_z[fi["interceptions_per90"]]
            score += centroid_z[fi["ball_recoveries_per90"]]
            score += centroid_z[fi["pressures_per90"]]

        elif role == "Box-to-Box Midfielder":
            score += centroid_z[fi["progressive_carries_per90"]]
            score += centroid_z[fi["touches_in_box_per90"]]
            score += centroid_z[fi["pressures_per90"]]
            score += centroid_z[fi["ball_recoveries_per90"]]

        elif role == "Advanced Playmaker":
            score += centroid_z[fi["xa_per90"]]
            score += centroid_z[fi["through_balls_per90"]]
            score += centroid_z[fi["key_passes_per90"]]
            score += centroid_z[fi["passes_into_box_per90"]]

        elif role == "Inside Forward":
            score += centroid_z[fi["xg_per90"]]
            score += centroid_z[fi["shots_per90"]]
            score += centroid_z[fi["progressive_carries_per90"]]
            score -= centroid_z[fi["crosses_per90"]]

        elif role == "Touchline Winger":
            score += centroid_z[fi["crosses_per90"]]
            score += centroid_z[fi["dribbles_attempted_per90"]]
            score += centroid_z[fi["progressive_carries_per90"]]
            score -= centroid_z[fi["shots_per90"]] * 0.5

        elif role == "Complete Forward":
            score += centroid_z[fi["xg_per90"]]
            score += centroid_z[fi["key_passes_per90"]]
            score += centroid_z[fi["ball_receipts_per90"]]
            score += centroid_z[fi["aerial_win_pct"]]

        elif role == "Poacher":
            score += centroid_z[fi["goals_per90"]]
            score += centroid_z[fi["xg_per_shot"]]
            score += centroid_z[fi["touches_in_box_per90"]]
            score -= centroid_z[fi["progressive_passes_per90"]]

        elif role == "Target Forward":
            score += centroid_z[fi["aerial_duels_per90"]]
            score += centroid_z[fi["aerial_win_pct"]]
            score += centroid_z[fi["fouls_won_per90"]]
            score -= centroid_z[fi["dribbles_attempted_per90"]]

        elif role == "Pressing Forward":
            score += centroid_z[fi["pressures_per90"]]
            score += centroid_z[fi["ball_recoveries_per90"]]
            score += centroid_z[fi["xa_per90"]]
            score -= centroid_z[fi["goals_per90"]] * 0.3

        role_scores[role] = score

    return max(role_scores, key=role_scores.get)


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

    # Assign role labels to each cluster
    cluster_role_map: dict[int, str] = {}
    used_labels: set[str] = set()

    for cid in sorted(df["cluster_id"].unique()):
        cluster_mask = df["cluster_id"] == cid
        cluster_members = df[cluster_mask]
        cluster_indices = np.where(cluster_mask)[0]
        centroid_z = X_scaled[cluster_indices].mean(axis=0)

        label = _label_cluster(cluster_members, centroid_z, FEATURE_NAMES)

        # Avoid duplicate labels — append cluster ID if needed
        if label in used_labels:
            for alt_label in ROLE_LABELS:
                if alt_label not in used_labels:
                    label = alt_label
                    break
            else:
                label = f"{label} ({cid})"

        cluster_role_map[cid] = label
        used_labels.add(label)

        logger.info(
            "  Cluster %d → %s (%d players, sil=%.3f)",
            cid, label, len(cluster_members),
            sil_samples[cluster_indices].mean(),
        )

    df["role_label"] = df["cluster_id"].map(cluster_role_map)

    # Log position sanity check per cluster
    for cid, role in cluster_role_map.items():
        members = df[df["cluster_id"] == cid]
        pos_dist = members["primary_position"].apply(
            lambda p: _POSITION_TO_GROUP.get(p, "Unknown")
        ).value_counts()
        logger.info("  %s position breakdown: %s", role, pos_dist.to_dict())

    # Save model artefacts (pickle is used intentionally for sklearn
    # model serialisation; the file is only generated and loaded locally)
    model = {
        "linkage": Z,
        "scaler_mean": scaler.mean_,
        "scaler_scale": scaler.scale_,
        "cluster_role_map": cluster_role_map,
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
