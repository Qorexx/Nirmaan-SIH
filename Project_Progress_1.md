# Methodology Progress Report — Financial Anomaly Detection Engine

**Project:** SIH 2026 — Problem Statement SIH26102  
**Organization:** Ministry of Statistics and Programme Implementation (MoSPI)  
**Lead:** Person 1 (Financial AI / Anomaly Detection Engine)  

---

## Checkpoint 1 — Project Initialization

### What I did
- Initialized the repository directory structure for the Financial Anomaly Detection Engine microservice.
- Set up isolated directory layers (`src/`, `data/raw/`, `data/processed/`, `models/`, `docs/`, `tests/`).
- Created a Python virtual environment (`.venv`) for project isolation.
- Defined explicit dependency requirements in `requirements.txt`.
- Configured `.gitignore` to prevent committing binary artifacts, virtual environments, cache files, and datasets.
- Authored initial project documentation in `README.md` and basic runtime settings in `src/config.py`.

### How I did it
- Configured modular layout:
  - `src/` to hold core Python modules (`config.py`, feature engineering, Isolation Forest model, rule engine, FastAPI app).
  - `data/raw/` and `data/processed/` for mock/production dataset management.
  - `models/` for serializing trained `scikit-learn` Isolation Forest models.
  - `tests/` for `pytest` unit/integration test suites.
- Created `.venv` using `virtualenv` and installed initial dependencies (`pandas`, `numpy`, `scikit-learn`, `fastapi`, `uvicorn`, `pydantic`, `pytest`, `python-dotenv`).
- Set environment defaults in `src/config.py` (Port 8001, risk threshold boundaries, contamination factor).

### Why I did it
- **Modular Isolation:** Person 1's module must run independently as a FastAPI microservice (`http://localhost:8001`) that Person 6 can easily integrate.
- **Reproducibility:** Enforcing virtual environment separation and explicit `requirements.txt` ensures seamless execution across team members' local machines.
- **Data & Model Hygiene:** Keeping dataset placeholders and serialized models out of Git prevents repository bloat while preserving reproducible directory structures (`.gitkeep`).

### Verification
- Verified directory tree creation using file system checks.
- Verified Python environment version (`Python 3.12.3`).
- Verified dependencies installation within `.venv`.
- Verified importability of `src.config`.

### Files Created
- `README.md` — Project documentation and setup guide.
- `.gitignore` — Ignore rules for Python, virtual environments, models, and data.
- `requirements.txt` — Project dependencies specification.
- `src/__init__.py` — Package initializer.
- `src/config.py` — Configuration constants & threshold settings.
- `tests/__init__.py` — Test package initializer.
- `data/raw/.gitkeep` — Directory placeholder.
- `data/processed/.gitkeep` — Directory placeholder.
- `models/.gitkeep` — Directory placeholder.
- `docs/.gitkeep` — Directory placeholder.
- `Project_Progress_1.md` — Chronological development progress log.

---

## Checkpoint 2 — Synthetic Dataset Generation

### What I did
- Generated a synthetic dataset of 500 MPLADS infrastructure projects (`data/mock_mplads.csv`) following the approved 10-column schema.
- Injected exactly 25 anomalies (5.0%) across 4 strictly mutually exclusive anomaly categories:
  1. `high_expenditure_low_progress` (6 projects)
  2. `expenditure_exceeds_sanction` (6 projects)
  3. `severe_progress_mismatch` (7 projects)
  4. `zero_progress_high_release` (6 projects)
- Developed an automated generation and verification script (`scripts/generate_synthetic_data.py`) using a fixed random seed (`42`) for 100% reproducible data generation.

### How I did it
- Enforced actual INR/Rupee scale for monetary values (`estimated_cost` between ₹500,000 and ₹25,000,000).
- Modelled realistic non-deterministic financial and progress relationships for normal projects:
  - `expenditure <= funds_released <= sanctioned_amount <= estimated_cost` with Gaussian noise introduced in physical progress tracking and disbursals.
- Implemented precise mathematical constraints for the 4 mutually exclusive anomaly categories:
  - `high_expenditure_low_progress`: `expenditure` = 80%–95% of `sanctioned_amount` while `current_progress_pct` = 5%–20%.
  - `expenditure_exceeds_sanction`: `expenditure` = 110%–150% of `sanctioned_amount` (`expenditure > sanctioned_amount`).
  - `severe_progress_mismatch`: `days_elapsed / project_duration_days` >= 0.85, `funds_released / sanctioned_amount` = 75%–90%, `current_progress_pct` < 15%, and `expenditure / sanctioned_amount` < 0.80.
  - `zero_progress_high_release`: `current_progress_pct` == 0%, `funds_released / sanctioned_amount` = 50%–85%, `expenditure / sanctioned_amount` > 40%, and `days_elapsed` > 100.
- Preserved ground-truth anomaly labels (`is_anomaly_injected`, `anomaly_type_injected`) purely for benchmark validation, strictly isolating them from model feature input sets.

### Why I did it
- **Ground-Truth Benchmarking:** Synthetic anomaly injection provides known positive/negative fraud labels to evaluate and tune unsupervised anomaly detection models (Isolation Forest / Risk Engine) without risking data leakage.
- **Mutual Exclusivity:** Ensuring non-overlapping anomaly rules eliminates ambiguity during rule-engine validation and metric evaluation.
- **Financial Realism:** Incorporating natural noise while maintaining fundamental accounting constraints (`expenditure <= funds_released <= sanctioned_amount` for normal projects) simulates real-world MoSPI MPLADS reporting dynamics.

### Verification
Executed automated data integrity and domain rule verification script (`scripts/generate_synthetic_data.py`):
- **Row count:** 500 rows verified (475 normal + 25 anomalies).
- **Anomaly count:** Exactly 25 anomalies (5.0%).
- **Anomaly distribution:** `severe_progress_mismatch`: 7, `expenditure_exceeds_sanction`: 6, `high_expenditure_low_progress`: 6, `zero_progress_high_release`: 6.
- **Missing values:** 0 missing values.
- **Duplicate project IDs:** 0 duplicates.
- **Negative monetary values:** 0 negative values.
- **Progress bounds:** All progress percentages strictly within [0, 100].
- **Days elapsed bounds:** Zero instances of `days_elapsed > project_duration_days`.
- **Sanction overrun check:** `expenditure > sanctioned_amount` occurred in exactly 6 rows (matching the `expenditure_exceeds_sanction` anomaly count).
- **Normal project constraints:** 0 violations of `expenditure <= funds_released <= sanctioned_amount`.
- **Mutual exclusivity:** 25/25 injected anomalies satisfied their intended category definition and belonged to exactly one category; 0 normal projects triggered any anomaly definition.

### Files Created/Modified
- `data/mock_mplads.csv` — Synthetic dataset (500 records).
- `scripts/generate_synthetic_data.py` — Reproducible generator and validation script.
- `Project_Progress_1.md` — Updated progress report.

---

## Checkpoint 3 — Data Validation & Guardrails

### What I Did
- Implemented the reusable data validation module `ml_modules/financial/data_validation.py` containing `FinancialDataValidator` and the `ValidationResult` dataclass.
- Built a comprehensive unit testing suite `tests/test_data_validation.py` covering 17 edge cases.
- Validated the 500-record synthetic dataset (`data/mock_mplads.csv`), confirming 100% structural validity and zero value mutation.

### How I Did It
- **Structural Validation Rules (`is_valid = False`):**
  - Mandatory presence and non-empty string check for `project_id`.
  - Type parsing and non-negativity checks for `estimated_cost`, `funds_released`, `expenditure`, and `days_elapsed`.
  - Strictly positive non-zero check for `sanctioned_amount > 0` (preventing division-by-zero errors in ratio calculations).
  - Strictly positive non-zero check for `project_duration_days > 0`.
  - Boundary constraint check `0 <= current_progress_pct <= 100`.
  - Timeline boundary check `0 <= days_elapsed <= project_duration_days`.
- **Financial Consistency Warnings (`is_valid = True`, `warnings` populated):**
  - `expenditure > sanctioned_amount` -> `"expenditure_exceeds_sanction"`
  - `expenditure > funds_released` -> `"expenditure_exceeds_funds_released"`
  - `funds_released > sanctioned_amount` -> `"funds_released_exceeds_sanction"`
  - `funds_released == 0` -> `"zero_funds_released"`
  - `current_progress_pct == 0` and (`expenditure > 0` or `funds_released > 0`) -> `"zero_progress_with_financial_activity"`
  - `expenditure / sanctioned_amount >= 0.80` and `5 <= current_progress_pct <= 20` -> `"high_expenditure_low_progress"`
  - `days_elapsed / project_duration_days >= 0.85`, `funds_released / sanctioned_amount >= 0.75`, `current_progress_pct <= 15` -> `"severe_progress_mismatch"`
- **Strict "No Value Mutation" Policy:**
  - Original input records are preserved without normalization, clipping, or silent data repair.

### Why I Did It
- **Downstream Protection:** Machine learning models (e.g. Isolation Forest) and numerical ratio transformations require clean, structurally sound inputs without negative costs or division-by-zero errors (`sanctioned_amount <= 0`).
- **Fraud Detection Integrity:** Genuine suspicious financial behavior (such as cost overruns or spending with zero progress) must NOT be filtered out or discarded by data validation. Marking these as valid records with warnings allows them to proceed to ML inference and rule engines for alert generation.

### Verification
- Executed `pytest tests/test_data_validation.py`: **17 / 17 tests PASSED**.
- Executed `validate_dataset(df)` on `data/mock_mplads.csv`:
  - **Total Records Checked:** 500
  - **Valid Records:** 500 (100.0%)
  - **Invalid Records:** 0
  - **Records with Warnings:** 25 (100% of injected anomalies flagged)
  - **Warning Distribution:** `expenditure_exceeds_sanction`: 6, `expenditure_exceeds_funds_released`: 7, `high_expenditure_low_progress`: 6, `severe_progress_mismatch`: 8, `zero_progress_with_financial_activity`: 6.

### Files Created/Modified
- `ml_modules/financial/data_validation.py` — Core validation module and dataclass structures.
- `tests/test_data_validation.py` — Pytest unit test suite (17 test cases).
- `Project_Progress_1.md` — Updated progress report.

### Important Design Decisions
- **`expenditure > sanctioned_amount` is suspicious, not invalid:** Cost overruns represent potential financial fraud/irregularity that must reach ML engines.
- **`expenditure > funds_released` is suspicious, not invalid:** Disbursal delays or unofficial vendor advances are key audit flags.
- **`funds_released > sanctioned_amount` is suspicious, not invalid:** Over-release of government funds requires flagging without data rejection.
- **`current_progress_pct == 0` is valid:** Projects with zero progress are legitimate initial state records or "ghost project" candidates.
- **Zero funds released handling:** `sanctioned_amount > 0` is enforced so ratio denominators are non-zero, while `funds_released == 0` triggers a zero disbursal warning without division errors.
- **Explicit Record Rejection:** Invalid records return `is_valid = False` with explicit error descriptions, preventing corrupted data from entering feature pipelines.

