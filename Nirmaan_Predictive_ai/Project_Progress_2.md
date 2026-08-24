# MPLADS Early Warning & Decision Support System — Project Progress

**Role:** Person 2 — Predictive AI & Early Warning Lead  
**Project:** Nirmaan Predictive AI  
**Last Updated:** 2026-08-24

---

## 📋 Implementation Status

| Task | Description | Status |
|------|------------|--------|
| Task 1 | Synthetic Data Generator (`data_generator.py`) | ✅ Code Complete |
| Task 2 | XGBoost Models — Cost & Delay (`train_models.py`) | ✅ Code Complete |
| Task 3 | SHAP Explainer Utility (`shap_explainer.py`) | ✅ Code Complete |
| Task 4 | FastAPI Backend Endpoint (`api.py`) | ✅ Code Complete |
| Infra | Pipeline Runner, README, Requirements | ✅ Code Complete |
| Verify | Install deps, run pipeline, test API | ✅ Complete |

---

## 🏗️ Architecture

```
Nirmaan_Predictive_ai/
├── data/
│   └── synthetic_mplads_data.csv          # 5000 generated records
├── models/
│   ├── cost_model.joblib                  # XGBoost cost predictor
│   ├── delay_model.joblib                 # XGBoost delay predictor
│   └── preprocessor.joblib               # Shared ColumnTransformer
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

## 🎯 Design Decisions

### Data Generation (Task 1)
- **5,000 records** with 16 features matching real MPLADS eSAKSHI portal structure
- Causal relationships embedded: monsoon → delay, inflation → cost overrun, contractor history → both
- Indian states/UTs, realistic ₹5L–₹5Cr cost range, 10 MPLADS project categories
- Targets generated with controlled noise for realistic model performance

### Predictive Models (Task 2)
- **Model A:** `XGBRegressor` → `actual_final_cost` (derive cost overrun = predicted - sanctioned)
- **Model B:** `XGBRegressor` → `actual_delay_days`
- 80/20 train-test split, evaluation via RMSE, MAE, R²
- Categorical encoding via `OrdinalEncoder` in `ColumnTransformer`

### Explainability (Task 3)
- `shap.TreeExplainer` for XGBoost-native SHAP values
- Returns top-3 human-readable factor names ranked by |SHAP value|
- Separate calls for cost and delay models

### API Contract (Task 4)
- `POST /api/v1/predict-early-warning`
- JSON output matches Person 6's exact schema specification
- **5 actionable trigger rules** with RED/AMBER severity:

| Condition | Alert Type | Severity |
|-----------|-----------|----------|
| `delay > 20% × expected_duration` | `TIME_WARNING` | 🔴 RED |
| `delay > 10% × expected_duration` | `TIME_WARNING` | 🟡 AMBER |
| `cost_overrun > 15% × sanctioned` | `COST_ESCALATION` | 🔴 RED |
| `cost_overrun > 5% × sanctioned` | `COST_ESCALATION` | 🟡 AMBER |
| `progress < 40%` AND `elapsed > 60% expected` | `STALLED_PROJECT` | 🔴 RED |

---

## 📊 Model Metrics

> Metrics populated from training run on 5000 synthetic records (80/20 train/test split).

### Cost Model (Model A)
| Metric | Value |
|--------|-------|
| RMSE | 1,082,012.90 |
| MAE | 793,419.03 |
| R² | 0.9968 |

### Delay Model (Model B)
| Metric | Value |
|--------|-------|
| RMSE | 16.56 |
| MAE | 13.10 |
| R² | 0.7092 |

---

## 🔄 Change Log

| Date | Change | Files Affected |
|------|--------|---------------|
| 2026-08-24 | Initial implementation of all 4 tasks | All files created |

