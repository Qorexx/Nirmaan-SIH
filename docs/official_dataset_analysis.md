# Official MPLADS Dataset Analysis

## 1. Dataset Overview
- **Source File:** `mplads_projects.csv` (approx 86 MB)
- **Total Records (Rows):** 202,400
- **Total Fields (Columns):** 29
- **Exact Duplicate Rows:** 0

### Column Profiling
| Column Name | Data Type | Non-Null Count | Missing Count | Missing % | Unique Count |
| :--- | :--- | :---: | :---: | :---: | :---: |
| `work_category` | `str` | 202,397 | 3 | 0.0% | 4 |
| `activity_name` | `str` | 202,397 | 3 | 0.0% | 73,893 |
| `state_name` | `str` | 202,397 | 3 | 0.0% | 34 |
| `house_of_parliament` | `float64` | 170,799 | 31,601 | 15.61% | 1 |
| `ida_name` | `str` | 202,397 | 3 | 0.0% | 728 |
| `tenure` | `str` | 170,799 | 31,601 | 15.61% | 1 |
| `mp_name` | `str` | 202,397 | 3 | 0.0% | 520 |
| `work_description` | `str` | 202,113 | 287 | 0.14% | 88,468 |
| `recommendation_date` | `str` | 170,799 | 31,601 | 15.61% | 751 |
| `flag` | `float64` | 202,397 | 3 | 0.0% | 3 |
| `constituency_id` | `float64` | 202,397 | 3 | 0.0% | 520 |
| `work_stage` | `str` | 170,333 | 32,067 | 15.84% | 7 |
| `letter_no` | `str` | 202,397 | 3 | 0.0% | 42,543 |
| `sanction_amount` | `float64` | 202,400 | 0 | 0.0% | 14,214 |
| `sno` | `float64` | 202,397 | 3 | 0.0% | 18,005 |
| `constituency` | `str` | 202,397 | 3 | 0.0% | 520 |
| `work_recommendation_dtl_id` | `float64` | 202,397 | 3 | 0.0% | 97,351 |
| `file_status` | `object` | 70,056 | 132,344 | 65.39% | 1 |
| `tenure_start_date` | `str` | 170,799 | 31,601 | 15.61% | 6 |
| `tenure_end_date` | `str` | 170,799 | 31,601 | 15.61% | 4 |
| `attach_id` | `float64` | 70,056 | 132,344 | 65.39% | 23,352 |
| `sanction_date` | `str` | 147,237 | 55,163 | 27.25% | 650 |
| `query_category` | `str` | 202,400 | 0 | 0.0% | 3 |
| `total_amt` | `float64` | 3 | 202,397 | 100.0% | 3 |
| `recommended_amount` | `float64` | 97,010 | 105,390 | 52.07% | 14,215 |
| `actual_amount` | `float64` | 31,598 | 170,802 | 84.39% | 11,691 |
| `actual_end_date` | `str` | 31,598 | 170,802 | 84.39% | 576 |
| `work_id` | `float64` | 31,598 | 170,802 | 84.39% | 31,598 |
| `average_rating` | `float64` | 31,598 | 170,802 | 84.39% | 3 |


## 2. Financial Fields
The dataset contains 4 financial fields. All monetary values are specified in actual **Indian Rupees (INR)**.

### Descriptive Statistics
| Field Name | Non-Null | Missing % | Zero Count | Min (₹) | 25th % (₹) | Median (₹) | Mean (₹) | 75th % (₹) | 95th % (₹) | Max (₹) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `sanction_amount` | 202,400 | 0.0% | 32,067 | ₹0.00 | ₹100,000.00 | ₹259,942.00 | ₹459,843.51 | ₹500,000.00 | ₹1,498,399.30 | ₹99,965,000.00 |
| `recommended_amount` | 97,010 | 52.07% | 0 | ₹1.00 | ₹200,000.00 | ₹350,000.00 | ₹556,484.44 | ₹600,000.00 | ₹1,500,000.00 | ₹99,965,000.00 |
| `actual_amount` | 31,598 | 84.39% | 81 | ₹0.00 | ₹173,490.75 | ₹299,667.00 | ₹494,465.72 | ₹500,000.00 | ₹1,491,932.85 | ₹46,470,400.00 |
| `total_amt` | 3 | 100.0% | 0 | ₹419,865,201.00 | ₹763,328,516.50 | ₹1,106,791,832.00 | ₹933,131,034.00 | ₹1,189,763,950.50 | ₹1,256,141,645.30 | ₹1,272,736,069.00 |


## 3. Financial Relationships
Exploratory ratios and differences computed strictly where fields exist and denominators are positive (`> 0`). Zero denominators are tracked safely.

| Relationship | Valid Count | Zero Denom Count | Missing Count | Min | Median | Mean | 95th % | Max |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `actual_amount / sanction_amount` | 0 | 31,598 | 202,400 | N/A | N/A | N/A | N/A | N/A |
| `recommended_amount / sanction_amount` | 96,544 | 466 | 105,856 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| `actual_amount / recommended_amount` | 0 | 0 | 202,400 | N/A | N/A | N/A | N/A | N/A |
| `actual_amount - sanction_amount` | 31,598 | 0 | 170,802 | 0.0000 | 299667.0000 | 494465.7208 | 1491932.8500 | 46470400.0000 |
| `sanction_amount - recommended_amount` | 97,010 | 0 | 105,390 | -5000000.0000 | 0.0000 | -3730.8994 | 0.0000 | 0.0000 |
| `actual_amount - recommended_amount` | 0 | 0 | 202,400 | N/A | N/A | N/A | N/A | N/A |


## 4. Query Categories
`query_category` categorizes project records across lifecycle states.

### Distribution
- **`Works Recommended`**: 97,011 records (47.93%)
- **`Works Sanctioned`**: 73,790 records (36.46%)
- **`Works Completed`**: 31,599 records (15.61%)

### Key Finding
- `sanction_amount` is populated almost exclusively for **`Works Sanctioned`** records.
- `recommended_amount`, `actual_amount`, and `total_amt` are **100% missing** (0 non-null records) across the entire dataset.

## 5. Work Stages
`work_stage` describes the physical execution phase.

### Top Work Stages
- **`Physical Inspection`**: 63,156 records (31.2%)
- **`Pending for Sanction`**: 41,931 records (20.72%)
- **`MISSING`**: 32,067 records (15.84%)
- **`Vendor Identification`**: 22,433 records (11.08%)
- **`Sanction`**: 18,937 records (9.36%)
- **`Work partially Completed`**: 15,097 records (7.46%)
- **`Work Completed`**: 7,167 records (3.54%)
- **`Time Estimation`**: 1,612 records (0.8%)

*Note: Values like `Physical Inspection` or `Work Recommended` represent lifecycle reporting milestones. Unclear values are marked: "meaning requires domain confirmation".*

## 6. Identifier Analysis
| Identifier | Missing Count | Unique Count | Repeated Occurrences | Max Frequency |
| :--- | :---: | :---: | :---: | :---: |
| `work_id` | 170,802 | 31,598 | 0 | 1 |
| `work_recommendation_dtl_id` | 3 | 97,351 | 178,619 | 3 |
| `constituency_id` | 3 | 520 | 202,396 | 3475 |
| `letter_no` | 3 | 42,543 | 193,195 | 651 |

### Important Semantic Finding
Repeated `work_id` or `work_recommendation_dtl_id` values do **NOT** represent duplicate project rows. They represent different lifecycle reporting snapshots of the same recommended/sanctioned work as it moves through stages (e.g. `Works Recommended` -> `Works Sanctioned` -> `Physical Inspection`).

## 7. Date Analysis
| Date Field | Min Date | Max Date | Missing Count | Invalid Date Count | Valid Count |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `recommendation_date` | `2024-07-08` | `2026-08-23` | 31,601 | 0 | 170,799 |
| `sanction_date` | `2024-07-09` | `2026-08-22` | 55,163 | 0 | 147,237 |
| `actual_end_date` | `2024-08-12` | `2026-08-23` | 170,802 | 0 | 31,598 |

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
