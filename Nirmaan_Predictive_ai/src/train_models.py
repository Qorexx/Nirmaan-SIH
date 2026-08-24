"""
Task 2: XGBoost Model Training Pipeline
=========================================
Trains two regression models on the synthetic MPLADS dataset:
  - Model A: Predicts actual_final_cost (to derive cost overrun)
  - Model B: Predicts actual_delay_days

Includes preprocessing (OrdinalEncoder for categoricals), evaluation
metrics (RMSE, MAE, R²), and model persistence via joblib.
"""

import os
import json
import numpy as np
import pandas as pd
import joblib
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OrdinalEncoder
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from xgboost import XGBRegressor


# ---------------------------------------------------------------------------
# Feature definitions
# ---------------------------------------------------------------------------

CATEGORICAL_FEATURES = [
    "state",
    "constituency_type",
    "project_category",
    "terrain_difficulty",
]

NUMERICAL_FEATURES = [
    "estimated_cost",
    "sanctioned_amount",
    "expected_duration_days",
    "elapsed_days",
    "progress_pct",
    "contractor_past_delays",
    "monsoon_overlap_days",
    "material_inflation_index",
    "labor_shortage_index",
    "sanction_year",
]

ALL_FEATURES = CATEGORICAL_FEATURES + NUMERICAL_FEATURES

COST_TARGET = "actual_final_cost"
DELAY_TARGET = "actual_delay_days"


def build_preprocessor() -> ColumnTransformer:
    """
    Build a ColumnTransformer that:
    - OrdinalEncodes categorical features (XGBoost handles encoded categoricals well)
    - Passes through numerical features as-is
    """
    return ColumnTransformer(
        transformers=[
            (
                "cat",
                OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1),
                CATEGORICAL_FEATURES,
            ),
            ("num", "passthrough", NUMERICAL_FEATURES),
        ],
        remainder="drop",
    )


def evaluate_model(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    model_name: str,
) -> dict:
    """Compute and print RMSE, MAE, R² for a model."""
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    mae = mean_absolute_error(y_true, y_pred)
    r2 = r2_score(y_true, y_pred)

    print(f"\n{'='*50}")
    print(f"  {model_name} — Evaluation Metrics")
    print(f"{'='*50}")
    print(f"  RMSE : {rmse:,.2f}")
    print(f"  MAE  : {mae:,.2f}")
    print(f"  R²   : {r2:.4f}")
    print(f"{'='*50}")

    return {"rmse": round(rmse, 2), "mae": round(mae, 2), "r2": round(r2, 4)}


def train_models(
    data_path: str = "data/synthetic_mplads_data.csv",
    model_dir: str = "models",
    test_size: float = 0.2,
    seed: int = 42,
) -> dict:
    """
    Full training pipeline: load data → preprocess → train → evaluate → save.

    Args:
        data_path: Path to the synthetic CSV dataset.
        model_dir: Directory to save trained models.
        test_size: Fraction held out for evaluation.
        seed: Random seed for reproducibility.

    Returns:
        Dictionary of metrics for both models.
    """
    # --- Load data ---
    print(f"[Task 2] Loading data from {data_path}...")
    df = pd.read_csv(data_path)
    print(f"         Loaded {len(df)} records with {len(df.columns)} columns.")

    X = df[ALL_FEATURES]
    y_cost = df[COST_TARGET]
    y_delay = df[DELAY_TARGET]

    # --- Train/test split ---
    X_train, X_test, y_cost_train, y_cost_test, y_delay_train, y_delay_test = (
        train_test_split(
            X, y_cost, y_delay, test_size=test_size, random_state=seed
        )
    )
    print(f"         Train: {len(X_train)} | Test: {len(X_test)}")

    # --- Preprocessing ---
    preprocessor = build_preprocessor()
    X_train_proc = preprocessor.fit_transform(X_train)
    X_test_proc = preprocessor.transform(X_test)

    # --- Model A: Cost Prediction ---
    print("\n[Task 2] Training Model A (Cost Prediction)...")
    cost_model = XGBRegressor(
        n_estimators=300,
        max_depth=6,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        reg_alpha=0.1,
        reg_lambda=1.0,
        random_state=seed,
        n_jobs=-1,
        verbosity=0,
    )
    cost_model.fit(X_train_proc, y_cost_train)
    y_cost_pred = cost_model.predict(X_test_proc)
    cost_metrics = evaluate_model(y_cost_test, y_cost_pred, "Model A — Cost Prediction")

    # --- Model B: Delay Prediction ---
    print("\n[Task 2] Training Model B (Delay Prediction)...")
    delay_model = XGBRegressor(
        n_estimators=300,
        max_depth=6,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        reg_alpha=0.1,
        reg_lambda=1.0,
        random_state=seed,
        n_jobs=-1,
        verbosity=0,
    )
    delay_model.fit(X_train_proc, y_delay_train)
    y_delay_pred = delay_model.predict(X_test_proc)
    delay_metrics = evaluate_model(y_delay_test, y_delay_pred, "Model B — Delay Prediction")

    # --- Save models and preprocessor ---
    model_path = Path(model_dir)
    model_path.mkdir(parents=True, exist_ok=True)

    joblib.dump(cost_model, model_path / "cost_model.joblib")
    joblib.dump(delay_model, model_path / "delay_model.joblib")
    joblib.dump(preprocessor, model_path / "preprocessor.joblib")

    # Save feature names for SHAP
    feature_names = (
        CATEGORICAL_FEATURES + NUMERICAL_FEATURES
    )
    joblib.dump(feature_names, model_path / "feature_names.joblib")

    print(f"\n[Task 2] ✅ Models saved to {model_path}/")
    print(f"         - cost_model.joblib")
    print(f"         - delay_model.joblib")
    print(f"         - preprocessor.joblib")
    print(f"         - feature_names.joblib")

    return {
        "cost_model_metrics": cost_metrics,
        "delay_model_metrics": delay_metrics,
    }


if __name__ == "__main__":
    metrics = train_models()
    print(f"\nAll metrics: {json.dumps(metrics, indent=2)}")
