"""
Checkpoint 10 — Backend Alert Client Module (SIH26102 / Person 1)

Provides an HTTP client module to transmit financial anomaly inference results
to the backend API endpoint.

CONTRACT INTEGRATION CONSTRAINTS:
  - Preserves project_id, is_anomalous, and anomaly_features exactly.
  - Preserves variance_amount_inr = None (null) without converting to 0.0 or fabricating data.
  - Configurable backend base URL (defaults to http://localhost:8000).
  - Uses requests with configurable timeouts and structured error handling.
  - DOES NOT modify backend code, schemas.py, or main.py.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional
import requests

logger = logging.getLogger(__name__)

DEFAULT_BACKEND_URL = "http://localhost:8000"
DEFAULT_FINANCIAL_ALERT_ENDPOINT = "/api/v1/financial-anomalies"
DEFAULT_TIMEOUT_SECONDS = 5.0


def build_financial_anomaly_payload(inference_result: Dict[str, Any]) -> Dict[str, Any]:
    """Construct the API request payload dictionary from a pipeline inference result.

    Preserves variance_amount_inr = None (null in JSON) without converting to 0.0.
    """
    if not isinstance(inference_result, dict):
        raise TypeError("inference_result must be a dictionary")

    project_id = str(inference_result.get("project_identifier", "UNKNOWN"))
    is_anomalous = bool(inference_result.get("is_anomalous", False))
    anomaly_features = list(inference_result.get("anomaly_features", []))
    variance_amount_inr = inference_result.get("variance_amount_inr", None)

    return {
        "project_id": project_id,
        "is_anomalous": is_anomalous,
        "anomaly_features": anomaly_features,
        "variance_amount_inr": variance_amount_inr,
    }


class FinancialAlertClient:
    """HTTP Client for sending financial anomaly payloads to the backend API."""

    def __init__(
        self,
        base_url: str = DEFAULT_BACKEND_URL,
        endpoint: str = DEFAULT_FINANCIAL_ALERT_ENDPOINT,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
    ):
        self.base_url = base_url.rstrip("/")
        self.endpoint = endpoint if endpoint.startswith("/") else f"/{endpoint}"
        self.timeout = timeout

    @property
    def full_url(self) -> str:
        return f"{self.base_url}{self.endpoint}"

    def send_alert(self, inference_result: Dict[str, Any]) -> Dict[str, Any]:
        """Transmit an inference result payload to the backend endpoint.

        Parameters
        ----------
        inference_result : dict
            Output dictionary from FinancialAnomalyInferencePipeline.predict_single_record().

        Returns
        -------
        dict
            {
                "success": bool,
                "status_code": int | None,
                "response_data": dict | None,
                "error": str | None,
                "payload_sent": dict
            }
        """
        payload = build_financial_anomaly_payload(inference_result)

        try:
            logger.info("[FinancialAlertClient] Posting payload to %s: %s", self.full_url, payload)
            response = requests.post(
                self.full_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=self.timeout,
            )

            if response.status_code in (200, 201):
                try:
                    data = response.json()
                except Exception:
                    data = {"text": response.text}

                return {
                    "success": True,
                    "status_code": response.status_code,
                    "response_data": data,
                    "error": None,
                    "payload_sent": payload,
                }
            else:
                return {
                    "success": False,
                    "status_code": response.status_code,
                    "response_data": None,
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "payload_sent": payload,
                }

        except requests.exceptions.Timeout as e:
            logger.error("[FinancialAlertClient] Timeout connecting to %s: %s", self.full_url, str(e))
            return {
                "success": False,
                "status_code": None,
                "response_data": None,
                "error": f"Request timeout after {self.timeout}s: {str(e)}",
                "payload_sent": payload,
            }
        except requests.exceptions.RequestException as e:
            logger.error("[FinancialAlertClient] Connection error to %s: %s", self.full_url, str(e))
            return {
                "success": False,
                "status_code": None,
                "response_data": None,
                "error": f"Network error connecting to backend: {str(e)}",
                "payload_sent": payload,
            }
