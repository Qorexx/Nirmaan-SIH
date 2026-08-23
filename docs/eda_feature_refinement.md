# EDA & Feature Refinement Report — Checkpoint 5

## 1. Executive Summary
Analysis population: **Works Sanctioned records only** (73,790 rows).
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
| Valid n | 73,789 |
| Min | ₹2 |
| Median | ₹300,706 |
| Mean | ₹534,629 |
| Max | ₹49,740,000 |
| Skewness (raw) | 17.85 |
| Kurtosis (raw) | 693.42 |
| IQR | ₹399,364 |
| IQR Outlier Threshold (upper) | ₹1,198,014 |
| N rows above IQR threshold | 5,966 (8.09%) |

**Finding:** Raw `sanction_amount` has extreme right skew (skewness = 17.85). Requires log transformation before Isolation Forest.

### 2.2 log1p_sanction_amount (Works Sanctioned)
| Metric | Value |
| :--- | :--- |
| Skewness | -0.44 |
| Kurtosis | 1.18 |
| Min | 1.241 |
| Median | 12.614 |
| Max | 17.722 |

**Finding:** log1p reduces skewness from 17.85 → -0.44. Numerically stable for Isolation Forest.

### 2.3 rec_to_sanc_days (Works Sanctioned)
| Metric | Value |
| :--- | :--- |
| Valid n | 73,789 |
| Missing | 0.0% (1 row) |
| Min | 0 days |
| Median | 79 days |
| Mean | 104.7 days |
| P95 | 295 days |
| Max | 732 days |
| Skewness | 1.82 |
| IQR | 99 days |
| IQR Outlier Threshold (upper) | 286 days |
| N rows above IQR threshold | 4,034 (5.47%) |
| N zero durations | 156 |

**Finding:** ~5.5% of sanctioned works have a bureaucratically anomalous delay >286 days. 0 negative durations (data is clean). Zero-duration sanctions (same-day) represent 156 potential rubber-stamp anomalies.

### 2.4 days_since_tenure_start (Works Sanctioned)
| Metric | Value |
| :--- | :--- |
| Valid n | 73,789 |
| Missing | 0.0% |
| Min | 34 days |
| Median | 376 days |
| Max | 805 days |
| Skewness | 0.21 |

**Finding:** Near-symmetric distribution (skew = 0.21). No negatives. Captures lifecycle position within MP tenure.

---

## 3. Correlation Analysis (Works Sanctioned, n = 73,789)

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
| Unusually high sanction delay | IQR (P75 + 1.5×IQR) | > 286 days |
| Extreme sanction amount | IQR (P75 + 1.5×IQR) | > ₹1,198,014 |
| Zero-day sanction delay | Hard rule | = 0 days (same-day sanction — 156 rows) |
| Extreme z-score within category | Robust | > 3.0 (max observed: 56.8) |

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
