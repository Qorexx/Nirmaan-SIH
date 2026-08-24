"""
Checkpoint 6 — Isolation Forest Training Script (SIH26102 / Person 1)

Loads data/mplads_projects.csv, prepares features, trains the Isolation Forest,
inspects the prediction distribution, and saves the model artifact.

Usage:
    python3 scripts/train_isolation_forest.py

Do NOT modify the source CSV.
Do NOT modify backend files.
"""

import logging
import os
import sys
from datetime import datetime

import numpy as np
import pandas as pd

# Ensure project root is on sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from ml_modules.financial.anomaly_model import (
    FEATURE_NAMES,
    DEFAULT_CONTAMINATION,
    DEFAULT_N_ESTIMATORS,
    DEFAULT_RANDOM_STATE,
    anomaly_scores,
    predict_anomalies,
    prepare_features,
    save_model,
    train_model,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def main():
    # ── 1. Locate CSV ──────────────────────────────────────────────────────
    csv_path = os.path.join(PROJECT_ROOT, "data", "mplads_projects.csv")
    if not os.path.exists(csv_path):
        csv_path = "/home/shaurya-dev01/Downloads/mplads_projects.csv"
    if not os.path.exists(csv_path):
        print("ERROR: Cannot locate mplads_projects.csv")
        sys.exit(1)

    print(f"\n{'='*60}")
    print("  CHECKPOINT 6 — ISOLATION FOREST TRAINING")
    print(f"{'='*60}")
    print(f"Source CSV : {csv_path}")

    # ── 2. Load once ───────────────────────────────────────────────────────
    print("\n[1/6] Loading dataset...")
    df = pd.read_csv(csv_path, low_memory=False)
    print(f"      Full dataset shape: {df.shape[0]:,} rows × {df.shape[1]} columns")

    ws_count = (df["query_category"] == "Works Sanctioned").sum()
    ws_nonzero = ((df["query_category"] == "Works Sanctioned") & (df["sanction_amount"] > 0)).sum()
    print(f"      Works Sanctioned rows total      : {ws_count:,}")
    print(f"      Works Sanctioned, sanction > 0   : {ws_nonzero:,}")

    # ── 3. Prepare features ────────────────────────────────────────────────
    print("\n[2/6] Preparing features...")
    X, meta = prepare_features(df, lifecycle_filter=True)
    n_train = X.shape[0]
    print(f"      Training rows (after all filters): {n_train:,}")
    print(f"      Feature vector: {FEATURE_NAMES}")
    print(f"      Feature matrix shape: {X.shape}")

    # Feature distribution report
    print("\n      Feature distributions:")
    for i, feat in enumerate(FEATURE_NAMES):
        col = X[:, i]
        q1, q3 = np.percentile(col, 25), np.percentile(col, 75)
        print(
            f"      [{feat}]  "
            f"min={col.min():.3f}  p25={q1:.3f}  median={np.median(col):.3f}  "
            f"p75={q3:.3f}  max={col.max():.3f}  "
            f"skew={pd.Series(col).skew():.3f}"
        )

    # Verify finite
    assert np.isfinite(X).all(), "FATAL: non-finite values detected in feature matrix"
    print("\n      ✓ All feature values are finite")

    # ── 4. Train model ─────────────────────────────────────────────────────
    print("\n[3/6] Training Isolation Forest...")
    print(f"      contamination = {DEFAULT_CONTAMINATION}")
    print(f"      n_estimators  = {DEFAULT_N_ESTIMATORS}")
    print(f"      random_state  = {DEFAULT_RANDOM_STATE}")

    model = train_model(
        X,
        contamination=DEFAULT_CONTAMINATION,
        n_estimators=DEFAULT_N_ESTIMATORS,
        random_state=DEFAULT_RANDOM_STATE,
    )
    print("      ✓ Training complete")

    # ── 5. Inspect prediction distribution ────────────────────────────────
    print("\n[4/6] Inspecting prediction distribution...")
    preds  = predict_anomalies(model, X)
    scores = anomaly_scores(model, X)

    n_anomaly  = int((preds == -1).sum())
    n_normal   = int((preds ==  1).sum())
    pct_anomaly = n_anomaly / n_train * 100

    print(f"      Predictions: 1 (normal) = {n_normal:,}  |  -1 (anomalous) = {n_anomaly:,}")
    print(f"      Model-detected anomalous records: {n_anomaly:,} / {n_train:,} = {pct_anomaly:.2f}%")

    print(f"\n      Decision function score distribution:")
    score_series = pd.Series(scores)
    print(
        f"      min={score_series.min():.4f}  "
        f"p5={score_series.quantile(0.05):.4f}  "
        f"median={score_series.median():.4f}  "
        f"p95={score_series.quantile(0.95):.4f}  "
        f"max={score_series.max():.4f}"
    )
    print("      NOTE: Negative scores → more anomalous; positive → more normal.")
    print("      NOTE: A -1 prediction does NOT confirm fraud or corruption.")

    # ── 6. Save model ──────────────────────────────────────────────────────
    model_path = os.path.join(PROJECT_ROOT, "models", "financial_isolation_forest.pkl")
    print(f"\n[5/6] Saving model artifact to {model_path}...")

    metadata = {
        "checkpoint": "Checkpoint 6",
        "trained_at": datetime.utcnow().isoformat() + "Z",
        "training_rows": n_train,
        "training_population": "Works Sanctioned, sanction_amount > 0, rec_to_sanc_days not null",
        "contamination": str(DEFAULT_CONTAMINATION),
        "n_estimators": DEFAULT_N_ESTIMATORS,
        "random_state": DEFAULT_RANDOM_STATE,
        "n_anomalies_detected": n_anomaly,
        "pct_anomalies_detected": round(pct_anomaly, 4),
    }
    save_model(model, model_path, feature_names=FEATURE_NAMES, metadata=metadata)
    print(f"      ✓ Model saved")

    # ── 7. Summary ─────────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print("  TRAINING SUMMARY")
    print(f"{'='*60}")
    print(f"  Training rows              : {n_train:,}")
    print(f"  Features                   : {FEATURE_NAMES}")
    print(f"  contamination              : {DEFAULT_CONTAMINATION}")
    print(f"  n_estimators               : {DEFAULT_N_ESTIMATORS}")
    print(f"  random_state               : {DEFAULT_RANDOM_STATE}")
    print(f"  Model-detected anomalies   : {n_anomaly:,}  ({pct_anomaly:.2f}%)")
    print(f"  Model path                 : {model_path}")
    print(f"{'='*60}")
    print("\n[6/6] Checkpoint 6 complete. Stopping — model training done.\n")


if __name__ == "__main__":
    main()
