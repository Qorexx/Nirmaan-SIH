# MPLADS Early Warning & Decision Support System

**Person 2 — Predictive AI & Early Warning Lead**

A production-grade predictive backend that outputs **tangible business forecasts** (predicted delay days, cost overrun in ₹), **SHAP explanations**, and **actionable alert triggers** for MPLADS project monitoring.

> ⚠️ **No abstract risk scores.** This system outputs exact values that government officials can act on.

---

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Full pipeline: generate data → train models → start API
python run_pipeline.py

# API will be available at http://localhost:8000
# Swagger docs at http://localhost:8000/docs
```

---

## Architecture

```
Nirmaan_Predictive_ai/
├── data/synthetic_mplads_data.csv    # 5,000 synthetic MPLADS records
├── models/
│   ├── cost_model.joblib             # XGBoost cost predictor
│   ├── delay_model.joblib            # XGBoost delay predictor
│   ├── preprocessor.joblib           # Shared ColumnTransformer
│   └── feature_names.joblib          # Feature name list
├── src/
│   ├── data_generator.py             # Task 1: Synthetic data
│   ├── train_models.py               # Task 2: Model training
│   ├── shap_explainer.py             # Task 3: SHAP utility
│   └── api.py                        # Task 4: FastAPI backend
├── run_pipeline.py                   # One-click orchestrator
├── requirements.txt
└── README.md
```

---

## API Usage

### Endpoint: `POST /api/v1/predict-early-warning`

**Request:**
```bash
curl -X POST http://localhost:8000/api/v1/predict-early-warning \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "MPLADS-1234",
    "state": "Uttar Pradesh",
    "constituency_type": "LOK_SABHA",
    "project_category": "Roads",
    "estimated_cost": 2500000,
    "sanctioned_amount": 2400000,
    "expected_duration_days": 365,
    "elapsed_days": 280,
    "progress_pct": 35.0,
    "contractor_id": "CTR-042",
    "contractor_past_delays": 8,
    "monsoon_overlap_days": 90,
    "material_inflation_index": 1.22,
    "labor_shortage_index": 0.7,
    "terrain_difficulty": "HILLY",
    "sanction_year": 2024
  }'
```

**Response:**
```json
{
  "project_id": "MPLADS-1234",
  "forecasts": {
    "predicted_delay_days": 45,
    "predicted_cost_overrun_amount": 1500000,
    "predicted_final_cost": 3500000
  },
  "explanations": {
    "top_delay_factors": ["contractor_past_delays", "monsoon_overlap_days", "labor_shortage_index"],
    "top_cost_factors": ["material_inflation_index", "terrain_difficulty", "estimated_cost"]
  },
  "actionable_triggers": [
    {
      "type": "TIME_WARNING",
      "severity": "RED",
      "threshold_violated": ">20% timeline buffer exceeded",
      "message": "Project forecasted to be 45 days late. Initiate physical inspection."
    }
  ]
}
```

---

## Actionable Trigger Rules

| Condition | Alert Type | Severity |
|-----------|-----------|----------|
| Predicted delay > 20% of expected duration | `TIME_WARNING` | 🔴 RED |
| Predicted delay > 10% of expected duration | `TIME_WARNING` | 🟡 AMBER |
| Cost overrun > 15% of sanctioned amount | `COST_ESCALATION` | 🔴 RED |
| Cost overrun > 5% of sanctioned amount | `COST_ESCALATION` | 🟡 AMBER |
| Progress < 40% but elapsed > 60% of expected | `STALLED_PROJECT` | 🔴 RED |

---

## Pipeline Options

```bash
# Generate + train only (no server)
python run_pipeline.py --no-serve

# Start server only (models must exist)
python run_pipeline.py --serve-only

# Custom record count and port
python run_pipeline.py --records 10000 --port 8080
```

---

## Integration Notes for Person 6 (Backend Lead)

- **CORS** is enabled for all origins — adjust in `src/api.py` for production.
- **Health check** available at `GET /health`.
- Models are loaded once at startup via FastAPI's `lifespan` context manager.
- All monetary values are in **₹ (Indian Rupees)**, not lakhs/crores.
- The `contractor_id` field is accepted but not used as a model feature (it's an identifier, not a predictor). The model uses `contractor_past_delays` instead.

---

## Tech Stack

- **ML:** XGBoost, scikit-learn, SHAP
- **API:** FastAPI, Pydantic, Uvicorn
- **Data:** pandas, numpy
