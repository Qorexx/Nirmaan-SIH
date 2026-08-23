# Backend Alert Client Specification & Contract Mismatch Report

**Project:** SIH 2026 — Problem Statement SIH26102 (MoSPI)  
**Lead:** Person 1 (Financial AI / Anomaly Detection Engine)  
**Module:** `ml_modules/financial/send_alert.py`  
**Date:** 2026-08-23  

---

## 1. Backend Endpoint Discovered

Inspection of `main.py` and `schemas.py` reveals the current backend structure:

- **Target Route:** `/api/v1/financial-anomalies` (Prospective POST endpoint for Person 1 ML alerts).
- **Current Route Status:** In `main.py`, only `GET /` and `GET /api/v1/projects/{project_id}/dashboard` exist. The dashboard endpoint currently instantiates a hardcoded mock `FinancialAnomalyPayload` object internally.
- **HTTP Method:** `POST` (for ML alert ingestion).

---

## 2. Request Schema Discovered

In `schemas.py` (lines 8–12), the backend defines `FinancialAnomalyPayload`:

```python
class FinancialAnomalyPayload(BaseModel):
    project_id: str
    is_anomalous: bool
    anomaly_features: List[str]
    variance_amount_inr: float
```

---

## 3. Response Schema

Prospective ingestion endpoint response schema:

```json
{
    "status": "received",
    "project_id": "string",
    "alert_id": "string",
    "processed_at": "ISO-8601 timestamp"
}
```

---

## 4. Field Mapping

The client function `build_financial_anomaly_payload()` maps inference results to the backend schema as follows:

| Inference Output Key | Backend Payload Key | Type | Description |
| :--- | :--- | :---: | :--- |
| `project_identifier` | `project_id` | `str` | Unique project identifier |
| `is_anomalous` | `is_anomalous` | `bool` | Flag indicating anomaly score $\le -0.093716$ or domain rule trigger |
| `anomaly_features` | `anomaly_features` | `List[str]` | List of human-readable explanation tags |
| `variance_amount_inr` | `variance_amount_inr` | `None` / `null` | Financial variance amount (INR) |

---

## 5. Nullable Variance Contract Analysis & Mismatch Report

> [!CAUTION]
> **CRITICAL CONTRACT MISMATCH REPORT:**
> - **Inference Pipeline Output:** Sets `variance_amount_inr = None` because expenditure/disbursal fields are absent from the official dataset snapshot.
> - **Current Backend Schema:** `schemas.py` types `variance_amount_inr: float` as a **mandatory, non-null float**.
> - **Pydantic Behavior:** Passing `{"variance_amount_inr": null}` to the current `FinancialAnomalyPayload` schema will fail with a Pydantic validation error (`value is not a valid float`).
> - **Strict Policy Compliance:** The client explicitly preserves `variance_amount_inr = None` (`null` in JSON) and does NOT silently send `0.0`. Backend schemas were NOT modified per Checkpoint 10 constraints.
> - **Recommendation:** When backend modifications are permitted in future integration phases, `schemas.py` should be updated to:
>   `variance_amount_inr: Optional[float] = None` or `Union[float, None] = None`.

---

## 6. HTTP Error Handling

`FinancialAlertClient` handles all HTTP and network communication errors gracefully:

1. **HTTP 200 / 201 Success:** Returns `{"success": True, "status_code": code, "response_data": data}`.
2. **HTTP 400 / 422 Client Error (Schema Validation Failure):** Returns `{"success": False, "status_code": 400/422, "error": "HTTP 400..."}`.
3. **HTTP 500 Server Error:** Returns `{"success": False, "status_code": 500, "error": "HTTP 500..."}`.
4. **Network Timeout / Connection Failure:** Catches `requests.exceptions.Timeout` and `RequestException`, returning `{"success": False, "status_code": None, "error": "Network error..."}` without crashing the calling process.

---

## 7. Configuration

```python
client = FinancialAlertClient(
    base_url="http://localhost:8000",
    endpoint="/api/v1/financial-anomalies",
    timeout=5.0
)
```

---

## 8. Example Payload

```json
{
    "project_id": "139500",
    "is_anomalous": true,
    "anomaly_features": [
        "unusually_long_recommendation_to_sanction_delay",
        "unusually_high_sanction_amount",
        "multi_signal_statistical_anomaly"
    ],
    "variance_amount_inr": null
}
```

---

## 9. Current Financial-Data Limitation

Because the official dataset snapshot lacks `expenditure`, `funds_released`, and `physical_progress_pct`, actual financial cost overruns or under-expenditure (`sanction_amount - expenditure`) cannot be calculated.

`variance_amount_inr` remains `null` until actual transaction/expenditure logs are made available to the platform.
