from schemas import (
    FinancialAnomalyPayload, 
    PredictiveDelayPayload, 
    DuplicateDetectionPayload, 
    ComplianceAlert
)

def generate_financial_alerts(payload: FinancialAnomalyPayload) -> list[ComplianceAlert]:
    alerts = []
    if payload.is_anomalous:
        features_str = ", ".join(payload.anomaly_features)
        var_str = f"₹{payload.variance_amount_inr:,.2f}" if payload.variance_amount_inr is not None else "N/A"
        alerts.append(ComplianceAlert(
            type="FINANCIAL_DEVIATION",
            message=f"Financial anomaly detected. Key drivers: {features_str}. Variance: {var_str}",
            severity="HIGH"
        ))
    return alerts


def generate_predictive_alerts(payload: PredictiveDelayPayload) -> list[ComplianceAlert]:
    alerts = []
    if payload.predicted_delay_days > 30:
        alerts.append(ComplianceAlert(
            type="PREDICTIVE_WARNING",
            message=f"Project forecasted to be delayed by {payload.predicted_delay_days} days due to: {', '.join(payload.shap_key_drivers)}",
            severity="MEDIUM"
        ))
    if payload.predicted_cost_overrun_inr > 0:
        alerts.append(ComplianceAlert(
            type="COST_OVERRUN_WARNING",
            message=f"Predicted cost overrun of ₹{payload.predicted_cost_overrun_inr:,.2f}",
            severity="HIGH"
        ))
    return alerts

def generate_duplicate_alerts(payload: DuplicateDetectionPayload) -> list[ComplianceAlert]:
    alerts = []
    if payload.is_duplicate_flagged:
        alerts.append(ComplianceAlert(
            type="DUPLICATE_SUSPICION",
            message=f"Proposal is {payload.similarity_percentage}% similar to past project {payload.matched_historical_project_id}.",
            severity="CRITICAL"
        ))
    return alerts

def calculate_overall_status(alerts: list[ComplianceAlert]) -> str:
    if any(a.severity == "CRITICAL" for a in alerts):
        return "CRITICAL_ALERT"
    elif any(a.severity == "HIGH" for a in alerts):
        return "HIGH_RISK"
    elif any(a.severity == "MEDIUM" for a in alerts):
        return "NEEDS_ATTENTION"
    return "ON_TRACK"
