"""
Checkpoint 10 — Unit Tests for Backend Contract Resolution & Schema Compatibility

Tests:
  1. valid float variance is accepted
  2. null variance is accepted
  3. anomaly payload with null variance is accepted
  4. existing backend schema behavior remains unchanged otherwise
  5. ML client payload with variance_amount_inr=None is compatible
  6. Pydantic validation test proving exact JSON payload with null variance is accepted
"""

import json
import pytest
from pydantic import ValidationError

from schemas import (
    FinancialAnomalyPayload,
    PredictiveDelayPayload,
    DuplicateDetectionPayload,
    ComplianceAlert,
    FrontendProjectDashboard,
)
from rules_engine import generate_financial_alerts
from ml_modules.financial.send_alert import build_financial_anomaly_payload


# ── 1. Valid Float Variance Accepted ───────────────────────────────────────────
def test_valid_float_variance_accepted():
    payload = FinancialAnomalyPayload(
        project_id="PROJ-001",
        is_anomalous=True,
        anomaly_features=["unusually_high_sanction_amount"],
        variance_amount_inr=1500000.0,
    )
    assert payload.project_id == "PROJ-001"
    assert payload.is_anomalous is True
    assert payload.variance_amount_inr == 1500000.0


# ── 2. Null Variance Accepted ──────────────────────────────────────────────────
def test_null_variance_accepted():
    payload = FinancialAnomalyPayload(
        project_id="PROJ-002",
        is_anomalous=True,
        anomaly_features=["unusually_long_recommendation_to_sanction_delay"],
        variance_amount_inr=None,
    )
    assert payload.project_id == "PROJ-002"
    assert payload.is_anomalous is True
    assert payload.variance_amount_inr is None


# ── 3. Anomaly Payload with Null Variance Accepted ─────────────────────────────
def test_anomaly_payload_with_null_variance_accepted():
    payload = FinancialAnomalyPayload(
        project_id="PROJ-003",
        is_anomalous=True,
        anomaly_features=["unusually_long_recommendation_to_sanction_delay", "early_tenure_recommendation"],
        variance_amount_inr=None,
    )
    alerts = generate_financial_alerts(payload)
    assert len(alerts) == 1
    assert alerts[0].type == "FINANCIAL_DEVIATION"
    assert "Variance: N/A" in alerts[0].message


# ── 4. Existing Backend Schema Behavior Remains Unchanged ──────────────────────
def test_existing_backend_schema_behavior_unchanged():
    # Default behavior without passing variance_amount_inr defaults to None
    payload_default = FinancialAnomalyPayload(
        project_id="PROJ-DEFAULT",
        is_anomalous=False,
        anomaly_features=[],
    )
    assert payload_default.variance_amount_inr is None

    # Other schemas behavior
    pred_payload = PredictiveDelayPayload(
        project_id="P-PRED",
        predicted_delay_days=45,
        predicted_cost_overrun_inr=500000.0,
        shap_key_drivers=["delay"],
    )
    assert pred_payload.predicted_delay_days == 45


# ── 5. ML Client Payload Compatibility ─────────────────────────────────────────
def test_ml_client_payload_compatibility():
    inference_result = {
        "project_identifier": "139500",
        "is_anomalous": True,
        "anomaly_features": ["unusually_long_recommendation_to_sanction_delay"],
        "anomaly_score": -0.237589,
        "variance_amount_inr": None,
    }
    raw_payload_dict = build_financial_anomaly_payload(inference_result)

    # Validate dict against Pydantic schema
    pydantic_payload = FinancialAnomalyPayload(**raw_payload_dict)
    assert pydantic_payload.project_id == "139500"
    assert pydantic_payload.is_anomalous is True
    assert pydantic_payload.variance_amount_inr is None


# ── 6. Pydantic JSON Deserialization Contract Test ─────────────────────────────
def test_pydantic_json_deserialization_contract():
    json_str = json.dumps({
        "project_id": "test-project",
        "is_anomalous": True,
        "anomaly_features": [
            "unusually_long_recommendation_to_sanction_delay"
        ],
        "variance_amount_inr": None
    })

    # Pydantic v1 / v2 compatible JSON parse
    if hasattr(FinancialAnomalyPayload, "model_validate_json"):
        payload = FinancialAnomalyPayload.model_validate_json(json_str)
    else:
        payload = FinancialAnomalyPayload.parse_raw(json_str)

    assert payload.project_id == "test-project"
    assert payload.is_anomalous is True
    assert payload.anomaly_features == ["unusually_long_recommendation_to_sanction_delay"]
    assert payload.variance_amount_inr is None
