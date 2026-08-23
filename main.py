from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from schemas import (
    FinancialAnomalyPayload, 
    PredictiveDelayPayload, 
    DuplicateDetectionPayload,
    FrontendProjectDashboard
)
import rules_engine

app = FastAPI(
    title="MPLADS Rules & Alert Engine",
    description="Backend API for the SIH 2026 MPLADS Fraud Detection Platform",
    version="1.0.0"
)

# Enable CORS for the frontend dev to hit localhost
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "MPLADS Alert Engine API is running. Ready for frontend consumption."}

@app.get("/api/v1/projects/{project_id}/dashboard", response_model=FrontendProjectDashboard)
def get_project_dashboard(project_id: str):
    """
    This endpoint serves the Frontend Dashboard.
    For the hackathon MVP, we are mocking the ML inputs here. 
    Once the ML teams are done, we will query their APIs/Database here instead.
    """
    
    # 1. Mock Data coming from Person 1 (Financial AI)
    mock_fin = FinancialAnomalyPayload(
        project_id=project_id,
        is_anomalous=True,
        anomaly_features=["expenditure_velocity_3x_normal"],
        variance_amount_inr=1500000
    )
    
    # 2. Mock Data coming from Person 2 (Predictive AI)
    mock_pred = PredictiveDelayPayload(
        project_id=project_id,
        predicted_delay_days=45,
        predicted_cost_overrun_inr=500000,
        shap_key_drivers=["contractor_historical_delay"]
    )
    
    # 3. Mock Data coming from Person 3 (Duplicate AI)
    mock_dup = DuplicateDetectionPayload(
        project_id=project_id,
        is_duplicate_flagged=True,
        similarity_percentage=92.5,
        matched_historical_project_id="PROJ-2022-001",
        shared_keywords=["water_treatment"]
    )
    
    # 4. Feed ML payloads into the Rules Engine to generate UI Alerts
    alerts = []
    alerts.extend(rules_engine.generate_financial_alerts(mock_fin))
    alerts.extend(rules_engine.generate_predictive_alerts(mock_pred))
    alerts.extend(rules_engine.generate_duplicate_alerts(mock_dup))
    
    # 5. Calculate overall status based on highest severity
    status = rules_engine.calculate_overall_status(alerts)
    
    # 6. Return the perfectly formatted JSON to the Frontend
    dashboard = FrontendProjectDashboard(
        project_id=project_id,
        project_name="Community Hall Construction (Sample)",
        location={"lat": 28.6139, "lng": 77.2090},
        overall_status=status,
        compliance_alerts=alerts,
        blockchain_verified=True
    )
    
    return dashboard
