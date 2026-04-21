"""Step 7: Build FAISS index for similarity search.

StandardScaler → L2-normalise → FAISS IndexFlatIP.
Inner product on L2-normalised vectors = cosine similarity.

Output: faiss_index.bin, scaler.pkl, player_id_map.npy
"""

from __future__ import annotations

import logging
import pickle  # noqa: S403 — required for sklearn model serialisation (local-only)
import sys
import time
from pathlib import Path

import faiss
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler, normalize

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from app.utils.constants import FEATURE_NAMES  # noqa: E402

logger = logging.getLogger(__name__)

FEATURES_DIR = Path(__file__).resolve().parents[1].parent / "data" / "features"
MODELS_DIR = Path(__file__).resolve().parents[1].parent / "data" / "models"


def build_index(force: bool = False) -> Path:
    """Build and save FAISS index + supporting artefacts.

    Returns:
        Path to the FAISS index file.
    """
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    index_path = MODELS_DIR / "faiss_index.bin"
    scaler_path = MODELS_DIR / "scaler.pkl"
    map_path = MODELS_DIR / "player_id_map.npy"

    feature_path = FEATURES_DIR / "feature_matrix.parquet"
    if not feature_path.exists():
        logger.error("Feature matrix not found — run engineer_features first.")
        return index_path

    if index_path.exists() and not force:
        logger.info("Skipping index build — cached at %s", index_path)
        return index_path

    df = pd.read_parquet(feature_path)
    logger.info("Loaded feature matrix: %d players", len(df))

    # Extract feature matrix and player IDs
    X = df[FEATURE_NAMES].values.astype(np.float64)
    player_ids = df["player_id"].values.astype(np.int64)

    # StandardScaler
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # L2 normalisation — so inner product = cosine similarity
    X_norm = normalize(X_scaled, norm="l2").astype(np.float32)

    # Build FAISS index (IndexFlatIP = exact inner product search)
    dim = X_norm.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(X_norm)
    logger.info("FAISS index built: %d vectors of dimension %d", index.ntotal, dim)

    # Verify: self-query should return score ≈ 1.0
    D, I = index.search(X_norm[:5], 1)
    mean_self_score = D[:, 0].mean()
    logger.info(
        "Self-query verification: mean score = %.6f (expected ≈ 1.0)", mean_self_score,
    )
    if mean_self_score < 0.99:
        logger.warning(
            "Self-query score %.4f is below 0.99 — check normalisation!", mean_self_score,
        )

    # Save artefacts
    faiss.write_index(index, str(index_path))
    logger.info("FAISS index saved to %s", index_path)

    with open(scaler_path, "wb") as f:
        pickle.dump(scaler, f)
    logger.info("Scaler saved to %s", scaler_path)

    np.save(map_path, player_ids)
    logger.info("Player ID map saved to %s (%d IDs)", map_path, len(player_ids))

    return index_path


def run(force: bool = False) -> None:
    """Run index building step."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    )
    logger.info("=== Step 7: FAISS index building ===")
    t0 = time.perf_counter()
    build_index(force=force)
    logger.info("Index building complete in %.1fs", time.perf_counter() - t0)


if __name__ == "__main__":
    run(force="--force" in sys.argv)
