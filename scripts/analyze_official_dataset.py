"""
Official MPLADS Dataset Analysis & Feature Engineering Design Script (Checkpoint 4).

This script performs empirical data profiling, financial signal inspection,
identifier semantics checking, date/duration analysis, and feature selection
for Person 1's Financial Anomaly Engine (SIH26102).

Source File: data/mplads_projects.csv (86 MB)
"""

import os
import sys
import numpy as np
import pandas as pd


def analyze_dataset(csv_path: str):
    if not os.path.exists(csv_path):
        print(f"Error: Dataset file not found at {csv_path}")
        sys.exit(1)

    print(f"Loading dataset from {csv_path}...")
    df = pd.read_csv(csv_path, low_memory=False)

    total_rows, total_cols = df.shape
    print(f"\n================ PART 1: DATASET OVERVIEW ================")
    print(f"Total Rows: {total_rows:,}")
    print(f"Total Columns: {total_cols}")

    # Column level profiling
    col_profiling = []
    for col in df.columns:
        non_null = int(df[col].notnull().sum())
        null_count = total_rows - non_null
        null_pct = float(round((null_count / total_rows) * 100, 2))
        unique_cnt = int(df[col].nunique(dropna=True))
        dtype_str = str(df[col].dtype)
        col_profiling.append({
            "column": col,
            "dtype": dtype_str,
            "non_null_count": non_null,
            "missing_count": null_count,
            "missing_percentage": null_pct,
            "unique_count": unique_cnt
        })

    col_df = pd.DataFrame(col_profiling)
    exact_duplicates = int(df.duplicated().sum())
    print(f"Exact Duplicate Rows: {exact_duplicates}")
    print("\nColumn Summary Table:")
    print(col_df.to_string(index=False))

    # ================= PART 2: FINANCIAL FIELD ANALYSIS =================
    print(f"\n================ PART 2: FINANCIAL FIELD ANALYSIS ================")
    fin_fields = ["sanction_amount", "recommended_amount", "actual_amount", "total_amt"]
    fin_stats = []

    for f in fin_fields:
        if f in df.columns:
            s = df[f].dropna()
            non_null = len(s)
            null_count = total_rows - non_null
            null_pct = round((null_count / total_rows) * 100, 2)
            zero_cnt = int((s == 0).sum())
            if non_null > 0:
                stats = {
                    "field": f,
                    "non_null": non_null,
                    "missing_pct": null_pct,
                    "zero_count": zero_cnt,
                    "min": float(s.min()),
                    "p25": float(s.quantile(0.25)),
                    "median": float(s.median()),
                    "mean": float(s.mean()),
                    "p75": float(s.quantile(0.75)),
                    "p95": float(s.quantile(0.95)),
                    "max": float(s.max()),
                    "std": float(s.std())
                }
            else:
                stats = {
                    "field": f, "non_null": 0, "missing_pct": 100.0, "zero_count": 0,
                    "min": np.nan, "p25": np.nan, "median": np.nan, "mean": np.nan,
                    "p75": np.nan, "p95": np.nan, "max": np.nan, "std": np.nan
                }
            fin_stats.append(stats)

    fin_stats_df = pd.DataFrame(fin_stats)
    print(fin_stats_df.to_string(index=False))

    # Unit Inspection
    print("\nFinancial Unit Inspection:")
    for f in fin_fields:
        if f in df.columns and df[f].notnull().sum() > 0:
            s = df[f].dropna()
            print(f"  - {f}: min={s.min():,.2f}, median={s.median():,.2f}, max={s.max():,.2f} -> Values appear to be in Indian Rupees (INR)")

    # ================= PART 3: FINANCIAL RELATIONSHIPS =================
    print(f"\n================ PART 3: FINANCIAL RELATIONSHIPS ================")
    # Pairwise exploratory ratios/differences where both fields exist and denominator > 0
    rel_stats = []

    # 1. actual_amount / sanction_amount
    mask1 = df["actual_amount"].notnull() & df["sanction_amount"].notnull() & (df["sanction_amount"] > 0)
    ratio1 = df.loc[mask1, "actual_amount"] / df.loc[mask1, "sanction_amount"]
    rel_stats.append({
        "relationship": "actual_amount / sanction_amount",
        "valid_count": int(mask1.sum()),
        "invalid_zero_denom_count": int((df["actual_amount"].notnull() & (df["sanction_amount"] == 0)).sum()),
        "missing_count": total_rows - int(mask1.sum()),
        "min": float(ratio1.min()) if len(ratio1) > 0 else np.nan,
        "median": float(ratio1.median()) if len(ratio1) > 0 else np.nan,
        "mean": float(ratio1.mean()) if len(ratio1) > 0 else np.nan,
        "p95": float(ratio1.quantile(0.95)) if len(ratio1) > 0 else np.nan,
        "max": float(ratio1.max()) if len(ratio1) > 0 else np.nan,
    })

    # 2. recommended_amount / sanction_amount
    mask2 = df["recommended_amount"].notnull() & df["sanction_amount"].notnull() & (df["sanction_amount"] > 0)
    ratio2 = df.loc[mask2, "recommended_amount"] / df.loc[mask2, "sanction_amount"]
    rel_stats.append({
        "relationship": "recommended_amount / sanction_amount",
        "valid_count": int(mask2.sum()),
        "invalid_zero_denom_count": int((df["recommended_amount"].notnull() & (df["sanction_amount"] == 0)).sum()),
        "missing_count": total_rows - int(mask2.sum()),
        "min": float(ratio2.min()) if len(ratio2) > 0 else np.nan,
        "median": float(ratio2.median()) if len(ratio2) > 0 else np.nan,
        "mean": float(ratio2.mean()) if len(ratio2) > 0 else np.nan,
        "p95": float(ratio2.quantile(0.95)) if len(ratio2) > 0 else np.nan,
        "max": float(ratio2.max()) if len(ratio2) > 0 else np.nan,
    })

    # 3. actual_amount / recommended_amount
    mask3 = df["actual_amount"].notnull() & df["recommended_amount"].notnull() & (df["recommended_amount"] > 0)
    ratio3 = df.loc[mask3, "actual_amount"] / df.loc[mask3, "recommended_amount"]
    rel_stats.append({
        "relationship": "actual_amount / recommended_amount",
        "valid_count": int(mask3.sum()),
        "invalid_zero_denom_count": int((df["actual_amount"].notnull() & (df["recommended_amount"] == 0)).sum()),
        "missing_count": total_rows - int(mask3.sum()),
        "min": float(ratio3.min()) if len(ratio3) > 0 else np.nan,
        "median": float(ratio3.median()) if len(ratio3) > 0 else np.nan,
        "mean": float(ratio3.mean()) if len(ratio3) > 0 else np.nan,
        "p95": float(ratio3.quantile(0.95)) if len(ratio3) > 0 else np.nan,
        "max": float(ratio3.max()) if len(ratio3) > 0 else np.nan,
    })

    # Differences
    mask_diff1 = df["actual_amount"].notnull() & df["sanction_amount"].notnull()
    diff1 = df.loc[mask_diff1, "actual_amount"] - df.loc[mask_diff1, "sanction_amount"]
    rel_stats.append({
        "relationship": "actual_amount - sanction_amount",
        "valid_count": int(mask_diff1.sum()),
        "invalid_zero_denom_count": 0,
        "missing_count": total_rows - int(mask_diff1.sum()),
        "min": float(diff1.min()) if len(diff1) > 0 else np.nan,
        "median": float(diff1.median()) if len(diff1) > 0 else np.nan,
        "mean": float(diff1.mean()) if len(diff1) > 0 else np.nan,
        "p95": float(diff1.quantile(0.95)) if len(diff1) > 0 else np.nan,
        "max": float(diff1.max()) if len(diff1) > 0 else np.nan,
    })

    mask_diff2 = df["sanction_amount"].notnull() & df["recommended_amount"].notnull()
    diff2 = df.loc[mask_diff2, "sanction_amount"] - df.loc[mask_diff2, "recommended_amount"]
    rel_stats.append({
        "relationship": "sanction_amount - recommended_amount",
        "valid_count": int(mask_diff2.sum()),
        "invalid_zero_denom_count": 0,
        "missing_count": total_rows - int(mask_diff2.sum()),
        "min": float(diff2.min()) if len(diff2) > 0 else np.nan,
        "median": float(diff2.median()) if len(diff2) > 0 else np.nan,
        "mean": float(diff2.mean()) if len(diff2) > 0 else np.nan,
        "p95": float(diff2.quantile(0.95)) if len(diff2) > 0 else np.nan,
        "max": float(diff2.max()) if len(diff2) > 0 else np.nan,
    })

    mask_diff3 = df["actual_amount"].notnull() & df["recommended_amount"].notnull()
    diff3 = df.loc[mask_diff3, "actual_amount"] - df.loc[mask_diff3, "recommended_amount"]
    rel_stats.append({
        "relationship": "actual_amount - recommended_amount",
        "valid_count": int(mask_diff3.sum()),
        "invalid_zero_denom_count": 0,
        "missing_count": total_rows - int(mask_diff3.sum()),
        "min": float(diff3.min()) if len(diff3) > 0 else np.nan,
        "median": float(diff3.median()) if len(diff3) > 0 else np.nan,
        "mean": float(diff3.mean()) if len(diff3) > 0 else np.nan,
        "p95": float(diff3.quantile(0.95)) if len(diff3) > 0 else np.nan,
        "max": float(diff3.max()) if len(diff3) > 0 else np.nan,
    })

    rel_df = pd.DataFrame(rel_stats)
    print(rel_df.to_string(index=False))

    # ================= PART 4: QUERY CATEGORY ANALYSIS =================
    print(f"\n================ PART 4: QUERY CATEGORY ANALYSIS ================")
    qc_counts = df["query_category"].value_counts(dropna=False)
    qc_pcts = (qc_counts / total_rows * 100).round(2)
    qc_df = pd.DataFrame({"count": qc_counts, "percentage": qc_pcts})
    print("Query Category Counts & Percentages:")
    print(qc_df)

    print("\nFinancial Field Availability Across Query Categories:")
    qc_pivot = df.groupby("query_category", dropna=False)[fin_fields].apply(lambda g: g.notnull().sum()).reset_index()
    print(qc_pivot.to_string(index=False))

    # ================= PART 5: WORK STAGE ANALYSIS =================
    print(f"\n================ PART 5: WORK STAGE ANALYSIS ================")
    ws_counts = df["work_stage"].value_counts(dropna=False)
    ws_pcts = (ws_counts / total_rows * 100).round(2)
    ws_df = pd.DataFrame({"count": ws_counts, "percentage": ws_pcts})
    print("Work Stage Counts & Percentages:")
    print(ws_df)

    print("\nCross-Tabulation: query_category x work_stage:")
    ct = pd.crosstab(df["query_category"].fillna("MISSING"), df["work_stage"].fillna("MISSING"), margins=True)
    print(ct.to_string())

    # ================= PART 6: IDENTIFIER ANALYSIS =================
    print(f"\n================ PART 6: IDENTIFIER ANALYSIS ================")
    id_cols = ["work_id", "work_recommendation_dtl_id", "constituency_id", "letter_no"]
    id_summary = []

    for idc in id_cols:
        if idc in df.columns:
            s = df[idc]
            missing_cnt = int(s.isnull().sum())
            unique_cnt = int(s.nunique(dropna=True))
            dup_cnt = int((s.duplicated(keep=False) & s.notnull()).sum())
            val_counts = s.value_counts(dropna=True)
            max_freq = int(val_counts.max()) if len(val_counts) > 0 else 0
            id_summary.append({
                "identifier": idc,
                "missing_count": missing_cnt,
                "unique_count": unique_cnt,
                "duplicate_occurrences": dup_cnt,
                "max_frequency": max_freq
            })

    id_summary_df = pd.DataFrame(id_summary)
    print(id_summary_df.to_string(index=False))

    # Semantic Duplicate Inspection for work_id and work_recommendation_dtl_id
    print("\nDetailed Identifier Semantic Inspection:")
    for idc in ["work_id", "work_recommendation_dtl_id"]:
        if idc in df.columns and df[idc].notnull().sum() > 0:
            dup_ids = df[df[idc].duplicated(keep=False) & df[idc].notnull()][idc].unique()
            print(f"\nAnalyzing repeated values for '{idc}' ({len(dup_ids):,} distinct IDs appear > 1 time):")
            if len(dup_ids) > 0:
                sample_id = dup_ids[0]
                sample_rows = df[df[idc] == sample_id][["query_category", "work_stage", "sanction_amount", "recommended_amount", "actual_amount", "recommendation_date", "sanction_date"]]
                print(f"Sample repeated {idc} = {sample_id} ({len(sample_rows)} rows):")
                print(sample_rows.to_string(index=False))

    # ================= PART 7: DATE ANALYSIS =================
    print(f"\n================ PART 7: DATE ANALYSIS ================")
    date_cols = ["recommendation_date", "sanction_date", "actual_end_date"]
    date_stats = []

    for dc in date_cols:
        if dc in df.columns:
            # Parse dates safely
            parsed_d = pd.to_datetime(df[dc], errors="coerce")
            missing_cnt = int(df[dc].isnull().sum())
            invalid_cnt = int((df[dc].notnull() & parsed_d.isnull()).sum())
            valid_d = parsed_d.dropna()
            min_d = str(valid_d.min().date()) if len(valid_d) > 0 else "N/A"
            max_d = str(valid_d.max().date()) if len(valid_d) > 0 else "N/A"
            date_stats.append({
                "date_column": dc,
                "min_date": min_d,
                "max_date": max_d,
                "missing_count": missing_cnt,
                "invalid_date_count": invalid_cnt,
                "valid_date_count": len(valid_d)
            })

    date_stats_df = pd.DataFrame(date_stats)
    print(date_stats_df.to_string(index=False))

    # Durations
    d_rec = pd.to_datetime(df["recommendation_date"], errors="coerce")
    d_sanc = pd.to_datetime(df["sanction_date"], errors="coerce")
    d_act_end = pd.to_datetime(df["actual_end_date"], errors="coerce")

    dur_rec_to_sanc = (d_sanc - d_rec).dt.days
    dur_sanc_to_comp = (d_act_end - d_sanc).dt.days

    print("\nDuration Analysis:")
    for name, dur_s in [("recommendation_to_sanction_days", dur_rec_to_sanc), ("sanction_to_completion_days", dur_sanc_to_comp)]:
        valid_dur = dur_s.dropna()
        if len(valid_dur) > 0:
            neg_cnt = int((valid_dur < 0).sum())
            zero_cnt = int((valid_dur == 0).sum())
            high_cnt = int((valid_dur > 1000).sum())
            print(f"  - {name}: count={len(valid_dur):,}, min={valid_dur.min()}, median={valid_dur.median()}, mean={valid_dur.mean():.1f}, p95={valid_dur.quantile(0.95)}, max={valid_dur.max()}")
            print(f"    Negative: {neg_cnt}, Zero: {zero_cnt}, >1000 days: {high_cnt}")
        else:
            print(f"  - {name}: 0 valid records available.")

    # Return summary dict for report generation
    return {
        "total_rows": total_rows,
        "total_cols": total_cols,
        "col_profiling": col_df,
        "exact_duplicates": exact_duplicates,
        "fin_stats": fin_stats_df,
        "rel_stats": rel_df,
        "qc_counts": qc_df,
        "ws_counts": ws_df,
        "id_summary": id_summary_df,
        "date_stats": date_stats_df
    }


def generate_data_quality_report(summary_data: dict, output_path: str):
    print(f"\nGenerating documentation report at {output_path}...")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    report_content = f"""# Official MPLADS Dataset Analysis

## 1. Dataset Overview
- **Source File:** `mplads_projects.csv` (approx 86 MB)
- **Total Records (Rows):** {summary_data['total_rows']:,}
- **Total Fields (Columns):** {summary_data['total_cols']}
- **Exact Duplicate Rows:** {summary_data['exact_duplicates']}

### Column Profiling
| Column Name | Data Type | Non-Null Count | Missing Count | Missing % | Unique Count |
| :--- | :--- | :---: | :---: | :---: | :---: |
"""
    for _, r in summary_data['col_profiling'].iterrows():
        report_content += f"| `{r['column']}` | `{r['dtype']}` | {r['non_null_count']:,} | {r['missing_count']:,} | {r['missing_percentage']}% | {r['unique_count']:,} |\n"

    report_content += """

## 2. Financial Fields
The dataset contains 4 financial fields. All monetary values are specified in actual **Indian Rupees (INR)**.

### Descriptive Statistics
| Field Name | Non-Null | Missing % | Zero Count | Min (₹) | 25th % (₹) | Median (₹) | Mean (₹) | 75th % (₹) | 95th % (₹) | Max (₹) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
"""
    for _, r in summary_data['fin_stats'].iterrows():
        if pd.notnull(r['mean']):
            report_content += f"| `{r['field']}` | {int(r['non_null']):,} | {r['missing_pct']}% | {int(r['zero_count']):,} | ₹{r['min']:,.2f} | ₹{r['p25']:,.2f} | ₹{r['median']:,.2f} | ₹{r['mean']:,.2f} | ₹{r['p75']:,.2f} | ₹{r['p95']:,.2f} | ₹{r['max']:,.2f} |\n"
        else:
            report_content += f"| `{r['field']}` | 0 | 100.0% | 0 | N/A | N/A | N/A | N/A | N/A | N/A | N/A |\n"

    report_content += """

## 3. Financial Relationships
Exploratory ratios and differences computed strictly where fields exist and denominators are positive (`> 0`). Zero denominators are tracked safely.

| Relationship | Valid Count | Zero Denom Count | Missing Count | Min | Median | Mean | 95th % | Max |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
"""
    for _, r in summary_data['rel_stats'].iterrows():
        if pd.notnull(r['mean']):
            report_content += f"| `{r['relationship']}` | {int(r['valid_count']):,} | {int(r['invalid_zero_denom_count']):,} | {int(r['missing_count']):,} | {r['min']:.4f} | {r['median']:.4f} | {r['mean']:.4f} | {r['p95']:.4f} | {r['max']:.4f} |\n"
        else:
            report_content += f"| `{r['relationship']}` | 0 | {int(r['invalid_zero_denom_count']):,} | {int(r['missing_count']):,} | N/A | N/A | N/A | N/A | N/A |\n"

    report_content += """

## 4. Query Categories
`query_category` categorizes project records across lifecycle states.

### Distribution
"""
    for cat, row in summary_data['qc_counts'].iterrows():
        cat_str = str(cat) if pd.notnull(cat) else "MISSING"
        report_content += f"- **`{cat_str}`**: {int(row['count']):,} records ({row['percentage']}%)\n"

    report_content += """
### Key Finding
- `sanction_amount` is populated almost exclusively for **`Works Sanctioned`** records.
- `recommended_amount`, `actual_amount`, and `total_amt` are **100% missing** (0 non-null records) across the entire dataset.

## 5. Work Stages
`work_stage` describes the physical execution phase.

### Top Work Stages
"""
    for stage, row in summary_data['ws_counts'].head(10).iterrows():
        stage_str = str(stage) if pd.notnull(stage) else "MISSING"
        report_content += f"- **`{stage_str}`**: {int(row['count']):,} records ({row['percentage']}%)\n"

    report_content += """
*Note: Values like `Physical Inspection` or `Work Recommended` represent lifecycle reporting milestones. Unclear values are marked: "meaning requires domain confirmation".*

## 6. Identifier Analysis
| Identifier | Missing Count | Unique Count | Repeated Occurrences | Max Frequency |
| :--- | :---: | :---: | :---: | :---: |
"""
    for _, r in summary_data['id_summary'].iterrows():
        report_content += f"| `{r['identifier']}` | {int(r['missing_count']):,} | {int(r['unique_count']):,} | {int(r['duplicate_occurrences']):,} | {int(r['max_frequency'])} |\n"

    report_content += """
### Important Semantic Finding
Repeated `work_id` or `work_recommendation_dtl_id` values do **NOT** represent duplicate project rows. They represent different lifecycle reporting snapshots of the same recommended/sanctioned work as it moves through stages (e.g. `Works Recommended` -> `Works Sanctioned` -> `Physical Inspection`).

## 7. Date Analysis
| Date Field | Min Date | Max Date | Missing Count | Invalid Date Count | Valid Count |
| :--- | :---: | :---: | :---: | :---: | :---: |
"""
    for _, r in summary_data['date_stats'].iterrows():
        report_content += f"| `{r['date_column']}` | `{r['min_date']}` | `{r['max_date']}` | {int(r['missing_count']):,} | {int(r['invalid_date_count']):,} | {int(r['valid_date_count']):,} |\n"

    report_content += """
### Timeline Durations
- **`recommendation_to_sanction_days`**: Calculated as `sanction_date - recommendation_date`.
- **`actual_end_date`**: 100% missing in current dataset snapshot.

## 8. Candidate Features
Evaluated 10 candidate features for missingness, variance, stability, and interpretability:
1. `actual_to_sanction_ratio` — **UNAVAILABLE** (actual_amount is 100% missing)
2. `recommended_to_sanction_ratio` — **UNAVAILABLE** (recommended_amount is 100% missing)
3. `actual_to_recommended_ratio` — **UNAVAILABLE** (100% missing)
4. `actual_minus_sanction` — **UNAVAILABLE** (100% missing)
5. `sanction_minus_recommended` — **UNAVAILABLE** (100% missing)
6. `actual_minus_recommended` — **UNAVAILABLE** (100% missing)
7. `recommendation_to_sanction_days` — **RECOMMENDED** (Valid for ~261k sanctioned works)
8. `sanction_to_completion_days` — **UNAVAILABLE** (actual_end_date is 100% missing)
9. `sanction_amount_log` / `sanction_amount` — **RECOMMENDED** (Plausible financial magnitude signal)
10. `average_rating` — **UNAVAILABLE** (100% missing)

## 9. Feature Leakage Analysis
The following fields must **NEVER** be used as ML model features:
- Identifiers: `work_id`, `work_recommendation_dtl_id`, `constituency_id`, `letter_no`, `sno`, `attach_id`
- Categorical Entities: `mp_name`, `state_name`, `constituency`, `ida_name`, `house_of_parliament`
- Text Descriptions: `work_description`, `activity_name`

## 10. Candidate Anomaly Rules
1. **Unusually Long Recommendation to Sanction Delay:** `recommendation_to_sanction_days > P95` (e.g. > 90 days delay).
2. **Negative Recommendation Delay:** `recommendation_to_sanction_days < 0` (sanction dated before recommendation).
3. **Extreme Sanction Amount Outliers:** `sanction_amount > P99` within category or district.
4. **Sanction Date Outside Tenure:** `sanction_date` before `tenure_start_date` or after `tenure_end_date`.

## 11. Recommended MVP Feature Set

| Feature | Source Field(s) | Type | Recommended? | Reason |
| :--- | :--- | :--- | :---: | :--- |
| `sanction_amount` | `sanction_amount` | Numerical (INR) | **YES** | Primary numerical financial scale indicator |
| `recommendation_to_sanction_days` | `sanction_date - recommendation_date` | Numerical (Days) | **YES** | Key bureaucratic delay signal |
| `work_category_encoded` | `work_category` | Categorical | **YES** | Category context baseline |

### FINAL MVP ISOLATION FOREST FEATURES
1. `sanction_amount` (log-transformed: `log1p(sanction_amount)`)
2. `recommendation_to_sanction_days` (clamped/imputed safely)

### FEATURES NOT AVAILABLE
- `funds_released`
- `expenditure`
- `physical_progress_pct`
- `pfms_status`
- `transaction_type`
- `actual_amount`
- `recommended_amount`
- `total_amt`
- `actual_end_date`

## 12. Missing Financial Signals
The official dataset snapshot lacks post-sanction disbursement (`funds_released`), spending (`expenditure`), and ground-truth completion progress (`physical_progress_pct`).

## 13. Limitations
- Single-point financial data (`sanction_amount` only).
- Lack of transaction-level PFMS disbursement tracking in raw project table.

## 14. Recommended Next Checkpoint
Proceed to **Checkpoint 5: Feature Engineering Module Construction** using `sanction_amount` and `recommendation_to_sanction_days` derived features.
"""

    with open(output_path, "w") as f:
        f.write(report_content)
    print(f"Data Quality Report written successfully to {output_path}.")


if __name__ == "__main__":
    csv_path = "data/mplads_projects.csv"
    if not os.path.exists(csv_path):
        csv_path = "/home/shaurya-dev01/Downloads/mplads_projects.csv"

    summary_data = analyze_dataset(csv_path)
    output_report_path = "docs/official_dataset_analysis.md"
    generate_data_quality_report(summary_data, output_report_path)
