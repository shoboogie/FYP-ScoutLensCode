"""Tests for feature engineering, role classification, and FAISS index."""

from __future__ import annotations

import pickle  # noqa: S403 — loading locally-generated sklearn model
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import sys
_BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from app.utils.constants import FEATURE_NAMES, FEATURE_COUNT, ROLE_LABELS

DATA_DIR = Path(__file__).resolve().parents[1].parent / "data"
FEATURES_DIR = DATA_DIR / "features"
MODELS_DIR = DATA_DIR / "models"


# ── Feature engineering tests ────────────────────────────────────────


class TestFeatureEngineering:
    """Verify the 42-feature matrix is correct."""

    @pytest.fixture()
    def features(self) -> pd.DataFrame:
        path = FEATURES_DIR / "feature_matrix.parquet"
        if not path.exists():
            pytest.skip("Feature matrix not yet created")
        return pd.read_parquet(path)

    def test_feature_count(self, features: pd.DataFrame) -> None:
        """All 42 features must be present."""
        for feat in FEATURE_NAMES:
            assert feat in features.columns, f"Missing feature: {feat}"

    def test_no_nan_values(self, features: pd.DataFrame) -> None:
        """Feature matrix must have no NaN values."""
        nan_count = features[FEATURE_NAMES].isna().sum().sum()
        assert nan_count == 0, f"Found {nan_count} NaN values in feature matrix"

    def test_no_inf_values(self, features: pd.DataFrame) -> None:
        """Feature matrix must have no Inf values."""
        inf_count = np.isinf(features[FEATURE_NAMES].values).sum()
        assert inf_count == 0, f"Found {inf_count} Inf values in feature matrix"

    def test_player_count(self, features: pd.DataFrame) -> None:
        """Should match qualified players count."""
        assert 1000 <= len(features) <= 2200

    def test_per90_values_reasonable(self, features: pd.DataFrame) -> None:
        """Per-90 features should not exceed reasonable maximums."""
        assert features["goals_per90"].max() < 5.0
        assert features["passes_attempted_per90"].max() < 120.0

    def test_percentage_values_bounded(self, features: pd.DataFrame) -> None:
        """Percentage features should be between 0 and 100."""
        pct_features = [f for f in FEATURE_NAMES if "pct" in f]
        for feat in pct_features:
            assert features[feat].min() >= 0.0, f"{feat} has negative value"
            assert features[feat].max() <= 100.0, f"{feat} exceeds 100%"

    def test_metadata_columns(self, features: pd.DataFrame) -> None:
        """Feature matrix should include player metadata."""
        for col in ["player_id", "player_name", "team_name", "league"]:
            assert col in features.columns, f"Missing metadata column: {col}"


# ── Role classification tests ────────────────────────────────────────


class TestRoleClassification:
    """Verify role labels are assigned correctly."""

    @pytest.fixture()
    def features(self) -> pd.DataFrame:
        path = FEATURES_DIR / "feature_matrix.parquet"
        if not path.exists():
            pytest.skip("Feature matrix not yet created")
        df = pd.read_parquet(path)
        if "role_label" not in df.columns:
            pytest.skip("Role labels not yet assigned")
        return df

    def test_role_labels_assigned(self, features: pd.DataFrame) -> None:
        """Every player should have a role label."""
        assert features["role_label"].notna().all()

    def test_role_confidence_present(self, features: pd.DataFrame) -> None:
        """Every player should have a confidence score."""
        assert "role_confidence" in features.columns
        assert features["role_confidence"].notna().all()

    def test_role_confidence_range(self, features: pd.DataFrame) -> None:
        """Silhouette scores should be between -1 and 1."""
        assert features["role_confidence"].min() >= -1.0
        assert features["role_confidence"].max() <= 1.0

    def test_minimum_cluster_size(self, features: pd.DataFrame) -> None:
        """Every role should have at least 2 players (rare archetypes expected)."""
        role_counts = features["role_label"].value_counts()
        for role, count in role_counts.items():
            assert count >= 2, f"Role '{role}' has only {count} players"

    def test_role_model_exists(self) -> None:
        """Role model file should exist."""
        path = MODELS_DIR / "role_model.pkl"
        assert path.exists(), "Role model not found"


# ── FAISS index tests ────────────────────────────────────────────────


class TestFAISSIndex:
    """Verify FAISS index is built correctly."""

    def test_index_file_exists(self) -> None:
        path = MODELS_DIR / "faiss_index.bin"
        assert path.exists(), "FAISS index not found"

    def test_scaler_file_exists(self) -> None:
        path = MODELS_DIR / "scaler.pkl"
        assert path.exists(), "Scaler not found"

    def test_player_map_exists(self) -> None:
        path = MODELS_DIR / "player_id_map.npy"
        assert path.exists(), "Player ID map not found"

    def test_player_map_count(self) -> None:
        path = MODELS_DIR / "player_id_map.npy"
        if not path.exists():
            pytest.skip("Player ID map not yet created")
        ids = np.load(path)
        assert 1000 <= len(ids) <= 2200

    def test_self_query_score(self) -> None:
        """Self-query should return score approx 1.0."""
        import faiss

        index_path = MODELS_DIR / "faiss_index.bin"
        scaler_path = MODELS_DIR / "scaler.pkl"
        feature_path = FEATURES_DIR / "feature_matrix.parquet"

        if not all(p.exists() for p in [index_path, scaler_path, feature_path]):
            pytest.skip("FAISS artefacts not yet created")

        index = faiss.read_index(str(index_path))
        with open(scaler_path, "rb") as f:
            scaler = pickle.load(f)  # noqa: S301 — local model only

        df = pd.read_parquet(feature_path)
        X = df[FEATURE_NAMES].values[:5].astype(np.float64)
        X_scaled = scaler.transform(X)
        from sklearn.preprocessing import normalize
        X_norm = normalize(X_scaled, norm="l2").astype(np.float32)

        D, I = index.search(X_norm, 1)
        mean_score = D[:, 0].mean()
        assert mean_score > 0.99, f"Self-query mean score {mean_score:.4f} < 0.99"
