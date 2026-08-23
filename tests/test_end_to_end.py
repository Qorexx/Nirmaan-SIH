"""
Checkpoint 11 — End-to-End Integration Tests for Financial Anomaly Pipeline

Tests the complete logical chain using mocks where live infrastructure is unavailable:

  loader → inference → rule engine → alert payload

Tests:
  1.  Full pipeline: loader → normalize → inference (normal record)
  2.  Full pipeline: loader → normalize → inference (anomaly record)
  3.  Project identifier preserved through pipeline
  4.  Sanction amount preserved through pipeline
  5.  Feature values (rec_to_sanc_days, days_since_tenure_start) generated correctly
  6.  Anomaly score generated (float, not None)
  7.  anomaly_features generated (list)
  8.  is_anomalous generated (bool)
  9.  variance_amount_inr remains None throughout (NOT fabricated)
  10. Alert payload is backend-compatible (validates against FinancialAnomalyPayload schema)
  11. Raw model prediction does NOT control final is_anomalous (score cutoff governs)
  12. PostgreSQL loader returns None for missing record (mock)
  13. PostgreSQL loader raises ConnectionError on unavailable DB
  14. Loader absent fields remain None after normalize (no fabrication)
  15. Multi-stage chain: mock DB → normalize → inference → payload
  16. Batch loader processes multiple records correctly (mock)
  17. Alert client sends correct payload shape to backend
  18. Alert client preserves variance_amount_inr=None in HTTP payload
  19. Backend unavailability detected cleanly (no exception escape)
  20. Rule tags match expected pattern for known anomaly features
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch
import pytest

from ml_modules.financial.data_loader import (
    PostgreSQLDataLoader,
    normalize_db_record,
)
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
    DEFAULT_MODEL_SCORE_CUTOFF,
)
from ml_modules.financial.send_alert import (
    FinancialAlertClient,
    build_financial_anomaly_payload,
)
from schemas import FinancialAnomalyPayload


# ──────────────────────────────────────────────────────────────────────────────
# Shared fixtures
# ──────────────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def pipeline():
    """Shared FinancialAnomalyInferencePipeline instance — loads model once."""
    return FinancialAnomalyInferencePipeline()


@pytest.fixture
def normal_db_row():
    """Simulated PostgreSQL row for a typical (normal) project."""
    return {
        "id": "PROJ-NORMAL-001",
        "sanctioned_amount": 350000.0,
        "start_date": "2024-09-01",
        "sanction_date": "2024-11-20",      # 80 days delay — normal
        "tenure_start_date": "2023-09-01",  # 366 days since tenure — normal
        "district_authority": "JAIPUR",
        "category": "DRINKING_WATER",
    }


@pytest.fixture
def anomaly_db_row():
    """Simulated PostgreSQL row for a known anomalous project."""
    return {
        "id": "PROJ-ANOMALY-001",
        "sanctioned_amount": 5000000.0,
        "start_date": "2024-09-06",
        "sanction_date": "2026-07-31",      # 693 days delay — extreme
        "tenure_start_date": "2024-06-04",  # 94 days since tenure — early
        "district_authority": "MUMBAI NORTH",
        "category": "ROAD",
    }


@pytest.fixture
def normal_record(normal_db_row):
    """Normalized record from normal DB row."""
    return normalize_db_record(normal_db_row)


@pytest.fixture
def anomaly_record(anomaly_db_row):
    """Normalized record from anomaly DB row."""
    return normalize_db_record(anomaly_db_row)


# ──────────────────────────────────────────────────────────────────────────────
# 1. Full pipeline: loader → normalize → inference (normal record)
# ──────────────────────────────────────────────────────────────────────────────

def test_full_pipeline_normal_record(pipeline, normal_record):
    """Complete chain from normalized DB record to inference result — normal project."""
    result = pipeline.predict_single_record(normal_record)

    assert isinstance(result, dict)
    assert result["is_anomalous"] is False
    assert result["validation_errors"] == []
    assert result["anomaly_score"] is not None
    assert isinstance(result["anomaly_score"], float)


# ──────────────────────────────────────────────────────────────────────────────
# 2. Full pipeline: loader → normalize → inference (anomaly record)
# ──────────────────────────────────────────────────────────────────────────────

def test_full_pipeline_anomaly_record(pipeline, anomaly_record):
    """Complete chain from normalized DB record to inference result — anomalous project."""
    result = pipeline.predict_single_record(anomaly_record)

    assert isinstance(result, dict)
    assert result["is_anomalous"] is True
    assert len(result["anomaly_features"]) > 0
    assert result["validation_errors"] == []


# ──────────────────────────────────────────────────────────────────────────────
# 3. Project identifier preserved through pipeline
# ──────────────────────────────────────────────────────────────────────────────

def test_project_identifier_preserved(pipeline, normal_record):
    """The project_identifier in inference result must match the source DB ID."""
    result = pipeline.predict_single_record(normal_record)
    # normalize_db_record maps "id" → "work_recommendation_dtl_id"
    assert result["project_identifier"] == "PROJ-NORMAL-001"


def test_project_identifier_preserved_anomaly(pipeline, anomaly_record):
    result = pipeline.predict_single_record(anomaly_record)
    assert result["project_identifier"] == "PROJ-ANOMALY-001"


# ──────────────────────────────────────────────────────────────────────────────
# 4. Sanction amount preserved through pipeline
# ──────────────────────────────────────────────────────────────────────────────

def test_sanction_amount_preserved(pipeline, normal_record):
    """sanction_amount in feature_values must match the value in the DB row."""
    result = pipeline.predict_single_record(normal_record)
    fv = result["feature_values"]
    assert fv is not None
    assert fv["sanction_amount"] == pytest.approx(350000.0, rel=1e-6)


def test_sanction_amount_preserved_anomaly(pipeline, anomaly_record):
    result = pipeline.predict_single_record(anomaly_record)
    fv = result["feature_values"]
    assert fv is not None
    assert fv["sanction_amount"] == pytest.approx(5000000.0, rel=1e-6)


# ──────────────────────────────────────────────────────────────────────────────
# 5. Feature values generated correctly
# ──────────────────────────────────────────────────────────────────────────────

def test_feature_values_generated_correctly(pipeline, normal_record):
    """rec_to_sanc_days and days_since_tenure_start must be computed, not None."""
    result = pipeline.predict_single_record(normal_record)
    fv = result["feature_values"]

    assert fv is not None
    assert "rec_to_sanc_days" in fv
    assert "days_since_tenure_start" in fv
    assert isinstance(fv["rec_to_sanc_days"], float)
    assert isinstance(fv["days_since_tenure_start"], float)

    # 2024-09-01 to 2024-11-20 = 80 days
    assert fv["rec_to_sanc_days"] == pytest.approx(80.0, abs=1.0)
    # 2024-09-01 minus 2023-09-01 = 366 days (2024 is leap year)
    assert fv["days_since_tenure_start"] == pytest.approx(366.0, abs=1.0)


def test_anomaly_feature_values_generated_correctly(pipeline, anomaly_record):
    result = pipeline.predict_single_record(anomaly_record)
    fv = result["feature_values"]
    assert fv is not None
    # 2024-09-06 to 2026-07-31 = 693 days
    assert fv["rec_to_sanc_days"] == pytest.approx(693.0, abs=1.0)
    # 2024-09-06 minus 2024-06-04 = 94 days
    assert fv["days_since_tenure_start"] == pytest.approx(94.0, abs=1.0)


# ──────────────────────────────────────────────────────────────────────────────
# 6. Anomaly score generated (float, not None)
# ──────────────────────────────────────────────────────────────────────────────

def test_anomaly_score_generated(pipeline, normal_record):
    result = pipeline.predict_single_record(normal_record)
    assert result["anomaly_score"] is not None
    assert isinstance(result["anomaly_score"], float)
    # Score must be a finite float (no NaN/inf from model)
    import math
    assert math.isfinite(result["anomaly_score"])


# ──────────────────────────────────────────────────────────────────────────────
# 7. anomaly_features generated (list)
# ──────────────────────────────────────────────────────────────────────────────

def test_anomaly_features_is_list(pipeline, normal_record):
    result = pipeline.predict_single_record(normal_record)
    assert isinstance(result["anomaly_features"], list)


def test_anomaly_features_populated_for_anomaly(pipeline, anomaly_record):
    result = pipeline.predict_single_record(anomaly_record)
    assert isinstance(result["anomaly_features"], list)
    assert len(result["anomaly_features"]) > 0
    # Extreme delay > 286 days must trigger RULE_LONG_DELAY
    assert RULE_LONG_DELAY in result["anomaly_features"]
    # High sanction > 11,98,014 must trigger RULE_HIGH_SANCTION
    assert RULE_HIGH_SANCTION in result["anomaly_features"]
    # Early tenure < 113 days must trigger RULE_EARLY_TENURE
    assert RULE_EARLY_TENURE in result["anomaly_features"]


# ──────────────────────────────────────────────────────────────────────────────
# 8. is_anomalous generated (bool)
# ──────────────────────────────────────────────────────────────────────────────

def test_is_anomalous_is_bool(pipeline, normal_record):
    result = pipeline.predict_single_record(normal_record)
    assert isinstance(result["is_anomalous"], bool)


def test_is_anomalous_false_for_normal(pipeline, normal_record):
    result = pipeline.predict_single_record(normal_record)
    assert result["is_anomalous"] is False


def test_is_anomalous_true_for_anomaly(pipeline, anomaly_record):
    result = pipeline.predict_single_record(anomaly_record)
    assert result["is_anomalous"] is True


# ──────────────────────────────────────────────────────────────────────────────
# 9. variance_amount_inr remains None throughout (NOT fabricated)
# ──────────────────────────────────────────────────────────────────────────────

def test_variance_amount_inr_remains_none_normal(pipeline, normal_record):
    """variance_amount_inr must be None — expenditure data is unavailable."""
    result = pipeline.predict_single_record(normal_record)
    assert "variance_amount_inr" in result
    assert result["variance_amount_inr"] is None
    # Explicitly confirm it is not 0 or 0.0 (silent conversion is banned)
    assert result["variance_amount_inr"] != 0
    assert result["variance_amount_inr"] != 0.0


def test_variance_amount_inr_remains_none_anomaly(pipeline, anomaly_record):
    result = pipeline.predict_single_record(anomaly_record)
    assert result["variance_amount_inr"] is None
    assert result["variance_amount_inr"] != 0


def test_absent_financial_fields_not_fabricated(normal_record):
    """Loader must set expenditure/funds_released etc. to None — never synthetic values."""
    assert normal_record["expenditure"] is None
    assert normal_record["funds_released"] is None
    assert normal_record["physical_progress_pct"] is None
    assert normal_record["pfms_status"] is None
    assert normal_record["transaction_type"] is None


# ──────────────────────────────────────────────────────────────────────────────
# 10. Alert payload is backend-compatible
# ──────────────────────────────────────────────────────────────────────────────

def test_alert_payload_backend_compatible(pipeline, anomaly_record):
    """build_financial_anomaly_payload output must pass FinancialAnomalyPayload Pydantic validation."""
    result = pipeline.predict_single_record(anomaly_record)
    payload_dict = build_financial_anomaly_payload(result)

    # Must validate against backend schema without raising
    validated = FinancialAnomalyPayload(**payload_dict)
    assert validated.project_id == result["project_identifier"]
    assert validated.is_anomalous is True
    assert isinstance(validated.anomaly_features, list)
    assert validated.variance_amount_inr is None


def test_alert_payload_normal_record_compatible(pipeline, normal_record):
    result = pipeline.predict_single_record(normal_record)
    payload_dict = build_financial_anomaly_payload(result)
    validated = FinancialAnomalyPayload(**payload_dict)
    assert validated.project_id == result["project_identifier"]
    assert validated.is_anomalous is False
    assert validated.variance_amount_inr is None


def test_alert_payload_json_serializable(pipeline, anomaly_record):
    """The payload dict must be JSON-serializable (no NaN, no non-serializable types)."""
    result = pipeline.predict_single_record(anomaly_record)
    payload_dict = build_financial_anomaly_payload(result)
    json_str = json.dumps(payload_dict)
    parsed = json.loads(json_str)
    assert parsed["variance_amount_inr"] is None


# ──────────────────────────────────────────────────────────────────────────────
# 11. Raw model prediction does NOT control final is_anomalous
# ──────────────────────────────────────────────────────────────────────────────

def test_raw_prediction_does_not_control_final_anomaly(pipeline, normal_record):
    """Even if the raw model returns -1 (anomaly), the score cutoff governs is_anomalous.

    For a record that scores above the cutoff (score > -0.093716), is_anomalous
    must be False (assuming no domain rules fire), regardless of raw_pred.
    """
    result = pipeline.predict_single_record(normal_record)
    score = result["anomaly_score"]
    is_anomalous = result["is_anomalous"]
    rule_tags = result["anomaly_features"]

    if score > DEFAULT_MODEL_SCORE_CUTOFF and len(rule_tags) == 0:
        # Score above cutoff AND no domain rules → must be normal
        assert is_anomalous is False

    # model_prediction_for_diagnostics is stored but does not override the above
    raw_pred = result["model_prediction_for_diagnostics"]
    assert raw_pred in [-1, 1]

    # If score above cutoff, RULE_MODEL_ANOMALY must not be in features
    if score > DEFAULT_MODEL_SCORE_CUTOFF:
        assert RULE_MODEL_ANOMALY not in rule_tags


# ──────────────────────────────────────────────────────────────────────────────
# 12. PostgreSQL loader returns None for missing record (mock)
# ──────────────────────────────────────────────────────────────────────────────

def test_loader_returns_none_for_missing_record():
    """fetch_project_by_id must return None when the DB row does not exist."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_conn.execute.side_effect = Exception("Fallback to cursor")
    mock_cursor.fetchone.return_value = None

    loader = PostgreSQLDataLoader(connection=mock_conn)
    result = loader.fetch_project_by_id("NON_EXISTENT_ID")
    assert result is None


# ──────────────────────────────────────────────────────────────────────────────
# 13. PostgreSQL loader raises ConnectionError on unavailable DB
# ──────────────────────────────────────────────────────────────────────────────

def test_loader_raises_connection_error_on_unavailable_db():
    """When no URI and no connection, fetch_project_by_id must raise ConnectionError."""
    loader = PostgreSQLDataLoader(db_uri=None)
    with pytest.raises(ConnectionError, match="No database URI"):
        loader.fetch_project_by_id("12345")


def test_loader_batch_raises_connection_error_on_unavailable_db():
    """When no URI and no connection, fetch_sanctioned_projects_batch must raise ConnectionError."""
    loader = PostgreSQLDataLoader(db_uri=None)
    with pytest.raises(ConnectionError, match="No database URI"):
        loader.fetch_sanctioned_projects_batch(limit=1)


# ──────────────────────────────────────────────────────────────────────────────
# 14. Loader absent fields remain None after normalize (no fabrication)
# ──────────────────────────────────────────────────────────────────────────────

def test_loader_absent_fields_are_none():
    """normalize_db_record must set unavailable financial fields to None, not any synthetic value."""
    raw = {
        "id": "PROJ-ABSENT-001",
        "sanctioned_amount": 800000.0,
        "start_date": "2024-07-01",
        "sanction_date": "2024-09-30",
        "tenure_start_date": "2023-09-01",
    }
    norm = normalize_db_record(raw)

    assert norm["expenditure"] is None
    assert norm["funds_released"] is None
    assert norm["physical_progress_pct"] is None
    assert norm["pfms_status"] is None
    assert norm["transaction_type"] is None

    # These values must not have been assigned default numerics
    assert norm["expenditure"] != 0
    assert norm["funds_released"] != 0


# ──────────────────────────────────────────────────────────────────────────────
# 15. Multi-stage chain: mock DB → normalize → inference → payload
# ──────────────────────────────────────────────────────────────────────────────

def test_multi_stage_chain_mock_db(pipeline):
    """Simulate the full chain: mocked DB row → normalize → inference → backend payload."""
    # Step 1: Simulate DB cursor returning a row
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_conn.execute.side_effect = Exception("Fallback to cursor")

    mock_cursor.description = [
        ("id", None), ("sanctioned_amount", None), ("start_date", None),
        ("sanction_date", None), ("tenure_start_date", None), ("district_authority", None),
    ]
    mock_cursor.fetchone.return_value = (
        "PROJ-CHAIN-001", 450000.0, "2024-08-15", "2024-10-25",
        "2023-09-01", "DELHI NORTH",
    )

    loader = PostgreSQLDataLoader(connection=mock_conn)

    # Step 2: Fetch and normalize
    record = loader.fetch_project_by_id("PROJ-CHAIN-001")
    assert record is not None
    assert record["work_recommendation_dtl_id"] == "PROJ-CHAIN-001"
    assert record["expenditure"] is None  # absent field — not fabricated

    # Step 3: Run inference
    result = pipeline.predict_single_record(record)
    assert result["project_identifier"] == "PROJ-CHAIN-001"
    assert result["variance_amount_inr"] is None
    assert isinstance(result["is_anomalous"], bool)
    assert isinstance(result["anomaly_score"], float)

    # Step 4: Build payload and validate against backend schema
    payload_dict = build_financial_anomaly_payload(result)
    validated = FinancialAnomalyPayload(**payload_dict)
    assert validated.project_id == "PROJ-CHAIN-001"
    assert validated.variance_amount_inr is None


# ──────────────────────────────────────────────────────────────────────────────
# 16. Batch loader processes multiple records correctly (mock)
# ──────────────────────────────────────────────────────────────────────────────

def test_batch_loader_mock_multiple_records(pipeline):
    """fetch_sanctioned_projects_batch should return multiple normalized records."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_conn.execute.side_effect = Exception("Fallback to cursor")

    mock_cursor.description = [
        ("id", None), ("sanctioned_amount", None), ("start_date", None),
        ("sanction_date", None), ("tenure_start_date", None), ("district_authority", None),
    ]
    mock_cursor.fetchall.return_value = [
        ("PROJ-BATCH-001", 300000.0, "2024-06-01", "2024-08-15", "2023-09-01", "MUMBAI"),
        ("PROJ-BATCH-002", 750000.0, "2024-07-10", "2024-10-01", "2023-09-01", "PUNE"),
    ]

    loader = PostgreSQLDataLoader(connection=mock_conn)
    records = loader.fetch_sanctioned_projects_batch(limit=2)

    assert len(records) == 2
    assert records[0]["work_recommendation_dtl_id"] == "PROJ-BATCH-001"
    assert records[1]["work_recommendation_dtl_id"] == "PROJ-BATCH-002"

    # All absent fields must be None
    for rec in records:
        assert rec["expenditure"] is None
        assert rec["funds_released"] is None
        assert rec["variance_amount_inr"] if "variance_amount_inr" in rec else True

    # Run inference on all
    for rec in records:
        result = pipeline.predict_single_record(rec)
        assert isinstance(result["is_anomalous"], bool)
        assert result["variance_amount_inr"] is None


# ──────────────────────────────────────────────────────────────────────────────
# 17. Alert client sends correct payload shape to backend
# ──────────────────────────────────────────────────────────────────────────────

@patch("requests.post")
def test_alert_client_sends_correct_payload(mock_post, pipeline, anomaly_record):
    """FinancialAlertClient must POST a payload matching the backend contract."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"status": "received", "alert_id": "E2E-001"}
    mock_post.return_value = mock_response

    result = pipeline.predict_single_record(anomaly_record)
    client = FinancialAlertClient(base_url="http://localhost:8000")
    alert_res = client.send_alert(result)

    assert alert_res["success"] is True
    assert alert_res["status_code"] == 200
    assert alert_res["error"] is None

    # Inspect what was POSTed
    call_kwargs = mock_post.call_args[1]
    posted_payload = call_kwargs["json"]

    assert "project_id" in posted_payload
    assert "is_anomalous" in posted_payload
    assert "anomaly_features" in posted_payload
    assert "variance_amount_inr" in posted_payload
    assert posted_payload["variance_amount_inr"] is None


# ──────────────────────────────────────────────────────────────────────────────
# 18. Alert client preserves variance_amount_inr=None in HTTP payload
# ──────────────────────────────────────────────────────────────────────────────

@patch("requests.post")
def test_alert_client_preserves_null_variance(mock_post, pipeline, normal_record):
    """variance_amount_inr must be sent as JSON null, not 0 or omitted."""
    mock_response = MagicMock()
    mock_response.status_code = 201
    mock_response.json.return_value = {"created": True}
    mock_post.return_value = mock_response

    result = pipeline.predict_single_record(normal_record)
    client = FinancialAlertClient()
    client.send_alert(result)

    call_kwargs = mock_post.call_args[1]
    posted_payload = call_kwargs["json"]

    # variance_amount_inr must be None (JSON null), not 0
    assert "variance_amount_inr" in posted_payload
    assert posted_payload["variance_amount_inr"] is None
    assert posted_payload["variance_amount_inr"] != 0


# ──────────────────────────────────────────────────────────────────────────────
# 19. Backend unavailability detected cleanly
# ──────────────────────────────────────────────────────────────────────────────

@patch("requests.post")
def test_backend_unavailability_detected_cleanly(mock_post, pipeline, normal_record):
    """FinancialAlertClient must return success=False with error info, not raise an exception."""
    import requests as req_lib
    mock_post.side_effect = req_lib.exceptions.ConnectionError("Connection refused")

    result = pipeline.predict_single_record(normal_record)
    client = FinancialAlertClient(base_url="http://localhost:8000")

    # Must not raise — must return structured error dict
    alert_res = client.send_alert(result)

    assert alert_res["success"] is False
    assert alert_res["status_code"] is None
    assert alert_res["error"] is not None
    assert "Network error" in alert_res["error"]


# ──────────────────────────────────────────────────────────────────────────────
# 20. Rule tags match expected pattern for known anomaly features
# ──────────────────────────────────────────────────────────────────────────────

def test_rule_tags_match_expected_pattern_for_extreme_anomaly(pipeline):
    """An extreme multi-signal record must trigger all 3 domain rules + multi-signal tag."""
    rec = {
        "work_recommendation_dtl_id": "RULE-PATTERN-001",
        "sanction_amount": 5000000.0,        # > Rs 11,98,014 — triggers RULE_HIGH_SANCTION
        "recommendation_date": "2024-09-06",
        "sanction_date": "2026-07-31",        # 693 days delay — triggers RULE_LONG_DELAY
        "tenure_start_date": "2024-06-04",    # 94 days elapsed — triggers RULE_EARLY_TENURE
    }
    result = pipeline.predict_single_record(rec)

    tags = result["anomaly_features"]
    assert RULE_LONG_DELAY in tags, f"Expected RULE_LONG_DELAY in {tags}"
    assert RULE_HIGH_SANCTION in tags, f"Expected RULE_HIGH_SANCTION in {tags}"
    assert RULE_EARLY_TENURE in tags, f"Expected RULE_EARLY_TENURE in {tags}"
    assert RULE_MULTI_SIGNAL in tags, f"Expected RULE_MULTI_SIGNAL in {tags}"
    assert result["is_anomalous"] is True


def test_rule_tags_empty_for_clean_normal_project(pipeline):
    """A clearly normal project must have empty rule tags."""
    rec = {
        "work_recommendation_dtl_id": "RULE-NORMAL-001",
        "sanction_amount": 250000.0,         # Low amount — normal
        "recommendation_date": "2024-09-01",
        "sanction_date": "2024-11-20",        # 80 days — normal
        "tenure_start_date": "2022-09-01",    # > 700 days since tenure — normal
    }
    result = pipeline.predict_single_record(rec)
    tags = result["anomaly_features"]
    assert RULE_LONG_DELAY not in tags
    assert RULE_HIGH_SANCTION not in tags
    assert RULE_EARLY_TENURE not in tags
