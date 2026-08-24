from pydantic import BaseModel
from typing import List, Optional

# ==========================================
# Inputs from ML Teams (API Contracts)
# ==========================================

class FinancialAnomalyPayload(BaseModel):
    project_id: str
    is_anomalous: bool
    anomaly_features: List[str]
    variance_amount_inr: Optional[float] = None


class PredictiveDelayPayload(BaseModel):
    project_id: str
    predicted_delay_days: int
    predicted_cost_overrun_inr: float
    shap_key_drivers: List[str]

class DuplicateDetectionPayload(BaseModel):
    project_id: str
    is_duplicate_flagged: bool
    similarity_percentage: float
    matched_historical_project_id: Optional[str] = None
    shared_keywords: List[str] = []

# ==========================================
# Output to Frontend (Dashboards)
# ==========================================

class ComplianceAlert(BaseModel):
    type: str
    message: str
    severity: str

class FrontendProjectDashboard(BaseModel):
    project_id: str
    project_name: str
    location: dict
    overall_status: str
    compliance_alerts: List[ComplianceAlert]
    blockchain_verified: bool
