"""
Checkpoint 7A — Model Evaluation & Threshold Tuning Script (SIH26102 / Person 1)

Loads the official dataset and saved model, calculates anomaly score distribution,
evaluates candidate threshold percentiles (1%, 2%, 3%, 5%, 8%, 10%), analyzes feature
behavior, and generates docs/top_100_model_anomalies.csv.

Usage:
    python3 scripts/evaluate_thresholds.py
"""

import os
import sys
import numpy as np
import pandas as pd

# Ensure project root is on sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from ml_modules.financial.anomaly_model import (
    FEATURE_NAMES,
    load_model,
    prepare_features,
    anomaly_scores,
    predict_anomalies,
)


def main():
    csv_path = os.path.join(PROJECT_ROOT, "data", "mplads_projects.csv")
    if not os.path.exists(csv_path):
        csv_path = "/home/shaurya-dev01/Downloads/mplads_projects.csv"
    if not os.path.exists(csv_path):
        print("ERROR: Cannot locate mplads_projects.csv")
        sys.exit(1)

    model_path = os.path.join(PROJECT_ROOT, "models", "financial_isolation_forest.pkl")
    if not os.path.exists(model_path):
        print(f"ERROR: Cannot locate model artifact at {model_path}")
        sys.exit(1)

    print(f"\n{'='*70}")
    print("  CHECKPOINT 7A — ISOLATION FOREST THRESHOLD EVALUATION & TUNING")
    print(f"{'='*70}")
    print(f"Source CSV   : {csv_path}")
    print(f"Model Path   : {model_path}")

    # 1. Load Dataset
    print("\n[1/6] Loading dataset and model...")
    df = pd.read_csv(csv_path, low_memory=False)
    model, feature_names = load_model(model_path)

    # 2. Prepare Features
    X, meta = prepare_features(df, lifecycle_filter=True)
    n_records = X.shape[0]
    print(f"      Training population size: {n_records:,} rows")
    print(f"      Features matched: {feature_names}")

    # 3. Calculate Anomaly Scores & Baseline Predictions
    scores = anomaly_scores(model, X)
    preds_auto = predict_anomalies(model, X)
    n_auto_anomalies = (preds_auto == -1).sum()
    pct_auto = (n_auto_anomalies / n_records) * 100

    # Task 1: Score Distribution Statistics
    print("\n[2/6] Task 1 — Score Distribution Statistics")
    score_min = np.min(scores)
    score_max = np.max(scores)
    score_mean = np.mean(scores)
    score_median = np.median(scores)
    score_std = np.std(scores)

    percentiles_keys = [1, 5, 10, 25, 75, 90, 95, 99]
    percentiles_vals = {p: np.percentile(scores, p) for p in percentiles_keys}

    print(f"      Min      : {score_min:.6f}")
    print(f"      Max      : {score_max:.6f}")
    print(f"      Mean     : {score_mean:.6f}")
    print(f"      Median   : {score_median:.6f}")
    print(f"      Std Dev  : {score_std:.6f}")
    print("      Percentiles:")
    for p in percentiles_keys:
        print(f"        P{p:02d}    : {percentiles_vals[p]:.6f}")
    
    print(f"\n      Baseline contamination='auto':")
    print(f"        Anomaly Count : {n_auto_anomalies:,}")
    print(f"        Percentage    : {pct_auto:.2f}%")

    # Task 2: Threshold Experiments
    print("\n[3/6] Task 2 — Threshold Experiments")
    candidate_pcts = [1.0, 2.0, 3.0, 5.0, 8.0, 10.0]
    thresh_table = []

    for pct in candidate_pcts:
        cutoff = np.percentile(scores, pct)
        count = int((scores <= cutoff).sum())
        real_pct = (count / n_records) * 100
        thresh_table.append({
            "Target Rate": f"{pct:.0f}%",
            "Score Cutoff": cutoff,
            "Anomaly Count": count,
            "Actual Percentage": real_pct
        })

    print(f"      {'Target':<10} | {'Score Cutoff':<14} | {'Anomaly Count':<14} | {'Actual Pct':<10}")
    print(f"      {'-'*55}")
    for row in thresh_table:
        print(f"      {row['Target Rate']:<10} | {row['Score Cutoff']:<14.6f} | {row['Anomaly Count']:<14,} | {row['Actual Percentage']:<9.2f}%")

    # Build full working DataFrame for top anomaly extraction and feature analysis
    df_ws = df[df["query_category"] == "Works Sanctioned"].copy()
    df_ws = df_ws[df_ws["sanction_amount"] > 0]
    
    rec_dt  = pd.to_datetime(df_ws["recommendation_date"], errors="coerce")
    sanc_dt = pd.to_datetime(df_ws["sanction_date"],       errors="coerce")
    ten_dt  = pd.to_datetime(df_ws["tenure_start_date"],   errors="coerce")

    df_ws["rec_to_sanc_days"]        = (sanc_dt - rec_dt).dt.days
    df_ws["days_since_tenure_start"] = (rec_dt  - ten_dt).dt.days
    df_ws["log1p_sanction_amount"] = np.log1p(df_ws["sanction_amount"])
    df_ws = df_ws.dropna(subset=FEATURE_NAMES).copy()
    df_ws["anomaly_score"] = scores

    # Sort ascending by anomaly_score (most anomalous first)
    df_ws_sorted = df_ws.sort_values(by="anomaly_score", ascending=True).reset_index(drop=True)

    # Task 3: Extract Top 100 Anomalies for Recommended Threshold
    # We will pick the recommended threshold cutoff and export the top 100 anomalies.
    print("\n[4/6] Task 3 — Extracting Top 100 Anomalies...")
    req_cols = [
        "work_recommendation_dtl_id",
        "constituency",
        "work_category",
        "sanction_amount",
        "recommendation_date",
        "sanction_date",
        "rec_to_sanc_days",
        "tenure_start_date",
        "days_since_tenure_start",
        "anomaly_score"
    ]
    
    top_100 = df_ws_sorted.head(100)[req_cols].copy()
    csv_out_path = os.path.join(PROJECT_ROOT, "docs", "top_100_model_anomalies.csv")
    os.makedirs(os.path.dirname(csv_out_path), exist_ok=True)
    top_100.to_csv(csv_out_path, index=False)
    print(f"      Saved top 100 anomalies to {csv_out_path}")

    # Task 4: Feature Behavior Analysis
    print("\n[5/6] Task 4 — Feature Behavior Analysis")
    top_100_full = df_ws_sorted.head(100)
    top_1pct = df_ws_sorted.head(int(n_records * 0.01))
    top_2pct = df_ws_sorted.head(int(n_records * 0.02))
    top_3pct = df_ws_sorted.head(int(n_records * 0.03))
    top_5pct = df_ws_sorted.head(int(n_records * 0.05))

    print("\n      Comparing Population vs Candidate Top Anomalies:")
    def summarize_subset(name, sub):
        print(f"\n      --- {name} (N={len(sub):,}) ---")
        print(f"      Sanction Amount (₹): Mean=₹{sub['sanction_amount'].mean():,.2f}, Median=₹{sub['sanction_amount'].median():,.2f}, Min=₹{sub['sanction_amount'].min():,.2f}, Max=₹{sub['sanction_amount'].max():,.2f}")
        print(f"      Rec to Sanc Days   : Mean={sub['rec_to_sanc_days'].mean():.1f}, Median={sub['rec_to_sanc_days'].median():.1f}, Min={sub['rec_to_sanc_days'].min():.0f}, Max={sub['rec_to_sanc_days'].max():.0f}")
        print(f"      Days Since Tenure  : Mean={sub['days_since_tenure_start'].mean():.1f}, Median={sub['days_since_tenure_start'].median():.1f}, Min={sub['days_since_tenure_start'].min():.0f}, Max={sub['days_since_tenure_start'].max():.0f}")

    summarize_subset("Full Population", df_ws)
    summarize_subset("Top 100 Anomalies", top_100_full)
    summarize_subset("Top 1% Anomalies", top_1pct)
    summarize_subset("Top 2% Anomalies", top_2pct)
    summarize_subset("Top 3% Anomalies", top_3pct)
    summarize_subset("Top 5% Anomalies", top_5pct)

    print("\n[6/6] Checkpoint 7A Evaluation Complete!")

if __name__ == "__main__":
    main()
