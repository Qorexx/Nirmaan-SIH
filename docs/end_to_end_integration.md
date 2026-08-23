# End-to-End Financial Anomaly Integration — Checkpoint 11

**Project:** SIH 2026 — Problem Statement SIH26102  
**Engineer:** Person 1 (Financial AI / Anomaly Detection Engine)  
**Checkpoint:** 11 — End-to-End Integration  
**Status:** ✅ 113/113 tests passing

---

## 1. Architecture

```
┌────────────────────────────────────────────────────────┐
│                 DATA SOURCE LAYER                      │
│   PostgreSQL DB  ──► PostgreSQLDataLoader              │
│   (read-only)        normalize_db_record()             │
└─────────────────────────┬──────────────────────────────┘
                          │  normalized record dict
                          ▼
┌────────────────────────────────────────────────────────┐
│              ML INFERENCE LAYER                        │
│   FinancialAnomalyInferencePipeline                    │
│   ├─ validate_inference_record()                       │
│   ├─ Feature Derivation:                               │
│   │   log1p_sanction_amount                            │
│   │   rec_to_sanc_days                                 │
│   │   days_since_tenure_start                          │
│   ├─ Isolation Forest (200 trees, n=73,789)            │
│   │   anomaly_score  (continuous)                      │
│   │   approved cutoff: score <= -0.093716              │
│   └─ Explainable Rule Engine                           │
│       RULE_LONG_DELAY (>286 days)                      │
│       RULE_HIGH_SANCTION (>₹11,98,014)                 │
│       RULE_EARLY_TENURE (<113 days)                    │
│       RULE_MULTI_SIGNAL (≥2 rules + model)             │
│       RULE_MODEL_ANOMALY (score only, no domain rules) │
└─────────────────────────┬──────────────────────────────┘
                          │  inference result dict
                          ▼
┌────────────────────────────────────────────────────────┐
│              ALERT DELIVERY LAYER                      │
│   build_financial_anomaly_payload()                    │
│   FinancialAlertClient.send_alert()                    │
│   POST /api/v1/financial-anomalies                     │
└────────────────────────────────────────────────────────┘
```

---

## 2. Data Flow

### Input (PostgreSQL row, normalized)
| Field | Source | Notes |
|-------|--------|-------|
| `work_recommendation_dtl_id` | DB `id` column | Project identifier |
| `sanction_amount` | DB `sanctioned_amount` | INR |
| `recommendation_date` | DB `start_date` | Date of MP's recommendation |
| `sanction_date` | DB `sanction_date` | Date of sanctioned approval |
| `tenure_start_date` | DB `tenure_start_date` | Start of MP's tenure |
| `expenditure` | **ABSENT** | Always `None` — not in DB snapshot |
| `funds_released` | **ABSENT** | Always `None` — not in DB snapshot |
| `physical_progress_pct` | **ABSENT** | Always `None` — not in DB snapshot |
| `pfms_status` | **ABSENT** | Always `None` — not in DB snapshot |
| `transaction_type` | **ABSENT** | Always `None` — not in DB snapshot |

### Feature Derivation (inside pipeline)
```
log1p_sanction_amount  = log(1 + sanction_amount)
rec_to_sanc_days       = sanction_date - recommendation_date  (days)
days_since_tenure_start = recommendation_date - tenure_start_date  (days)
```

### Inference Output Schema
```json
{
  "project_identifier": "141814",
  "is_anomalous": true,
  "anomaly_features": ["early_tenure_recommendation"],
  "anomaly_score": -0.002613,
  "model_prediction_for_diagnostics": -1,
  "feature_values": {
    "sanction_amount": 100000.0,
    "log1p_sanction_amount": 11.5129,
    "rec_to_sanc_days": 50.0,
    "days_since_tenure_start": 107.0
  },
  "validation_errors": [],
  "validation_warnings": [],
  "variance_amount_inr": null
}
```

### Backend Payload (POST body)
```json
{
  "project_id": "141814",
  "is_anomalous": true,
  "anomaly_features": ["early_tenure_recommendation"],
  "variance_amount_inr": null
}
```

---

## 3. Real Database Verification

**Status: DATABASE UNAVAILABLE (no PostgreSQL configured in local dev)**

When `DATABASE_URL` is not set:
```
DATABASE UNAVAILABLE
Could not connect to the database: No database URI or active connection provided.
Set DATABASE_URL environment variable.
```

The runner exits with code 1 — it does NOT fabricate success.

To connect a real PostgreSQL database:
```bash
export DATABASE_URL="postgresql://user:password@localhost:5432/mplads"
PYTHONPATH=. .venv/bin/python scripts/run_financial_pipeline.py --project-id 141814
```

---

## 4. ML Inference Verification

**Status: VERIFIED — using real official dataset (mplads_projects.csv)**

Live inference was run on real project record `141814.0` from the official MPLADS dataset:

```
Project ID : 141814.0
Sanction   : Rs 100,000
Rec Date   : 2024-09-19
Sanc Date  : 2024-11-08
Tenure     : 2024-06-04

rec_to_sanc_days       : 50
days_since_tenure      : 107
anomaly_score          : -0.002613
model_pred (diag)      : -1    ← raw prediction (diagnostic only)
rule_tags              : ['early_tenure_recommendation']
is_anomalous           : True  ← rule triggered despite score above cutoff
variance_amount_inr    : None  ← NOT fabricated
```

**Key observation:** The raw model prediction is `-1` but the anomaly score (`-0.002613`) is **above** the approved cutoff (`-0.093716`). The model anomaly flag is `False`. However, the `early_tenure_recommendation` domain rule fired (107 days < 113 threshold), making `is_anomalous = True`. This demonstrates that `model_prediction_for_diagnostics` is **never** the final arbiter.

---

## 5. Backend Verification

**Status: NOT TESTED (backend server not running during Checkpoint 11 verification)**

The `--send-alert` flag is opt-in. Without it, no HTTP request is made.

To test backend integration (requires FastAPI running):
```bash
# Terminal 1: Start backend
PYTHONPATH=. .venv/bin/uvicorn main:app --reload

# Terminal 2: Send real inference result
PYTHONPATH=. .venv/bin/python scripts/run_financial_pipeline.py \
    --project-id 141814 --send-alert
```

If backend is unavailable, the runner prints:
```
BACKEND UNAVAILABLE
  Error: Network error connecting to backend: ...
  Ensure the FastAPI server is running at: http://localhost:8000
  Start it with: PYTHONPATH=. .venv/bin/uvicorn main:app --reload
```
And exits with code 2.

---

## 6. Example Normal Result

```
────────────────────────────────────────────────────────────
  PROJECT #1  |  ID: PROJ-NORMAL-001
────────────────────────────────────────────────────────────
  Sanction Amount (INR)       : Rs 350,000.00
  Rec to Sanction Days        : 80 days
  Days Since Tenure Start     : 366 days
  Anomaly Score               : 0.048512  (cutoff: -0.093716)
  Raw Model Prediction (diag) : NORMAL (1)
  Model Anomaly (score-based) : NO
  Rule Tags                   : (none)
  Final is_anomalous          : [NORMAL]
  variance_amount_inr         : null  (expenditure unavailable -- not fabricated)
────────────────────────────────────────────────────────────
```

**Backend payload:**
```json
{
  "project_id": "PROJ-NORMAL-001",
  "is_anomalous": false,
  "anomaly_features": [],
  "variance_amount_inr": null
}
```

---

## 7. Example Anomaly Result

```
────────────────────────────────────────────────────────────
  PROJECT #1  |  ID: PROJ-ANOMALY-001
────────────────────────────────────────────────────────────
  Sanction Amount (INR)       : Rs 5,000,000.00
  Rec to Sanction Days        : 693 days
  Days Since Tenure Start     : 94 days
  Anomaly Score               : -0.237589  (cutoff: -0.093716)
  Raw Model Prediction (diag) : ANOMALY (-1)
  Model Anomaly (score-based) : YES
  Rule Tags                   : unusually_long_recommendation_to_sanction_delay,
                                unusually_high_sanction_amount,
                                early_tenure_recommendation,
                                multi_signal_statistical_anomaly
  Final is_anomalous          : *** ANOMALOUS ***
  variance_amount_inr         : null  (expenditure unavailable -- not fabricated)
────────────────────────────────────────────────────────────
```

**Backend payload:**
```json
{
  "project_id": "PROJ-ANOMALY-001",
  "is_anomalous": true,
  "anomaly_features": [
    "unusually_long_recommendation_to_sanction_delay",
    "unusually_high_sanction_amount",
    "early_tenure_recommendation",
    "multi_signal_statistical_anomaly"
  ],
  "variance_amount_inr": null
}
```

---

## 8. Missing Financial Signals

The official MPLADS snapshot does **not** provide:

| Missing Field | Reason | Handling |
|---------------|--------|----------|
| `expenditure` | Not in DB export | Set to `None` — never fabricated |
| `funds_released` | Not in DB export | Set to `None` — never fabricated |
| `physical_progress_pct` | Not in DB export | Set to `None` — never fabricated |
| `pfms_status` | Not in DB export | Set to `None` — never fabricated |
| `transaction_type` | Not in DB export | Set to `None` — never fabricated |
| `variance_amount_inr` | Computed from missing fields | Always `null` in output |

**The rule engine and Isolation Forest operate exclusively on available features:**
- `log1p_sanction_amount` (from `sanctioned_amount`)
- `rec_to_sanc_days` (derived from `recommendation_date` and `sanction_date`)
- `days_since_tenure_start` (derived from `recommendation_date` and `tenure_start_date`)

---

## 9. Failure Handling

| Failure Scenario | Behavior | Exit Code |
|-----------------|----------|-----------|
| PostgreSQL unavailable | Prints `DATABASE UNAVAILABLE`, exits cleanly | 1 |
| Project ID not found | Prints `not found in the database`, exits cleanly | 1 |
| DB query error | Prints `DATABASE QUERY FAILED`, exits cleanly | 1 |
| Invalid record (validation fails) | Returns `is_anomalous: False` with `validation_errors` populated | 0 (pipeline continues) |
| Backend unavailable (--send-alert) | Prints `BACKEND UNAVAILABLE`, exits cleanly | 2 |
| Backend returns HTTP error (--send-alert) | Prints `Backend returned HTTP {code}`, exits cleanly | 3 |

---

## 10. How to Run the Demo

### Prerequisites
```bash
# Activate virtual environment
source .venv/bin/activate  # or: .venv/bin/python ...

# Ensure model exists
ls models/financial_isolation_forest.pkl

# Set DB connection (if PostgreSQL is available)
export DATABASE_URL="postgresql://user:password@localhost:5432/mplads"
```

### Run inference on a single project (inference only, no HTTP)
```bash
PYTHONPATH=. .venv/bin/python scripts/run_financial_pipeline.py --project-id 141814
```

### Run inference on a small batch (no HTTP)
```bash
PYTHONPATH=. .venv/bin/python scripts/run_financial_pipeline.py --limit 5
```

### Run inference + send alert to backend
```bash
# Start backend first:
PYTHONPATH=. .venv/bin/uvicorn main:app --reload

# Then in another terminal:
PYTHONPATH=. .venv/bin/python scripts/run_financial_pipeline.py \
    --project-id 141814 --send-alert
```

### Use a custom backend URL
```bash
PYTHONPATH=. .venv/bin/python scripts/run_financial_pipeline.py \
    --project-id 141814 --send-alert --backend-url http://192.168.1.100:8000
```

### Run all tests
```bash
PYTHONPATH=. .venv/bin/pytest tests/ -v
```

### Run only end-to-end tests
```bash
PYTHONPATH=. .venv/bin/pytest tests/test_end_to_end.py -v
```

---

## Files Created in Checkpoint 11

| File | Purpose |
|------|---------|
| `scripts/run_financial_pipeline.py` | Integration runner (CLI tool) |
| `tests/test_end_to_end.py` | 36-test end-to-end test suite |
| `docs/end_to_end_integration.md` | This document |

## Files NOT Modified

- `main.py` — unchanged
- `schemas.py` — unchanged
- `models/financial_isolation_forest.pkl` — unchanged
- All `ml_modules/financial/*.py` — unchanged
- Database schema — not touched

---

*Checkpoint 11 Complete — End-to-End Financial Anomaly Integration*
