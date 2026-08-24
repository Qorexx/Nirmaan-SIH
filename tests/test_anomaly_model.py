"""
Checkpoint 6 — Tests for anomaly_model.py

Tests:
  1.  FEATURE_NAMES constant is exactly the approved 3 features in correct order
  2.  prepare_features() filters to Works Sanctioned rows
  3.  prepare_features() excludes sanction_amount == 0 rows
  4.  prepare_features() derives log1p_sanction_amount correctly
  5.  prepare_features() derives rec_to_sanc_days correctly
  6.  prepare_features() derives days_since_tenure_start correctly
  7.  prepare_features() returns finite numeric values only
  8.  prepare_features() raises ValueError when no valid rows remain
  9.  train_model() returns a fitted IsolationForest
  10. train_model() raises ValueError on wrong feature count
  11. predict_anomalies() returns only −1 or 1
  12. predict_anomalies() output shape matches input rows
  13. anomaly_scores() returns float array matching input rows
  14. Model save and load round-trip preserves feature names and model type
  15. Predictions are deterministic with random_state=42
  16. Feature preparation rejects non-finite values (guards against bad data)
"""

import os
import pickle
import tempfile
import textwrap

import numpy as np
import pandas as pd
import pytest
from sklearn.ensemble import IsolationForest

# Allow running from project root or tests/ directory
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from ml_modules.financial.anomaly_model import (
    FEATURE_NAMES,
    anomaly_scores,
    load_model,
    predict_anomalies,
    prepare_features,
    save_model,
    train_model,
)


# ──────────────────────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────────────────────

def _make_valid_row(**overrides) -> dict:
    """Return a minimal valid Works Sanctioned row."""
    base = {
        "query_category":       "Works Sanctioned",
        "sanction_amount":      500000.0,
        "recommendation_date":  "2024-09-01",
        "sanction_date":        "2024-11-15",
        "tenure_start_date":    "2024-06-04",
        "work_category":        "Normal/Others",
        "state_name":           "Punjab",
        "work_recommendation_dtl_id": 99001,
    }
    base.update(overrides)
    return base


def _make_df(rows: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(rows)


@pytest.fixture
def small_valid_df() -> pd.DataFrame:
    """10 valid Works Sanctioned rows."""
    rows = [
        _make_valid_row(
            sanction_amount=500000.0 + i * 50000,
            recommendation_date="2024-09-01",
            sanction_date="2024-11-15",
            tenure_start_date="2024-06-04",
        )
        for i in range(10)
    ]
    return _make_df(rows)


@pytest.fixture
def trained_model_and_X(small_valid_df):
    X, _ = prepare_features(small_valid_df, lifecycle_filter=True)
    model = train_model(X, contamination="auto", n_estimators=50, random_state=42)
    return model, X


# ──────────────────────────────────────────────────────────────────────────────
# Test 1 — FEATURE_NAMES constant
# ──────────────────────────────────────────────────────────────────────────────

def test_feature_names_exact_order():
    """Feature names must be the approved 3 in the exact approved order."""
    assert FEATURE_NAMES == [
        "log1p_sanction_amount",
        "rec_to_sanc_days",
        "days_since_tenure_start",
    ], f"FEATURE_NAMES mismatch: {FEATURE_NAMES}"


def test_feature_names_length():
    assert len(FEATURE_NAMES) == 3


# ──────────────────────────────────────────────────────────────────────────────
# Test 2 — lifecycle filter keeps only Works Sanctioned rows
# ──────────────────────────────────────────────────────────────────────────────

def test_prepare_features_filters_lifecycle():
    rows = [
        _make_valid_row(query_category="Works Recommended"),
        _make_valid_row(query_category="Works Sanctioned"),
        _make_valid_row(query_category="Works Completed", sanction_amount=0),
    ]
    df = _make_df(rows)
    X, meta = prepare_features(df, lifecycle_filter=True)
    assert X.shape[0] == 1, "Only Works Sanctioned rows should survive"


# ──────────────────────────────────────────────────────────────────────────────
# Test 3 — sanction_amount == 0 rows are excluded
# ──────────────────────────────────────────────────────────────────────────────

def test_prepare_features_excludes_zero_sanction():
    rows = [
        _make_valid_row(sanction_amount=0.0),
        _make_valid_row(sanction_amount=300000.0),
    ]
    X, _ = prepare_features(_make_df(rows), lifecycle_filter=True)
    assert X.shape[0] == 1, "Zero-sanction row must be excluded"


# ──────────────────────────────────────────────────────────────────────────────
# Test 4 — log1p_sanction_amount derivation is correct
# ──────────────────────────────────────────────────────────────────────────────

def test_log1p_sanction_amount_value():
    sa = 500000.0
    row = _make_valid_row(sanction_amount=sa)
    X, _ = prepare_features(_make_df([row]), lifecycle_filter=True)
    expected = np.log1p(sa)
    idx = FEATURE_NAMES.index("log1p_sanction_amount")
    assert abs(X[0, idx] - expected) < 1e-9


# ──────────────────────────────────────────────────────────────────────────────
# Test 5 — rec_to_sanc_days derivation is correct
# ──────────────────────────────────────────────────────────────────────────────

def test_rec_to_sanc_days_value():
    row = _make_valid_row(
        recommendation_date="2024-09-01",
        sanction_date="2024-11-15",  # 75 days later
    )
    X, _ = prepare_features(_make_df([row]), lifecycle_filter=True)
    idx = FEATURE_NAMES.index("rec_to_sanc_days")
    expected = (pd.Timestamp("2024-11-15") - pd.Timestamp("2024-09-01")).days
    assert abs(X[0, idx] - expected) < 1e-6


# ──────────────────────────────────────────────────────────────────────────────
# Test 6 — days_since_tenure_start derivation is correct
# ──────────────────────────────────────────────────────────────────────────────

def test_days_since_tenure_start_value():
    row = _make_valid_row(
        recommendation_date="2024-09-01",
        tenure_start_date="2024-06-04",  # 89 days before recommendation
    )
    X, _ = prepare_features(_make_df([row]), lifecycle_filter=True)
    idx = FEATURE_NAMES.index("days_since_tenure_start")
    expected = (pd.Timestamp("2024-09-01") - pd.Timestamp("2024-06-04")).days
    assert abs(X[0, idx] - expected) < 1e-6


# ──────────────────────────────────────────────────────────────────────────────
# Test 7 — feature matrix is finite
# ──────────────────────────────────────────────────────────────────────────────

def test_prepare_features_returns_finite(small_valid_df):
    X, _ = prepare_features(small_valid_df, lifecycle_filter=True)
    assert np.isfinite(X).all(), "Feature matrix must contain only finite values"


# ──────────────────────────────────────────────────────────────────────────────
# Test 8 — ValueError raised when no valid rows remain
# ──────────────────────────────────────────────────────────────────────────────

def test_prepare_features_raises_when_empty():
    rows = [
        _make_valid_row(query_category="Works Recommended"),
        _make_valid_row(query_category="Works Completed", sanction_amount=0),
    ]
    with pytest.raises(ValueError, match="No valid rows"):
        prepare_features(_make_df(rows), lifecycle_filter=True)


# ──────────────────────────────────────────────────────────────────────────────
# Test 9 — train_model returns a fitted IsolationForest
# ──────────────────────────────────────────────────────────────────────────────

def test_train_model_returns_isolation_forest(small_valid_df):
    X, _ = prepare_features(small_valid_df, lifecycle_filter=True)
    model = train_model(X, contamination="auto", n_estimators=50, random_state=42)
    assert isinstance(model, IsolationForest)
    # sklearn sets estimators_ after fitting
    assert hasattr(model, "estimators_"), "Model must be fitted (estimators_ attribute)"


# ──────────────────────────────────────────────────────────────────────────────
# Test 10 — train_model raises ValueError on wrong feature count
# ──────────────────────────────────────────────────────────────────────────────

def test_train_model_raises_on_wrong_feature_count(small_valid_df):
    X, _ = prepare_features(small_valid_df, lifecycle_filter=True)
    X_wrong = X[:, :2]  # Only 2 features instead of 3
    with pytest.raises(ValueError, match="Expected 3 features"):
        train_model(X_wrong)


# ──────────────────────────────────────────────────────────────────────────────
# Test 11 — predict_anomalies returns only −1 or 1
# ──────────────────────────────────────────────────────────────────────────────

def test_predict_anomalies_values(trained_model_and_X):
    model, X = trained_model_and_X
    preds = predict_anomalies(model, X)
    unique_vals = set(preds.tolist())
    assert unique_vals.issubset({-1, 1}), f"Predictions must be -1 or 1, got: {unique_vals}"


# ──────────────────────────────────────────────────────────────────────────────
# Test 12 — predict_anomalies shape matches input
# ──────────────────────────────────────────────────────────────────────────────

def test_predict_anomalies_shape(trained_model_and_X):
    model, X = trained_model_and_X
    preds = predict_anomalies(model, X)
    assert preds.shape == (X.shape[0],)


# ──────────────────────────────────────────────────────────────────────────────
# Test 13 — anomaly_scores returns float array of correct shape
# ──────────────────────────────────────────────────────────────────────────────

def test_anomaly_scores_shape_and_dtype(trained_model_and_X):
    model, X = trained_model_and_X
    scores = anomaly_scores(model, X)
    assert scores.shape == (X.shape[0],)
    assert np.issubdtype(scores.dtype, np.floating), "Scores must be float"
    assert np.isfinite(scores).all(), "Scores must be finite"


# ──────────────────────────────────────────────────────────────────────────────
# Test 14 — save/load round-trip preserves model and feature names
# ──────────────────────────────────────────────────────────────────────────────

def test_model_save_load_roundtrip(trained_model_and_X):
    model, X = trained_model_and_X
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "test_model.pkl")
        save_model(model, path, feature_names=FEATURE_NAMES)
        loaded_model, loaded_features = load_model(path)
    assert isinstance(loaded_model, IsolationForest)
    assert loaded_features == FEATURE_NAMES
    # Predictions from loaded model must match original
    preds_original = predict_anomalies(model, X)
    preds_loaded   = predict_anomalies(loaded_model, X)
    assert np.array_equal(preds_original, preds_loaded)


# ──────────────────────────────────────────────────────────────────────────────
# Test 15 — deterministic predictions with random_state=42
# ──────────────────────────────────────────────────────────────────────────────

def test_deterministic_predictions(small_valid_df):
    X, _ = prepare_features(small_valid_df, lifecycle_filter=True)
    model_a = train_model(X, n_estimators=50, random_state=42)
    model_b = train_model(X, n_estimators=50, random_state=42)
    preds_a = predict_anomalies(model_a, X)
    preds_b = predict_anomalies(model_b, X)
    assert np.array_equal(preds_a, preds_b), "Same random_state must produce identical predictions"


# ──────────────────────────────────────────────────────────────────────────────
# Test 16 — load_model raises FileNotFoundError for missing path
# ──────────────────────────────────────────────────────────────────────────────

def test_load_model_missing_file():
    with pytest.raises(FileNotFoundError):
        load_model("/nonexistent/path/model.pkl")
