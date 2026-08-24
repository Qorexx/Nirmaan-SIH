"""
Checkpoint 6 — Isolation Forest Anomaly Model (SIH26102 / Person 1)

Provides reusable functions for:
  - preparing model features from an MPLADS project DataFrame
  - training the Isolation Forest
  - saving / loading the trained model artifact
  - predicting anomalies and returning anomaly scores

IMPORTANT DESIGN CONSTRAINTS:
  - Features: log1p_sanction_amount, rec_to_sanc_days, days_since_tenure_start
  - Training population: Works Sanctioned rows, sanction_amount > 0, rec_to_sanc_days not null
  - No StandardScaler (IsolationForest is tree-based; scaling does not affect tree splits)
  - log1p is applied inside prepare_features() — raw sanction_amount enters; log1p exits
  - Predictions of −1 are "model-detected anomalous records"; NOT confirmed fraud
  - Do NOT modify the source CSV or any backend files
"""

from __future__ import annotations

import logging
import os
import pickle
from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# Public constants
# ──────────────────────────────────────────────────────────────────────────────

#: Exact feature names in the order the model expects them.
#: DO NOT reorder without retraining.
FEATURE_NAMES: list[str] = [
    "log1p_sanction_amount",
    "rec_to_sanc_days",
    "days_since_tenure_start",
]

#: Default model hyperparameters
DEFAULT_CONTAMINATION = "auto"
DEFAULT_N_ESTIMATORS = 200
DEFAULT_RANDOM_STATE = 42


# ──────────────────────────────────────────────────────────────────────────────
# Feature preparation
# ──────────────────────────────────────────────────────────────────────────────

def prepare_features(
    df: pd.DataFrame,
    lifecycle_filter: bool = True,
) -> tuple[np.ndarray, pd.DataFrame]:
    """Derive and validate the 3 approved features from a raw MPLADS DataFrame.

    Parameters
    ----------
    df:
        Raw DataFrame loaded from mplads_projects.csv (or any DataFrame with
        the same column schema).
    lifecycle_filter:
        If True (default), restrict to Works Sanctioned rows where
        sanction_amount > 0.  Set to False only when calling on pre-filtered
        data (e.g., a single-row inference payload).

    Returns
    -------
    X : np.ndarray  shape (n_valid, 3)
        Finite numeric feature matrix, columns = FEATURE_NAMES.
    meta : pd.DataFrame
        Row-aligned metadata (index preserved from the filtered df) useful
        for annotating predictions back to source records.

    Raises
    ------
    ValueError
        If no valid rows remain after filtering, or if any feature column
        contains non-finite values.
    """
    work_df = df.copy() if not lifecycle_filter else (
        df[df["query_category"] == "Works Sanctioned"].copy()
    )

    # ── 1. Apply population filter ─────────────────────────────────────────
    if lifecycle_filter:
        initial_ws = len(work_df)
        work_df = work_df[work_df["sanction_amount"] > 0]
        excluded_zero = initial_ws - len(work_df)
        logger.info("[prepare_features] Excluded %d rows with sanction_amount == 0", excluded_zero)

    # ── 2. Derive temporal features ────────────────────────────────────────
    rec_dt  = pd.to_datetime(work_df["recommendation_date"], errors="coerce")
    sanc_dt = pd.to_datetime(work_df["sanction_date"],       errors="coerce")
    ten_dt  = pd.to_datetime(work_df["tenure_start_date"],   errors="coerce")

    work_df["rec_to_sanc_days"]        = (sanc_dt - rec_dt).dt.days
    work_df["days_since_tenure_start"] = (rec_dt  - ten_dt).dt.days

    # ── 3. Derive log1p_sanction_amount ───────────────────────────────────
    work_df["log1p_sanction_amount"] = np.log1p(work_df["sanction_amount"])

    # ── 4. Drop rows where any feature is missing ─────────────────────────
    before_drop = len(work_df)
    work_df = work_df.dropna(subset=FEATURE_NAMES)
    excluded_missing = before_drop - len(work_df)
    if excluded_missing > 0:
        logger.info("[prepare_features] Excluded %d rows with NaN in features", excluded_missing)

    if len(work_df) == 0:
        raise ValueError(
            "No valid rows remain after filtering. "
            "Check that the DataFrame contains Works Sanctioned rows with "
            "sanction_amount > 0 and all date fields populated."
        )

    # ── 5. Extract feature matrix ─────────────────────────────────────────
    X = work_df[FEATURE_NAMES].values.astype(np.float64)

    # ── 6. Validate finite ────────────────────────────────────────────────
    if not np.isfinite(X).all():
        bad_cols = [FEATURE_NAMES[i] for i in range(X.shape[1]) if not np.isfinite(X[:, i]).all()]
        raise ValueError(
            f"Non-finite values detected in features after derivation: {bad_cols}. "
            "This indicates invalid date arithmetic or corrupted source data."
        )

    # ── 7. Build meta DataFrame ───────────────────────────────────────────
    meta_cols = [c for c in ["work_recommendation_dtl_id", "query_category",
                              "sanction_amount", "recommendation_date",
                              "sanction_date", "tenure_start_date",
                              "work_category", "state_name"]
                 if c in work_df.columns]
    meta = work_df[meta_cols].reset_index(drop=True)

    logger.info(
        "[prepare_features] Feature matrix ready: %d rows × %d features",
        X.shape[0], X.shape[1],
    )
    return X, meta


# ──────────────────────────────────────────────────────────────────────────────
# Model training
# ──────────────────────────────────────────────────────────────────────────────

def train_model(
    X: np.ndarray,
    contamination: Any = DEFAULT_CONTAMINATION,
    n_estimators: int = DEFAULT_N_ESTIMATORS,
    random_state: int = DEFAULT_RANDOM_STATE,
) -> IsolationForest:
    """Train an IsolationForest on the prepared feature matrix X.

    No StandardScaler is used — IsolationForest is tree-based and invariant
    to monotone transformations of features. log1p is already applied inside
    prepare_features().

    Parameters
    ----------
    X : np.ndarray  shape (n, 3)
        Finite feature matrix from prepare_features().
    contamination : float | 'auto'
        Expected fraction of anomalies. 'auto' lets sklearn choose.
    n_estimators : int
        Number of isolation trees.
    random_state : int
        Seed for reproducibility.

    Returns
    -------
    model : IsolationForest
        Fitted model ready for prediction.
    """
    if not np.isfinite(X).all():
        raise ValueError("X contains non-finite values. Call prepare_features() first.")
    if X.shape[1] != len(FEATURE_NAMES):
        raise ValueError(
            f"Expected {len(FEATURE_NAMES)} features, got {X.shape[1]}. "
            f"Feature order must be: {FEATURE_NAMES}"
        )

    model = IsolationForest(
        contamination=contamination,
        n_estimators=n_estimators,
        random_state=random_state,
        n_jobs=-1,
    )
    model.fit(X)
    logger.info(
        "[train_model] Trained IsolationForest: n_estimators=%d, contamination=%s, "
        "random_state=%d, n_samples=%d",
        n_estimators, contamination, random_state, X.shape[0],
    )
    return model


# ──────────────────────────────────────────────────────────────────────────────
# Model serialization
# ──────────────────────────────────────────────────────────────────────────────

def save_model(
    model: IsolationForest,
    path: str,
    feature_names: list[str] | None = None,
    metadata: dict | None = None,
) -> None:
    """Persist the trained model and feature contract to disk.

    The artifact is a dict containing the model and the exact feature names
    required for inference, so that any future loading code can verify
    feature compatibility.

    Parameters
    ----------
    model : IsolationForest
        Fitted Isolation Forest.
    path : str
        File path for the .pkl artifact (e.g. 'models/financial_isolation_forest.pkl').
    feature_names : list[str] | None
        Defaults to FEATURE_NAMES if not provided.
    metadata : dict | None
        Optional extra metadata to embed (checkpoint version, training date, etc.).
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)
    artifact = {
        "model": model,
        "feature_names": feature_names if feature_names is not None else FEATURE_NAMES,
        "metadata": metadata or {},
    }
    with open(path, "wb") as f:
        pickle.dump(artifact, f)
    logger.info("[save_model] Model artifact saved to %s", path)


def load_model(path: str) -> tuple[IsolationForest, list[str]]:
    """Load a saved model artifact.

    Returns
    -------
    model : IsolationForest
        Fitted model.
    feature_names : list[str]
        Exact feature names in the order the model expects.

    Raises
    ------
    FileNotFoundError
        If the model file does not exist.
    KeyError
        If the artifact format is invalid.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Model artifact not found at: {path}")
    with open(path, "rb") as f:
        artifact = pickle.load(f)
    model        = artifact["model"]
    feature_names = artifact["feature_names"]
    logger.info("[load_model] Loaded model from %s — features: %s", path, feature_names)
    return model, feature_names


# ──────────────────────────────────────────────────────────────────────────────
# Inference
# ──────────────────────────────────────────────────────────────────────────────

def predict_anomalies(model: IsolationForest, X: np.ndarray) -> np.ndarray:
    """Return IsolationForest predictions for each row.

    Returns
    -------
    predictions : np.ndarray[int]  shape (n,)
        -1 for model-detected anomalous records.
         1 for normal records.

    NOTE: A prediction of −1 means the record is anomalous relative to the
    training distribution. It does NOT confirm fraud or corruption.
    """
    return model.predict(X)


def anomaly_scores(model: IsolationForest, X: np.ndarray) -> np.ndarray:
    """Return the raw decision function scores for each row.

    Negative scores → more anomalous; positive → more normal.
    This is the unthresholded continuous score useful for ranking.

    Returns
    -------
    scores : np.ndarray[float]  shape (n,)
    """
    return model.decision_function(X)
