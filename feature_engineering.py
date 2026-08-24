"""
feature_engineering.py
Generates derived features from the cleaned MPLADS dataset for analytics
and downstream ML tasks. Reads mplads_projects.csv and outputs
mplads_features.csv with enriched columns.
"""

import numpy as np
import pandas as pd

INPUT_CSV = "mplads_projects.csv"
OUTPUT_CSV = "mplads_features.csv"


def load_data(path: str) -> pd.DataFrame:
    """Load and parse the raw MPLADS CSV with correct dtypes."""
    print(f"[*] Loading {path}...")
    df = pd.read_csv(path)

    # Parse date columns
    date_cols = [
        "recommendation_date",
        "sanction_date",
        "tenure_start_date",
        "tenure_end_date",
        "actual_end_date",
    ]
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    # Ensure numeric columns
    numeric_cols = ["sanction_amount", "actual_amount", "total_amt", "recommended_amount"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

    print(f"    Loaded {len(df)} records with {len(df.columns)} columns.")
    return df


# ── Time-based features ─────────────────────────────────────────────

def add_time_features(df: pd.DataFrame) -> pd.DataFrame:
    """Derive time-gap and duration features from date columns."""
    print("[*] Engineering time-based features...")

    # Days from recommendation to sanction (approval lag)
    if {"recommendation_date", "sanction_date"}.issubset(df.columns):
        df["days_to_sanction"] = (
            df["sanction_date"] - df["recommendation_date"]
        ).dt.days

    # Days from sanction to actual completion
    if {"sanction_date", "actual_end_date"}.issubset(df.columns):
        df["days_to_completion"] = (
            df["actual_end_date"] - df["sanction_date"]
        ).dt.days

    # Total project lifecycle (recommendation → completion)
    if {"recommendation_date", "actual_end_date"}.issubset(df.columns):
        df["project_lifecycle_days"] = (
            df["actual_end_date"] - df["recommendation_date"]
        ).dt.days

    # MP tenure duration in days
    if {"tenure_start_date", "tenure_end_date"}.issubset(df.columns):
        df["tenure_duration_days"] = (
            df["tenure_end_date"] - df["tenure_start_date"]
        ).dt.days

    # Year and month of recommendation (for seasonal analysis)
    if "recommendation_date" in df.columns:
        df["recommendation_year"] = df["recommendation_date"].dt.year
        df["recommendation_month"] = df["recommendation_date"].dt.month

    return df


# ── Financial features ───────────────────────────────────────────────

def add_financial_features(df: pd.DataFrame) -> pd.DataFrame:
    """Derive spending efficiency and budget utilization features."""
    print("[*] Engineering financial features...")

    # Fund utilization ratio (actual / sanctioned)
    if {"actual_amount", "sanction_amount"}.issubset(df.columns):
        df["utilization_ratio"] = np.where(
            df["sanction_amount"] > 0,
            df["actual_amount"] / df["sanction_amount"],
            0.0,
        )

    # Cost overrun flag (actual exceeds sanctioned by > 10%)
    if "utilization_ratio" in df.columns:
        df["is_cost_overrun"] = (df["utilization_ratio"] > 1.10).astype(int)

    # Under-utilization flag (less than 50% of sanctioned amount used)
    if "utilization_ratio" in df.columns:
        df["is_underutilized"] = (
            (df["utilization_ratio"] < 0.50) & (df["utilization_ratio"] > 0)
        ).astype(int)

    # Sanction amount bucket (categorical binning)
    if "sanction_amount" in df.columns:
        bins = [0, 1e5, 5e5, 10e5, 50e5, 100e5, np.inf]
        labels = ["<1L", "1-5L", "5-10L", "10-50L", "50L-1Cr", ">1Cr"]
        df["amount_bucket"] = pd.cut(
            df["sanction_amount"], bins=bins, labels=labels, right=False
        )

    return df


# ── Work stage features ──────────────────────────────────────────────

def add_stage_features(df: pd.DataFrame) -> pd.DataFrame:
    """Encode work stage and query category as numeric features."""
    print("[*] Engineering stage/status features...")

    # Encode work_stage as ordinal
    if "work_stage" in df.columns:
        stage_order = {
            "Recommended": 1,
            "Sanctioned": 2,
            "In Progress": 3,
            "Completed": 4,
        }
        df["work_stage_code"] = (
            df["work_stage"].str.strip().map(stage_order).fillna(0).astype(int)
        )

    # Binary flag: is the project completed?
    if "query_category" in df.columns:
        df["is_completed"] = (
            df["query_category"].str.lower().str.contains("completed", na=False)
        ).astype(int)

    return df


# ── Aggregation features ────────────────────────────────────────────

def add_aggregation_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add MP-level and state-level aggregate statistics."""
    print("[*] Engineering aggregation features...")

    # Per-MP statistics
    if "mp_name" in df.columns and "sanction_amount" in df.columns:
        mp_stats = df.groupby("mp_name")["sanction_amount"].agg(
            mp_total_sanctioned="sum",
            mp_avg_sanctioned="mean",
            mp_project_count="count",
        )
        df = df.merge(mp_stats, on="mp_name", how="left")

    # Per-state statistics
    if "state_name" in df.columns and "sanction_amount" in df.columns:
        state_stats = df.groupby("state_name")["sanction_amount"].agg(
            state_total_sanctioned="sum",
            state_avg_sanctioned="mean",
            state_project_count="count",
        )
        df = df.merge(state_stats, on="state_name", how="left")

    # Per-constituency statistics
    if "constituency" in df.columns and "sanction_amount" in df.columns:
        const_stats = df.groupby("constituency")["sanction_amount"].agg(
            constituency_total_sanctioned="sum",
            constituency_project_count="count",
        )
        df = df.merge(const_stats, on="constituency", how="left")

    return df


# ── Text features ────────────────────────────────────────────────────

def add_text_features(df: pd.DataFrame) -> pd.DataFrame:
    """Extract simple text-based features from description fields."""
    print("[*] Engineering text features...")

    if "work_description" in df.columns:
        df["description_length"] = (
            df["work_description"].fillna("").str.len()
        )
        df["description_word_count"] = (
            df["work_description"].fillna("").str.split().str.len().fillna(0).astype(int)
        )

    if "activity_name" in df.columns:
        df["activity_name_length"] = (
            df["activity_name"].fillna("").str.len()
        )

    return df


# ── Main pipeline ────────────────────────────────────────────────────

def main():
    df = load_data(INPUT_CSV)

    df = add_time_features(df)
    df = add_financial_features(df)
    df = add_stage_features(df)
    df = add_aggregation_features(df)
    df = add_text_features(df)

    # Summary of new features
    original_cols = pd.read_csv(INPUT_CSV, nrows=0).columns.tolist()
    new_cols = [c for c in df.columns if c not in original_cols]
    print(f"\n[+] Added {len(new_cols)} new features:")
    for col in new_cols:
        non_null = df[col].notna().sum()
        print(f"    * {col:35s} ({non_null:,} non-null values)")

    df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8")
    print(f"\n[done] Feature-engineered dataset saved to '{OUTPUT_CSV}' ({len(df)} rows, {len(df.columns)} columns)")


if __name__ == "__main__":
    main()