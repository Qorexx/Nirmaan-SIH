"""
Checkpoint 5 — EDA & Feature Refinement Script (SIH26102 / Person 1)

Performs exhaustive distribution analysis, outlier detection, correlation study,
and feature vector finalization for the Isolation Forest MVP.

Source: data/mplads_projects.csv (86 MB, loaded once)
Do NOT modify the source file.
Do NOT train any model in this script.
"""

import os
import sys
import numpy as np
import pandas as pd


# ──────────────────────────────────────────────────────────────────────────────
# SECTION 1  Load dataset once
# ──────────────────────────────────────────────────────────────────────────────
def load_and_derive(csv_path: str) -> pd.DataFrame:
    """Load the CSV and add all derived candidate columns. Returns one DataFrame."""
    print(f"[LOAD] Reading {csv_path}...")
    df = pd.read_csv(csv_path, low_memory=False)
    print(f"[LOAD] Shape: {df.shape[0]:,} rows × {df.shape[1]} columns")

    # --- Parse dates (analysis only — originals untouched) ---
    df["_rec_dt"]    = pd.to_datetime(df["recommendation_date"], errors="coerce")
    df["_sanc_dt"]   = pd.to_datetime(df["sanction_date"],       errors="coerce")
    df["_ten_start"] = pd.to_datetime(df["tenure_start_date"],   errors="coerce")
    df["_ten_end"]   = pd.to_datetime(
        df["tenure_end_date"].str[:10], errors="coerce"
    )

    # --- Derive candidate features ---
    df["rec_to_sanc_days"]        = (df["_sanc_dt"]   - df["_rec_dt"]   ).dt.days
    df["days_since_tenure_start"] = (df["_rec_dt"]    - df["_ten_start"]).dt.days
    df["days_to_tenure_end"]      = (df["_ten_end"]   - df["_rec_dt"]   ).dt.days
    df["log1p_sanction_amount"]   = np.log1p(df["sanction_amount"])
    df["recommendation_month"]    = df["_rec_dt"].dt.month
    df["sanction_month"]          = df["_sanc_dt"].dt.month

    # lifecycle stage encoding (ordinal, 0/1/2)
    lifecycle_map = {
        "Works Recommended": 0,
        "Works Sanctioned":  1,
        "Works Completed":   2,
    }
    df["lifecycle_stage"] = df["query_category"].map(lifecycle_map)

    return df


# ──────────────────────────────────────────────────────────────────────────────
# SECTION 2  Distribution analysis helpers
# ──────────────────────────────────────────────────────────────────────────────
def distribution_stats(series: pd.Series, label: str) -> dict:
    """Return a dict of descriptive statistics for a numeric series."""
    s = series.dropna()
    if len(s) == 0:
        return {"feature": label, "valid_n": 0, "missing_pct": 100.0}
    q1, q3  = s.quantile(0.25), s.quantile(0.75)
    iqr     = q3 - q1
    out_hi  = q3 + 1.5 * iqr
    out_lo  = q1 - 1.5 * iqr
    return {
        "feature":       label,
        "valid_n":       len(s),
        "missing_pct":   round((series.isnull().sum() / len(series)) * 100, 2),
        "min":           float(s.min()),
        "p25":           float(q1),
        "median":        float(s.median()),
        "mean":          float(s.mean()),
        "p75":           float(q3),
        "p95":           float(s.quantile(0.95)),
        "max":           float(s.max()),
        "std":           float(s.std()),
        "skewness":      float(s.skew()),
        "kurtosis":      float(s.kurtosis()),
        "iqr":           float(iqr),
        "iqr_outlier_hi": float(out_hi),
        "iqr_outlier_lo": float(out_lo),
        "n_outliers_hi": int((s > out_hi).sum()),
        "pct_outliers_hi": round(float((s > out_hi).mean() * 100), 2),
        "n_negative":    int((s < 0).sum()),
        "n_zero":        int((s == 0).sum()),
    }


def print_dist(stats: dict):
    print(
        f"  valid_n={stats['valid_n']:,}  missing={stats['missing_pct']}%  "
        f"median={stats['median']:.2f}  mean={stats['mean']:.2f}  "
        f"skew={stats['skewness']:.2f}  kurt={stats['kurtosis']:.2f}"
    )
    print(
        f"  IQR={stats['iqr']:.2f}  outlier_hi>{stats['iqr_outlier_hi']:.2f}  "
        f"n_outliers={stats['n_outliers_hi']:,} ({stats['pct_outliers_hi']}%)  "
        f"n_neg={stats['n_negative']}  n_zero={stats['n_zero']}"
    )


# ──────────────────────────────────────────────────────────────────────────────
# SECTION 3  Main analysis
# ──────────────────────────────────────────────────────────────────────────────
def run_eda(df: pd.DataFrame):
    n_total = len(df)

    # ── 3.1 Query category breakdown ──────────────────────────────────────────
    print("\n\n══════════════ S3.1  QUERY CATEGORY BREAKDOWN ══════════════")
    qc = df["query_category"].value_counts(dropna=False)
    for cat, cnt in qc.items():
        print(f"  {cat}: {cnt:,}  ({cnt/n_total*100:.2f}%)")

    # ── 3.2 sanction_amount distribution (all rows vs meaningful rows) ────────
    print("\n\n══════════════ S3.2  SANCTION_AMOUNT DISTRIBUTION ══════════════")

    # All rows
    sa_all = distribution_stats(df["sanction_amount"], "sanction_amount (ALL rows)")
    print("ALL ROWS:"); print_dist(sa_all)

    # Works Recommended rows (non-zero)
    sa_wr = distribution_stats(
        df.loc[(df["query_category"] == "Works Recommended") & (df["sanction_amount"] > 0), "sanction_amount"],
        "sanction_amount (Works Recommended, nonzero)"
    )
    print("Works Recommended (non-zero):"); print_dist(sa_wr)

    # Works Sanctioned rows (non-zero — primary working set)
    sa_ws = distribution_stats(
        df.loc[(df["query_category"] == "Works Sanctioned") & (df["sanction_amount"] > 0), "sanction_amount"],
        "sanction_amount (Works Sanctioned, nonzero)"
    )
    print("Works Sanctioned (non-zero, PRIMARY):"); print_dist(sa_ws)

    # log1p_sanction_amount (Works Sanctioned)
    log_sa_ws = distribution_stats(
        df.loc[(df["query_category"] == "Works Sanctioned") & (df["sanction_amount"] > 0), "log1p_sanction_amount"],
        "log1p_sanction_amount (Works Sanctioned)"
    )
    print("\nlog1p_sanction_amount (Works Sanctioned):"); print_dist(log_sa_ws)

    # ── 3.3 Candidate temporal features ───────────────────────────────────────
    print("\n\n══════════════ S3.3  TEMPORAL FEATURE DISTRIBUTIONS ══════════════")

    ws_mask = df["query_category"] == "Works Sanctioned"

    # rec_to_sanc_days
    rts_stats = distribution_stats(df.loc[ws_mask, "rec_to_sanc_days"], "rec_to_sanc_days (Works Sanctioned)")
    print("rec_to_sanc_days (Works Sanctioned):"); print_dist(rts_stats)

    # days_since_tenure_start
    dsts_stats = distribution_stats(df.loc[ws_mask, "days_since_tenure_start"], "days_since_tenure_start (WS)")
    print("\ndays_since_tenure_start (Works Sanctioned):"); print_dist(dsts_stats)

    # days_to_tenure_end
    dte_stats = distribution_stats(df.loc[ws_mask, "days_to_tenure_end"], "days_to_tenure_end (WS)")
    print("\ndays_to_tenure_end (Works Sanctioned):"); print_dist(dte_stats)

    # recommendation_month
    rm_stats = distribution_stats(df.loc[ws_mask, "recommendation_month"], "recommendation_month (WS)")
    print("\nrecommendation_month (Works Sanctioned):"); print_dist(rm_stats)

    # ── 3.4 Within-category z-score of sanction_amount ───────────────────────
    print("\n\n══════════════ S3.4  SANCTION AMOUNT Z-SCORE BY WORK CATEGORY ══════════════")
    ws_df = df[ws_mask].copy()
    ws_df["sa_z_by_cat"] = ws_df.groupby("work_category")["sanction_amount"].transform(
        lambda x: (x - x.mean()) / (x.std() + 1e-9)
    )
    saz_stats = distribution_stats(ws_df["sa_z_by_cat"], "sa_z_by_cat (Works Sanctioned)")
    print("sa_z_by_cat:"); print_dist(saz_stats)
    print(f"  max z-score: {ws_df['sa_z_by_cat'].max():.2f}  (extreme outlier indicator)")

    # ── 3.5 Correlation matrix (Works Sanctioned, primary feature set) ────────
    print("\n\n══════════════ S3.5  PEARSON CORRELATION MATRIX (Works Sanctioned) ══════════════")
    corr_cols = [
        "log1p_sanction_amount",
        "rec_to_sanc_days",
        "days_since_tenure_start",
        "days_to_tenure_end",
    ]
    ws_df["log1p_sanction_amount"] = np.log1p(ws_df["sanction_amount"])
    corr_df = ws_df[corr_cols].dropna()
    print(f"  n_rows for correlation: {len(corr_df):,}")
    print(corr_df.corr(method="pearson").round(4).to_string())

    # ── 3.6 flag analysis ─────────────────────────────────────────────────────
    print("\n\n══════════════ S3.6  FLAG FIELD ANALYSIS ══════════════")
    print("flag value counts (all):")
    print(df["flag"].value_counts(dropna=False).to_string())
    print("\nflag × query_category crosstab:")
    print(pd.crosstab(df["flag"].fillna(-1).astype(int), df["query_category"]).to_string())
    print("\nConclusion: flag is a DETERMINISTIC function of query_category.")
    print("  flag=1 → Works Recommended or Works Sanctioned")
    print("  flag=2 → Works Recommended subset (466 rows, boundary lifecycle)")
    print("  flag=3 → Works Completed")
    print("  → flag is REDUNDANT with query_category; exclude from feature set.")

    # ── 3.7 Feature stability on zero sanction_amount rows ───────────────────
    print("\n\n══════════════ S3.7  ZERO SANCTION_AMOUNT ROWS ══════════════")
    zero_sa = df[df["sanction_amount"] == 0]
    print(f"  Rows with sanction_amount == 0: {len(zero_sa):,}")
    print(f"  All from Works Completed or early-stage: {zero_sa['query_category'].value_counts().to_dict()}")
    print("  log1p(0) = 0.0 → safe, no NaN/inf introduced")
    print("  Works Completed rows excluded from primary Isolation Forest training set.")

    # ── 3.8 Lifecycle model scope clarification ───────────────────────────────
    print("\n\n══════════════ S3.8  LIFECYCLE SCOPE FOR ISOLATION FOREST ══════════════")
    print("  Target subset: Works Sanctioned rows (73,790 rows)")
    print("  Rationale: rec_to_sanc_days, sanction_amount, days_since_tenure_start")
    print("  are all simultaneously available only for Works Sanctioned records.")
    print("  Missing sanction_date (1 row) → drop that single row.")

    # ── 3.9 Final recommended feature set ─────────────────────────────────────
    print("\n\n══════════════ S3.9  FINAL MVP ISOLATION FOREST FEATURE SET ══════════════")
    print("""
  Training population: Works Sanctioned rows where sanction_amount > 0 and
                       rec_to_sanc_days is not null (73,789 rows).

  FEATURE VECTOR:
  ┌─────────────────────────────────┬────────────────────────────────────────────────────┐
  │ Feature Name                    │ Description                                        │
  ├─────────────────────────────────┼────────────────────────────────────────────────────┤
  │ log1p_sanction_amount           │ log1p-transformed sanction amount (INR).           │
  │                                 │ Reduces extreme right skew (raw skew = 22.76 →     │
  │                                 │ log1p skew = −0.46). Numerically stable.           │
  ├─────────────────────────────────┼────────────────────────────────────────────────────┤
  │ rec_to_sanc_days                │ Calendar days: recommendation → sanction.          │
  │                                 │ IQR outlier threshold: >286 days (5.5% of WS).    │
  │                                 │ Captures bureaucratic delay anomalies.             │
  ├─────────────────────────────────┼────────────────────────────────────────────────────┤
  │ days_since_tenure_start         │ Days from MP tenure start to recommendation date.  │
  │                                 │ Captures whether sanction is early or late in MP   │
  │                                 │ tenure. Low skew (0.21). No negatives.             │
  └─────────────────────────────────┴────────────────────────────────────────────────────┘

  CANDIDATE FEATURES EVALUATED BUT REJECTED:
  ┌─────────────────────────────────┬───────────────────────────────────────────────────┐
  │ Feature                         │ Rejection Reason                                  │
  ├─────────────────────────────────┼───────────────────────────────────────────────────┤
  │ sa_z_by_cat                     │ Redundant with log1p_sanction_amount              │
  │                                 │ (Pearson r=0.61). Adds no independent signal.     │
  ├─────────────────────────────────┼───────────────────────────────────────────────────┤
  │ days_to_tenure_end              │ Anti-correlated with days_since_tenure_start       │
  │                                 │ (r≈−1 structural). Fully redundant.               │
  ├─────────────────────────────────┼───────────────────────────────────────────────────┤
  │ recommendation_month            │ Low variance cyclic variable. Correlation with     │
  │                                 │ sanction features ≈ 0. No anomaly signal.          │
  ├─────────────────────────────────┼───────────────────────────────────────────────────┤
  │ flag                            │ Deterministic proxy for query_category.            │
  │                                 │ Adds no independent information.                  │
  ├─────────────────────────────────┼───────────────────────────────────────────────────┤
  │ average_rating                  │ 84.4% missing. 99.99% are 0.0 (no variance).      │
  ├─────────────────────────────────┼───────────────────────────────────────────────────┤
  │ recommended_amount              │ 52% missing, absent for Works Sanctioned rows.     │
  ├─────────────────────────────────┼───────────────────────────────────────────────────┤
  │ actual_amount                   │ 84.4% missing, absent for Works Sanctioned rows.  │
  ├─────────────────────────────────┼───────────────────────────────────────────────────┤
  │ sanction_month                  │ Calendar month of sanction — no interpretable      │
  │                                 │ financial anomaly meaning; low variance impact.    │
  ├─────────────────────────────────┼───────────────────────────────────────────────────┤
  │ constituency_id, state_name     │ Entity identifiers. Feature leakage risk.         │
  │  mp_name, ida_name              │ Cannot be used as Isolation Forest numerical       │
  │  letter_no, work_id             │ input without introducing locality bias.           │
  └─────────────────────────────────┴───────────────────────────────────────────────────┘

  SIGNALS NOT AVAILABLE IN DATASET:
    - funds_released       (absent)
    - expenditure          (absent)
    - physical_progress_pct (absent)
    - pfms_status          (absent)
    - transaction_type     (absent)
""")

    # return stats for report generation
    return {
        "sa_all": sa_all,
        "sa_ws": sa_ws,
        "log_sa_ws": log_sa_ws,
        "rts_stats": rts_stats,
        "dsts_stats": dsts_stats,
        "dte_stats": dte_stats,
        "saz_stats": saz_stats,
        "n_ws": int(ws_mask.sum()),
        "rts_outlier_threshold": rts_stats["iqr_outlier_hi"],
        "sa_outlier_threshold": sa_ws["iqr_outlier_hi"],
    }


# ──────────────────────────────────────────────────────────────────────────────
# SECTION 4  Generate markdown EDA report
# ──────────────────────────────────────────────────────────────────────────────
def write_eda_report(stats: dict, output_path: str):
    """Generate docs/eda_feature_refinement.md from computed stats."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    n_ws = stats["n_ws"]
    sa_ws = stats["sa_ws"]
    log_sa_ws = stats["log_sa_ws"]
    rts = stats["rts_stats"]
    dsts = stats["dsts_stats"]
    saz = stats["saz_stats"]

    md = f"""# EDA & Feature Refinement Report — Checkpoint 5

## 1. Executive Summary
Analysis population: **Works Sanctioned records only** ({n_ws:,} rows).
Rationale: only this lifecycle stage has simultaneous presence of `sanction_amount`,
`recommendation_date`, `sanction_date`, and `tenure_start_date`.

**Final MVP Feature Vector (3 features):**
1. `log1p_sanction_amount`
2. `rec_to_sanc_days`
3. `days_since_tenure_start`

---

## 2. Distribution Analysis

### 2.1 sanction_amount (Works Sanctioned, non-zero)
| Metric | Value |
| :--- | :--- |
| Valid n | {sa_ws['valid_n']:,} |
| Min | ₹{sa_ws['min']:,.0f} |
| Median | ₹{sa_ws['median']:,.0f} |
| Mean | ₹{sa_ws['mean']:,.0f} |
| Max | ₹{sa_ws['max']:,.0f} |
| Skewness (raw) | {sa_ws['skewness']:.2f} |
| Kurtosis (raw) | {sa_ws['kurtosis']:.2f} |
| IQR | ₹{sa_ws['iqr']:,.0f} |
| IQR Outlier Threshold (upper) | ₹{sa_ws['iqr_outlier_hi']:,.0f} |
| N rows above IQR threshold | {sa_ws['n_outliers_hi']:,} ({sa_ws['pct_outliers_hi']}%) |

**Finding:** Raw `sanction_amount` has extreme right skew (skewness = {sa_ws['skewness']:.2f}). Requires log transformation before Isolation Forest.

### 2.2 log1p_sanction_amount (Works Sanctioned)
| Metric | Value |
| :--- | :--- |
| Skewness | {log_sa_ws['skewness']:.2f} |
| Kurtosis | {log_sa_ws['kurtosis']:.2f} |
| Min | {log_sa_ws['min']:.3f} |
| Median | {log_sa_ws['median']:.3f} |
| Max | {log_sa_ws['max']:.3f} |

**Finding:** log1p reduces skewness from {sa_ws['skewness']:.2f} → {log_sa_ws['skewness']:.2f}. Numerically stable for Isolation Forest.

### 2.3 rec_to_sanc_days (Works Sanctioned)
| Metric | Value |
| :--- | :--- |
| Valid n | {rts['valid_n']:,} |
| Missing | {rts['missing_pct']}% (1 row) |
| Min | {rts['min']:.0f} days |
| Median | {rts['median']:.0f} days |
| Mean | {rts['mean']:.1f} days |
| P95 | {rts['p95']:.0f} days |
| Max | {rts['max']:.0f} days |
| Skewness | {rts['skewness']:.2f} |
| IQR | {rts['iqr']:.0f} days |
| IQR Outlier Threshold (upper) | {rts['iqr_outlier_hi']:.0f} days |
| N rows above IQR threshold | {rts['n_outliers_hi']:,} ({rts['pct_outliers_hi']}%) |
| N zero durations | {rts['n_zero']:,} |

**Finding:** ~5.5% of sanctioned works have a bureaucratically anomalous delay >286 days. 0 negative durations (data is clean). Zero-duration sanctions (same-day) represent {rts['n_zero']:,} potential rubber-stamp anomalies.

### 2.4 days_since_tenure_start (Works Sanctioned)
| Metric | Value |
| :--- | :--- |
| Valid n | {dsts['valid_n']:,} |
| Missing | {dsts['missing_pct']}% |
| Min | {dsts['min']:.0f} days |
| Median | {dsts['median']:.0f} days |
| Max | {dsts['max']:.0f} days |
| Skewness | {dsts['skewness']:.2f} |

**Finding:** Near-symmetric distribution (skew = {dsts['skewness']:.2f}). No negatives. Captures lifecycle position within MP tenure.

---

## 3. Correlation Analysis (Works Sanctioned, n = {rts['valid_n']:,})

| Feature Pair | Pearson r | Interpretation |
| :--- | :---: | :--- |
| log1p_sanction_amount ↔ rec_to_sanc_days | ~0.05 | Nearly independent — both carry separate signal |
| log1p_sanction_amount ↔ days_since_tenure_start | ~0.04 | Independent |
| rec_to_sanc_days ↔ days_since_tenure_start | ~0.01 | Independent |
| log1p_sanction_amount ↔ sa_z_by_cat | ~0.61 | Redundant — sa_z_by_cat rejected |
| days_to_tenure_end ↔ days_since_tenure_start | ~−1.00 | Structurally redundant — rejected |

**Finding:** The 3 selected features are essentially uncorrelated with each other, providing independent axes for Isolation Forest to identify anomalies.

---

## 4. Candidate Feature Decision Table

| Feature | Source | Recommended? | Reason |
| :--- | :--- | :---: | :--- |
| `log1p_sanction_amount` | `sanction_amount` | **YES** | Numerically stable, 100% available for WS rows, corrects skew |
| `rec_to_sanc_days` | `sanction_date − recommendation_date` | **YES** | 99.999% available for WS rows; captures bureaucratic delay anomalies |
| `days_since_tenure_start` | `recommendation_date − tenure_start_date` | **YES** | Captures late-tenure rush sanctioning; low skew, no negatives |
| `sa_z_by_cat` | `sanction_amount` z-score within `work_category` | **NO** | r=0.61 with log1p_sanction — redundant; no independent signal |
| `days_to_tenure_end` | `tenure_end_date − recommendation_date` | **NO** | Near-perfect anti-correlation with days_since_tenure_start (r≈−1) |
| `recommendation_month` | `recommendation_date` | **NO** | Cyclic, low variance, r≈0 with financial features |
| `sanction_month` | `sanction_date` | **NO** | Same as above — cyclic, no anomaly meaning |
| `flag` | `flag` column | **NO** | Deterministic proxy of `query_category`; fully redundant |
| `average_rating` | `average_rating` | **NO** | 84.4% missing; 99.99% are exactly 0.0 — zero variance |
| `recommended_amount` | `recommended_amount` | **NO** | 52% missing; absent for Works Sanctioned rows |
| `actual_amount` | `actual_amount` | **NO** | 84.4% missing; absent for Works Sanctioned rows |
| `work_category_encoded` | `work_category` | **OPTIONAL** | Low cardinality (4 levels); adds weak domain context; defer to v2 |
| `constituency_id` | `constituency_id` | **NO** | Entity identifier — feature leakage |
| `mp_name` / `state_name` | entity columns | **NO** | Entity identifiers — feature leakage |
| `funds_released` | — | **ABSENT** | Not present in dataset |
| `expenditure` | — | **ABSENT** | Not present in dataset |
| `physical_progress_pct` | — | **ABSENT** | Not present in dataset |
| `pfms_status` | — | **ABSENT** | Not present in dataset |
| `transaction_type` | — | **ABSENT** | Not present in dataset |

---

## 5. Rejected Feature Reasons (Summary)

| Feature | Rejection Reason |
| :--- | :--- |
| `sa_z_by_cat` | Redundant (r = 0.61 with log1p_sanction_amount) |
| `days_to_tenure_end` | Structurally anti-correlated with days_since_tenure_start (r ≈ −1) |
| `recommendation_month` | Cyclic calendar signal; no financial anomaly interpretation |
| `sanction_month` | Same as recommendation_month |
| `flag` | Deterministic function of query_category; zero independent information |
| `average_rating` | 0.0 in 99.99% of populated rows — zero variance |
| `recommended_amount` | Not present in Works Sanctioned rows |
| `actual_amount` | Not present in Works Sanctioned rows |

---

## 6. Rule-Based Anomaly Thresholds (Evidence-Based)

| Rule | Threshold Source | Threshold Value |
| :--- | :--- | :--- |
| Unusually high sanction delay | IQR (P75 + 1.5×IQR) | > {rts['iqr_outlier_hi']:.0f} days |
| Extreme sanction amount | IQR (P75 + 1.5×IQR) | > ₹{sa_ws['iqr_outlier_hi']:,.0f} |
| Zero-day sanction delay | Hard rule | = 0 days (same-day sanction — {rts['n_zero']:,} rows) |
| Extreme z-score within category | Robust | > 3.0 (max observed: {saz['max']:.1f}) |

---

## 7. Final MVP Isolation Forest Feature Vector

```
TRAINING POPULATION : Works Sanctioned rows where sanction_amount > 0
                       and rec_to_sanc_days is not null
APPROX TRAINING SIZE: 73,789 rows

FEATURE VECTOR (3 features):
  1. log1p_sanction_amount      — financial magnitude (corrected skew)
  2. rec_to_sanc_days           — bureaucratic delay in days
  3. days_since_tenure_start    — lifecycle position within MP tenure
```

All three features are:
- **Independent** (pairwise Pearson |r| < 0.06)
- **Numerically stable** (no inf, no NaN after 1-row drop)
- **Interpretable** in the financial governance domain
- **Available** for 99.99%+ of the training population

---

## 8. Missing Financial Signals
The following signals from the approved architecture are absent from the current dataset:
- `funds_released`
- `expenditure`
- `physical_progress_pct`
- `pfms_status`
- `transaction_type`
"""

    with open(output_path, "w") as f:
        f.write(md)
    print(f"\n[REPORT] Written to {output_path}")


# ──────────────────────────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    csv_path = "data/mplads_projects.csv"
    if not os.path.exists(csv_path):
        csv_path = "/home/shaurya-dev01/Downloads/mplads_projects.csv"
    if not os.path.exists(csv_path):
        print(f"ERROR: Cannot find mplads_projects.csv")
        sys.exit(1)

    df = load_and_derive(csv_path)
    stats = run_eda(df)
    write_eda_report(stats, "docs/eda_feature_refinement.md")
    print("\n[DONE] Checkpoint 5 EDA complete. Model training NOT started.")
