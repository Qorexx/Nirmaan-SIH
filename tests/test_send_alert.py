"""
Checkpoint 10 — Unit Tests for Backend Alert Client Module

Tests:
  1. valid anomaly payload construction
  2. normal project payload construction
  3. None variance preservation (json null)
  4. correct project ID mapping
  5. correct anomaly features mapping
  6. successful HTTP response (200/201)
  7. HTTP 400 bad request handling
  8. HTTP 500 server error handling
  9. connection timeout and network error handling
  10. configurable backend base URL and endpoint
"""

from unittest.mock import MagicMock, patch
import pytest
import requests

from ml_modules.financial.send_alert import (
    FinancialAlertClient,
    build_financial_anomaly_payload,
    DEFAULT_BACKEND_URL,
    DEFAULT_FINANCIAL_ALERT_ENDPOINT,
)


@pytest.fixture
def sample_anomaly_inference_result():
    return {
        "project_identifier": "139500",
        "is_anomalous": True,
        "anomaly_features": [
            "unusually_long_recommendation_to_sanction_delay",
            "unusually_high_sanction_amount",
            "multi_signal_statistical_anomaly",
        ],
        "anomaly_score": -0.237589,
        "model_prediction_for_diagnostics": -1,
        "feature_values": {
            "sanction_amount": 5000000.0,
            "log1p_sanction_amount": 15.424948,
            "rec_to_sanc_days": 693.0,
            "days_since_tenure_start": 94.0,
        },
        "validation_errors": [],
        "validation_warnings": [],
        "variance_amount_inr": None,
    }


@pytest.fixture
def sample_normal_inference_result():
    return {
        "project_identifier": "10001",
        "is_anomalous": False,
        "anomaly_features": [],
        "anomaly_score": 0.048512,
        "model_prediction_for_diagnostics": 1,
        "feature_values": {
            "sanction_amount": 300000.0,
            "log1p_sanction_amount": 12.611538,
            "rec_to_sanc_days": 80.0,
            "days_since_tenure_start": 366.0,
        },
        "validation_errors": [],
        "validation_warnings": [],
        "variance_amount_inr": None,
    }


# ── 1. Valid Anomaly Payload Construction ─────────────────────────────────────
def test_valid_anomaly_payload_construction(sample_anomaly_inference_result):
    payload = build_financial_anomaly_payload(sample_anomaly_inference_result)
    assert payload["project_id"] == "139500"
    assert payload["is_anomalous"] is True
    assert len(payload["anomaly_features"]) == 3
    assert payload["variance_amount_inr"] is None


# ── 2. Normal Project Payload Construction ────────────────────────────────────
def test_normal_project_payload_construction(sample_normal_inference_result):
    payload = build_financial_anomaly_payload(sample_normal_inference_result)
    assert payload["project_id"] == "10001"
    assert payload["is_anomalous"] is False
    assert payload["anomaly_features"] == []
    assert payload["variance_amount_inr"] is None


# ── 3. None Variance Preservation ──────────────────────────────────────────────
def test_none_variance_preservation(sample_anomaly_inference_result):
    payload = build_financial_anomaly_payload(sample_anomaly_inference_result)
    assert payload["variance_amount_inr"] is None
    assert payload["variance_amount_inr"] != 0.0
    assert payload["variance_amount_inr"] != 0


# ── 4. Correct Project ID Mapping ──────────────────────────────────────────────
def test_correct_project_id_mapping(sample_anomaly_inference_result):
    payload = build_financial_anomaly_payload(sample_anomaly_inference_result)
    assert payload["project_id"] == "139500"


# ── 5. Correct Anomaly Features Mapping ────────────────────────────────────────
def test_correct_anomaly_features_mapping(sample_anomaly_inference_result):
    payload = build_financial_anomaly_payload(sample_anomaly_inference_result)
    assert payload["anomaly_features"] == [
        "unusually_long_recommendation_to_sanction_delay",
        "unusually_high_sanction_amount",
        "multi_signal_statistical_anomaly",
    ]


# ── 6. Successful HTTP Response (200/201) ──────────────────────────────────────
@patch("requests.post")
def test_successful_http_response(mock_post, sample_anomaly_inference_result):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"status": "received", "alert_id": "ALT-001"}
    mock_post.return_value = mock_response

    client = FinancialAlertClient(base_url="http://localhost:8000")
    res = client.send_alert(sample_anomaly_inference_result)

    assert res["success"] is True
    assert res["status_code"] == 200
    assert res["response_data"]["status"] == "received"
    assert res["error"] is None
    assert res["payload_sent"]["variance_amount_inr"] is None
    mock_post.assert_called_once()


# ── 7. HTTP 400 Bad Request Handling ──────────────────────────────────────────
@patch("requests.post")
def test_http_400_bad_request_handling(mock_post, sample_anomaly_inference_result):
    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.text = '{"detail": "variance_amount_inr cannot be null"}'
    mock_post.return_value = mock_response

    client = FinancialAlertClient()
    res = client.send_alert(sample_anomaly_inference_result)

    assert res["success"] is False
    assert res["status_code"] == 400
    assert res["response_data"] is None
    assert "HTTP 400" in res["error"]


# ── 8. HTTP 500 Server Error Handling ──────────────────────────────────────────
@patch("requests.post")
def test_http_500_server_error_handling(mock_post, sample_anomaly_inference_result):
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.text = 'Internal Server Error'
    mock_post.return_value = mock_response

    client = FinancialAlertClient()
    res = client.send_alert(sample_anomaly_inference_result)

    assert res["success"] is False
    assert res["status_code"] == 500
    assert "HTTP 500" in res["error"]


# ── 9. Connection Timeout and Network Error Handling ─────────────────────────
@patch("requests.post")
def test_connection_timeout_and_network_error(mock_post, sample_anomaly_inference_result):
    # Timeout test
    mock_post.side_effect = requests.exceptions.Timeout("Connection timed out")
    client = FinancialAlertClient(timeout=2.0)
    res_timeout = client.send_alert(sample_anomaly_inference_result)

    assert res_timeout["success"] is False
    assert res_timeout["status_code"] is None
    assert "timeout" in res_timeout["error"].lower()

    # Connection error test
    mock_post.side_effect = requests.exceptions.ConnectionError("Failed to establish connection")
    res_conn = client.send_alert(sample_anomaly_inference_result)

    assert res_conn["success"] is False
    assert res_conn["status_code"] is None
    assert "Network error" in res_conn["error"]


# ── 10. Configurable Backend Base URL and Endpoint ────────────────────────────
@patch("requests.post")
def test_configurable_backend_url(mock_post, sample_anomaly_inference_result):
    mock_response = MagicMock()
    mock_response.status_code = 201
    mock_response.json.return_value = {"created": True}
    mock_post.return_value = mock_response

    custom_client = FinancialAlertClient(
        base_url="https://api.mplads.gov.in",
        endpoint="/v2/alerts/financial",
        timeout=10.0,
    )
    assert custom_client.full_url == "https://api.mplads.gov.in/v2/alerts/financial"

    res = custom_client.send_alert(sample_anomaly_inference_result)
    assert res["success"] is True

    # Verify requests.post was called with custom URL and timeout
    mock_post.assert_called_once()
    call_args, call_kwargs = mock_post.call_args
    assert call_args[0] == "https://api.mplads.gov.in/v2/alerts/financial"
    assert call_kwargs["timeout"] == 10.0
