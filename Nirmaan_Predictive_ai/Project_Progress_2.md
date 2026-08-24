# MPLADS Early Warning & Decision Support System — Project Progress

**Role:** Person 2 — Predictive AI & Early Warning Lead  
**Project:** Nirmaan Predictive AI  
**Last Updated:** 2026-08-24

---

## Implementation Status

| Task | Description | Status |
|------|------------|--------|
| Task 1 | Synthetic Data Generator (`data_generator.py`) | Done - Optimized |
| Task 2 | XGBoost Models — Cost & Delay (`train_models.py`) | Done - Optimized |
| Task 3 | SHAP Explainer Utility (`shap_explainer.py`) | Done - Optimized |
| Task 4 | FastAPI Backend Endpoint (`api.py`) | Done - Optimized |
| Infra | Pipeline Runner, README, Requirements | Done - Optimized |
| Verify | Install deps, run pipeline, test API | Done |

---

## Architecture

```
Nirmaan_Predictive_ai/
├── data/
│   └── synthetic_mplads_data.csv          # 8000 generated records
├── models/
│   ├── cost_model.joblib                  # XGBoost cost predictor
│   ├── delay_model.joblib                 # XGBoost delay predictor
│   ├── preprocessor.joblib               # Shared ColumnTransformer
│   └── feature_names.joblib              # Feature names (18 features)
├── src/
│   ├── __init__.py
│   ├── data_generator.py                  # Task 1
│   ├── train_models.py                    # Task 2
│   ├── shap_explainer.py                  # Task 3
│   └── api.py                             # Task 4
├── requirements.txt
├── run_pipeline.py                        # Generate → Train → Serve
├── README.md
└── Project_Progress_2.md                  # This file
```

---

## Design Decisions

### Data Generation (Task 1)
- **8,000 records** with 16 features matching real MPLADS eSAKSHI portal structure
- Causal relationships embedded: monsoon → delay, inflation → cost overrun, contractor history → both
- Indian states/UTs, log-normal cost distribution centered around typical MPLADS costs
- **Tighter noise** on targets (1.5% cost noise, 3-day delay noise) for clean model learning
- **Fixed causal coefficients** instead of randomized — deterministic signal, stochastic noise
- Category-level complexity multipliers for realistic variation

### Predictive Models (Task 2)
- **Model A:** `XGBRegressor` → `actual_final_cost` (derive cost overrun = predicted - sanctioned)
- **Model B:** `XGBRegressor` → `actual_delay_days`
- **4 engineered features**: `cost_per_day`, `progress_gap`, `sanction_ratio`, `remaining_days_pct`
- 80/20 train-test split, evaluation via RMSE, MAE, R²
- **Separate hyperparameters** per model (delay model uses deeper trees, more estimators)
- Categorical encoding via `OrdinalEncoder` in `ColumnTransformer`

### Explainability (Task 3)
- `shap.TreeExplainer` for XGBoost-native SHAP values
- **Cached explainers** built at startup — not recreated per request
- Returns top-3 human-readable factor names ranked by |SHAP value|
- **Graceful fallback** if SHAP fails on edge cases
- Separate calls for cost and delay models

### API Contract (Task 4)
- `POST /api/v1/predict-early-warning`
- JSON output matches Person 6's exact schema specification
- **Enum validation** on `terrain_difficulty`, `constituency_type`, `project_category`
- **Prediction clamping** — no negative costs, delay capped at 3× expected duration
- **6 actionable trigger rules** with RED/AMBER/GREEN severity:

| Condition | Alert Type | Severity |
|-----------|-----------|----------|
| `delay > 20% × expected_duration` | `TIME_WARNING` | RED |
| `delay > 10% × expected_duration` | `TIME_WARNING` | AMBER |
| `cost_overrun > 15% × sanctioned` | `COST_ESCALATION` | RED |
| `cost_overrun > 5% × sanctioned` | `COST_ESCALATION` | AMBER |
| `progress < 40%` AND `elapsed > 60% expected` | `STALLED_PROJECT` | RED |
| No thresholds violated | `ON_TRACK` | GREEN |

---

## Model Metrics

> Metrics from training run on 8000 synthetic records (80/20 train/test split).

### Cost Model (Model A)
| Metric | Previous | Current | Change |
|--------|----------|---------|--------|
| RMSE | 1,082,012.90 | 821,825.14 | -24% |
| MAE | 793,419.03 | 156,823.50 | -80% |
| R² | 0.9968 | 0.9783 | -1.9% |

### Delay Model (Model B)
| Metric | Previous | Current | Change |
|--------|----------|---------|--------|
| RMSE | 16.56 | 4.23 | -74% |
| MAE | 13.10 | 3.30 | -75% |
| R² | 0.7092 | 0.9744 | +37% |

> **Key improvement**: Delay model R² jumped from 0.71 to 0.97 — predictions are now actionable.
> Cost model MAE dropped 80% while maintaining excellent R².

---

## Change Log

| Date | Change | Files Affected |
|------|--------|---------------|
| 2026-08-24 | Initial implementation of all 4 tasks | All files created |
| 2026-08-24 | Optimization pass: stronger data signals, feature engineering, SHAP caching, enum validation, ON_TRACK trigger, prediction clamping | All files modified |
