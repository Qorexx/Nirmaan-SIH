"""
Checkpoint 8 — Unit Tests for End-to-End Financial Anomaly Inference Pipeline

Tests:
  1. normal project
  2. model-detected anomaly
  3. rule-only anomaly
  4. multi-signal anomaly
  5. invalid input rejected
  6. missing required field
  7. feature ordering verification
  8. anomaly score returned
  9. raw model prediction is diagnostic only
  10. variance_amount_inr remains None because expenditure is unavailable
"""

import os
import pytest
import numpy as np
import pandas as pd

from ml_modules.financial.inference import (
    FinancialAnomalyInferencePipeline,
    extract_project_identifier,
    validate_inference_record,
)
from ml_modules.financial.anomaly_rules import (
    RULE_LONG_DELAY,
    RULE_HIGH_SANCTION,
    RULE_EARLY_TENURE,
    RULE_MULTI_SIGNAL,
    RULE_MODEL_ANOMALY,
    RuleEngineConfig,
)


@pytest.fixture
def pipeline():
    return FinancialAnomalyInferencePipeline()


@pytest.fixture
def normal_record():
    return {
        "work_recommendation_dtl_id": 10001,
        "sanction_amount": 300000.0,
        "recommendation_date": "2024-09-01",
        "sanction_date": "2024-11-20",       # 80 days delay
        "tenure_start_date": "2023-09-01",   # 366 days elapsed
    }


# ── 1. Normal Project Test ──────────────────────────────────────────────────────
def test_normal_project(pipeline, normal_record):
    res = pipeline.predict_single_record(normal_record)
    assert res["project_identifier"] == "10001"
    assert res["is_anomalous"] is False
    assert res["anomaly_features"] == []
    assert res["anomaly_score"] is not None
    assert res["anomaly_score"] > -0.093716
    assert res["validation_errors"] == []
    assert res["variance_amount_inr"] is None


# ── 2. Model-Detected Anomaly Test ─────────────────────────────────────────────
def test_model_detected_anomaly(pipeline):
    # Record with feature values matching known top model anomaly (high amount, extreme delay)
    anomalous_rec = {
        "work_recommendation_dtl_id": 139500,
        "sanction_amount": 5000000.0,
        "recommendation_date": "2024-09-06",
        "sanction_date": "2026-07-31",      # 693 days delay
        "tenure_start_date": "2024-06-04",  # 94 days since tenure start
    }
    res = pipeline.predict_single_record(anomalous_rec)
    assert res["is_anomalous"] is True
    assert res["anomaly_score"] <= -0.093716
    assert len(res["anomaly_features"]) > 0


# ── 3. Rule-Only Anomaly Test ──────────────────────────────────────────────────
def test_rule_only_anomaly(pipeline, normal_record):
    rec = normal_record.copy()
    rec["sanction_date"] = "2025-08-01"  # 334 days delay (> 286 threshold)
    rec["sanction_amount"] = 300000.0    # Normal amount <= ₹11,98,014
    rec["tenure_start_date"] = "2022-01-01"  # > 113 days

    res = pipeline.predict_single_record(rec)
    assert res["is_anomalous"] is True
    assert RULE_LONG_DELAY in res["anomaly_features"]
    assert res["variance_amount_inr"] is None


# ── 4. Multi-Signal Anomaly Test ───────────────────────────────────────────────
def test_multi_signal_anomaly(pipeline):
    rec = {
        "work_recommendation_dtl_id": "MULTI_01",
        "sanction_amount": 5000000.0,         # > ₹11,98,014
        "recommendation_date": "2024-09-06",
        "sanction_date": "2026-07-31",        # 693 days delay (> 286)
        "tenure_start_date": "2024-06-04",    # 94 days (< 113)
    }
    res = pipeline.predict_single_record(rec)
    assert res["is_anomalous"] is True
    assert RULE_LONG_DELAY in res["anomaly_features"]
    assert RULE_HIGH_SANCTION in res["anomaly_features"]
    assert RULE_EARLY_TENURE in res["anomaly_features"]
    assert RULE_MULTI_SIGNAL in res["anomaly_features"]


# ── 5. Invalid Input Rejected Test ─────────────────────────────────────────────
def test_invalid_input_rejected(pipeline):
    bad_rec = {
        "work_recommendation_dtl_id": "BAD_01",
        "sanction_amount": -5000.0,           # Invalid negative cost
        "recommendation_date": "2024-09-01",
        "sanction_date": "2024-11-20",
        "tenure_start_date": "2023-09-01",
    }
    res = pipeline.predict_single_record(bad_rec)
    assert res["is_anomalous"] is False
    assert len(res["validation_errors"]) > 0
    assert "Field 'sanction_amount' must be a positive number > 0" in res["validation_errors"][0]
    assert res["anomaly_score"] is None


# ── 6. Missing Required Field Test ─────────────────────────────────────────────
def test_missing_required_field(pipeline):
    missing_rec = {
        "sanction_amount": 300000.0,
        "recommendation_date": "2024-09-01",
        # missing sanction_date and tenure_start_date
    }
    res = pipeline.predict_single_record(missing_rec)
    assert res["is_anomalous"] is False
    assert len(res["validation_errors"]) >= 2
    assert res["anomaly_score"] is None


# ── 7. Feature Ordering Verification Test ─────────────────────────────────────
def test_feature_ordering_verification(pipeline):
    assert pipeline.feature_names == [
        "log1p_sanction_amount",
        "rec_to_sanc_days",
        "days_since_tenure_start",
    ]


# ── 8. Anomaly Score Returned Test ──────────────────────────────────────────────
def test_anomaly_score_returned(pipeline, normal_record):
    res = pipeline.predict_single_record(normal_record)
    assert "anomaly_score" in res
    assert isinstance(res["anomaly_score"], float)


# ── 9. Raw Model Prediction is Diagnostic Only Test ────────────────────────────
def test_raw_model_prediction_is_diagnostic_only(pipeline, normal_record):
    res = pipeline.predict_single_record(normal_record)
    assert "model_prediction_for_diagnostics" in res
    assert res["model_prediction_for_diagnostics"] in [-1, 1]

    # Even if model_prediction_for_diagnostics is returned, decision function score governs model anomaly status
    if res["anomaly_score"] > -0.093716:
        assert RULE_MODEL_ANOMALY not in res["anomaly_features"]


# ── 10. Variance Amount INR Remains None Test ──────────────────────────────────
def test_variance_amount_inr_remains_none(pipeline, normal_record):
    res = pipeline.predict_single_record(normal_record)
    assert res["variance_amount_inr"] is None
    assert "variance_amount_inr" in res
