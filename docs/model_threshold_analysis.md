# Model Threshold Analysis — Isolation Forest Anomaly Detection

**Project:** SIH 2026 — Problem Statement SIH26102 (MoSPI)  
**Lead:** Person 1 (Financial AI / Anomaly Detection Engine)  
**Date:** 2026-08-23  

---

## 1. Current Model

The current baseline Isolation Forest model is configured and persisted as follows:

| Component / Parameter | Configuration Value |
| :--- | :--- |
| **Model Type** | `sklearn.ensemble.IsolationForest` |
| **`n_estimators`** | `200` |
| **`contamination`** | `'auto'` (sklearn default; offset = −0.5 against raw scores) |
| **`random_state`** | `42` |
| **Training Population** | **73,789** Works Sanctioned records (`query_category == 'Works Sanctioned'`, `sanction_amount > 0`, non-null features) |
| **Model Artifact** | `models/financial_isolation_forest.pkl` |

### Feature Vector Contract (3 Approved Features)
1. `log1p_sanction_amount`: Natural logarithm `log(1 + sanction_amount)` to normalize heavy right-skewed financial amounts (raw skewness 22.76 → −0.46).
2. `rec_to_sanc_days`: Bureaucratic approval duration in days (`sanction_date − recommendation_date`).
3. `days_since_tenure_start`: Days elapsed between MP tenure start date and project recommendation date (`recommendation_date − tenure_start_date`).

---

## 2. Current 26.31% Result

Evaluating the trained model on the 73,789 training records with `contamination='auto'` yields:

- **Normal Records (prediction = 1):** 54,375 (73.69%)
- **Anomalous Records (prediction = −1):** 19,414 (26.31%)

### Why 26.31% is Unacceptable as a Final Operational Threshold
1. **Severe Audit Overload:** Flagging 19,414 projects for audit out of 73,789 creates an unmanageable review queue (~35.8 alerts per MP constituency).
2. **Dilution of High-Risk Signals:** An anomaly rate of 26.31% conflates minor statistical variance with genuinely suspicious multi-dimensional outliers.
3. **Artifact of Default Parameter:** In `scikit-learn`, `contamination='auto'` sets `offset_ = -0.5` against raw decision scores. This threshold corresponds exactly to `decision_function(X) <= 0.0`. In our dataset distribution, 26.31% of records happen to have decision function scores <= 0.0.

---

## 3. Score Distribution

The Isolation Forest decision function outputs a continuous score where:
- **Lower / Negative Scores:** Higher degree of anomaly (isolated in fewer tree splits).
- **Higher / Positive Scores:** Normal baseline projects (deep in isolation trees).

### Statistical Summary of Decision Scores (N = 73,789)

| Statistic | Value |
| :--- | :---: |
| **Minimum Score** | `-0.237589` |
| **Maximum Score** | `+0.109930` |
| **Mean Score** | `+0.030439` |
| **Median Score** | `+0.043360` |
| **Standard Deviation** | `0.054671` |

### Percentile Breakdown

| Percentile | Score Cutoff | Description |
| :--- | :---: | :--- |
| **P01 (1%)** | `-0.125149` | Extreme 1% tail of most isolated records |
| **P05 (5%)** | `-0.077342` | Top 5% statistical outliers |
| **P10 (10%)** | `-0.046464` | Top 10% statistical outliers |
| **P25 (25%)** | `-0.003111` | 25th percentile (near 0 boundary) |
| **P75 (75%)** | `+0.073709` | 75th percentile |
| **P90 (90%)** | `+0.090345` | 90th percentile |
| **P95 (95%)** | `+0.095740` | 95th percentile |
| **P99 (99%)** | `+0.101608` | 99th percentile (most typical normal records) |

---

## 4. Candidate Thresholds

To tune the model anomaly detection cutoff, we evaluate 6 candidate anomaly rate percentiles derived directly from the real score distribution without retraining the underlying model:

| Target Rate | Score Cutoff | Model-Detected Anomalies | Actual Percentage |
| :---: | :---: | :---: | :---: |
| **1%** | `-0.125149` | 747 | 1.01% |
| **2%** | `-0.100013` | 1,502 | 2.04% |
| **3%** | `-0.093716` | 2,235 | 3.03% |
| **5%** | `-0.077342` | 3,690 | 5.00% |
| **8%** | `-0.055184` | 5,905 | 8.00% |
| **10%** | `-0.046464` | 7,379 | 10.00% |

---

## 5. Anomaly Volume & Operational Capacity

The operational viability of each candidate threshold depends on the review capacity of MoSPI audit officers across 543 Lok Sabha constituencies:

| Threshold | Total Alerts | Avg Alerts per Constituency | Operational Impact & Review Viability |
| :---: | :---: | :---: | :--- |
| **1%** | 747 | 1.38 | Extremely high precision targets; may miss moderate joint-signal anomalies. |
| **2%** | 1,502 | 2.77 | Highly focused review queue; easily manageable for initial team. |
| **3%** | 2,235 | 4.12 | **Balanced MVP volume; ~4 alerts/constituency over multi-year data.** |
| **5%** | 3,690 | 6.79 | Substantial alert queue; risks officer workload fatigue. |
| **8%** | 5,905 | 10.87 | High operational burden; potential high false-positive rate. |
| **10%** | 7,379 | 13.59 | Overwhelming alert volume for standard monitoring. |

### Operational Trade-off Analysis
- **Lower Threshold (1% – 2%):** Yields fewer alerts with extreme decision scores. Highly actionable for audit teams, but risks missing subtle multi-dimensional outliers.
- **Higher Threshold (5% – 10%):** Yields broader coverage of statistical outliers, but increases operational overhead and reviewer fatigue with potential false positives.

*Note: Precision and recall metrics cannot be computed on this dataset because the official MoSPI dataset contains no ground-truth anomaly labels.*

---

## 6. Feature Behavior

Analyzing the feature distributions of candidate anomaly subsets against the full population reveals the statistical drivers behind model-detected anomalies:

### Comparative Feature Statistics Across Subsets

| Feature / Metric | Full Population (N=73,789) | Top 100 Anomalies (N=100) | Top 1% Anomalies (N=747) | Top 3% Anomalies (N=2,235) | Top 5% Anomalies (N=3,690) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Sanction Amount Mean** | ₹5,34,628 | **₹19,54,978** | **₹19,42,816** | **₹14,63,293** | ₹13,37,833 |
| **Sanction Amount Median** | ₹3,00,706 | **₹15,50,000** | **₹9,50,000** | **₹4,00,000** | ₹3,00,000 |
| **Rec-to-Sanc Days Mean** | 104.7 days | **560.4 days** | **460.2 days** | **297.5 days** | 253.9 days |
| **Rec-to-Sanc Days Median** | 79.0 days | **544.0 days** | **492.0 days** | **341.0 days** | 201.0 days |
| **Days Since Tenure Mean** | 388.1 days | **113.1 days** | **213.1 days** | **297.7 days** | 332.2 days |
| **Days Since Tenure Median** | 376.0 days | **113.0 days** | **191.0 days** | **230.0 days** | 284.0 days |

### Anomaly Driver Insights
1. **Primary Driver — Severe Approval Delays:** Top anomalies feature extreme recommendation-to-sanction delays (median 544 days vs population median 79 days).
2. **Secondary Driver — Large Sanction Amounts:** Top anomalous records have median sanction amounts of ₹15.5 Lakhs (over 5x the population median of ₹3.01 Lakhs).
3. **Tertiary Driver — Tenure Timing:** Highly anomalous projects tend to be recommended early in tenure (median 113 days since tenure start vs population median 376 days).
4. **Multi-Signal Interaction:** The Isolation Forest isolates records fastest when multiple features exhibit simultaneous deviations (e.g. ₹50 Lakh sanction with a 693-day approval delay early in tenure).

---

## 7. Top Anomalies

The top 100 most anomalous records (lowest decision scores) have been exported to:
`docs/top_100_model_anomalies.csv`

### Sample of Top 5 Model-Detected Anomalies

| Work Rec Dtl ID | Constituency | Category | Sanction Amount | Rec Date | Sanc Date | Rec-to-Sanc Days | Tenure Start | Days Since Tenure | Anomaly Score |
| :---: | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 139500 | Diphu (ST) | Normal/Others | ₹50,00,000 | 2024-09-06 | 2026-07-31 | 693 | 2024-06-04 | 94 | `-0.237589` |
| 143526 | MUMBAI NORTH | Normal/Others | ₹45,00,000 | 2024-09-25 | 2026-03-25 | 546 | 2024-06-04 | 113 | `-0.231699` |
| 150074 | THOOTHUKKUDI | Normal/Others | ₹30,00,000 | 2024-11-02 | 2026-05-21 | 565 | 2024-06-04 | 151 | `-0.227842` |
| 139022 | BASIRHAT | Normal/Others | ₹27,65,000 | 2024-09-05 | 2026-07-08 | 671 | 2024-06-04 | 93 | `-0.227841` |
| 144827 | TIRUPPUR | Normal/Others | ₹52,95,000 | 2024-09-30 | 2026-02-20 | 508 | 2024-06-04 | 118 | `-0.223893` |

---

## 8. Recommended MVP Threshold

### Recommendation: **3.0% Anomaly Rate (Score Cutoff = `-0.093716`)**

### Justification Matrix

| Criterion | Evaluation & Rationale |
| :--- | :--- |
| **Anomaly Volume** | Generates **2,235 alerts** across 73,789 projects (~4.12 alerts per Lok Sabha constituency). This volume matches the realistic capacity of MoSPI audit teams. |
| **Score Distribution** | `-0.093716` lies on the upper elbow of the negative decision score tail, separating significant multi-dimensional outliers from baseline variance. |
| **Feature Behavior** | Captures records with median sanction amounts of ₹4.0 Lakhs and median delays of 341 days (over 4.3x the national median delay). |
| **Operational Usefulness** | Provides high-signal, actionable review targets without causing officer alert fatigue. |
| **Interpretability** | Every flagged project can be explained clearly via its composite delay, amount, and tenure timing scores. |

> [!IMPORTANT]
> **Operational Terminology Notice:** All records flagged by this threshold must be categorized as **"model-detected statistical anomalies"**. They represent statistical deviations from historical norms and MUST NOT be labeled as "fraud", "corruption", or "financial fraud" without independent audit verification.

---

## 9. Limitations

1. **Unsupervised Nature:** In the absence of labeled fraud ground-truth, threshold selection is based on distribution percentiles and operational volume constraints rather than empirical ROC/PR optimization.
2. **Sanction-Stage Scope:** The current feature set (`log1p_sanction_amount`, `rec_to_sanc_days`, `days_since_tenure_start`) evaluates only sanction-stage dynamics. It cannot detect post-sanction execution risks, non-disbursement, or embezzlement.
3. **Absence of Post-Sanction Signals:** Core financial tracking fields (`funds_released`, `expenditure`, `physical_progress_pct`, `pfms_status`) are not present in this dataset lifecycle snapshot.

---

## 10. Future Calibration

1. **Recalibration on Verified Audit Feedback:** As MoSPI audit teams review flagged statistical anomalies, audit outcome labels (e.g. `confirmed_irregularity`, `benign_delay`) should be logged to train supervised or semi-supervised classifiers.
2. **Dynamic Thresholding by Category / Region:** Future iterations can implement category-specific thresholds (e.g. distinct score cutoffs for Trust & Society recommendations vs public infrastructure works).
3. **Multi-Stage Feature Fusion:** When transaction-level disbursal data becomes available, the anomaly score threshold should be recalibrated to incorporate expenditure-to-release and release-to-sanction ratios.
