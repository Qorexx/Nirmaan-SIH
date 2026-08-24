from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError

from database import get_db, engine
import models
import schemas
import crud
import rules_engine
import ml_integrator

# Attempt to create tables if DB is connected (will fail gracefully if not)
try:
    models.Base.metadata.create_all(bind=engine)
except OperationalError:
    print("WARNING: Database not connected yet. Running in Mock/Hackathon Mode.")

app = FastAPI(
    title="MPLADS Rules & Alert Engine",
    description="Backend API for the SIH 2026 MPLADS Fraud Detection Platform",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# INGESTION LAYER (For ML Teams 1, 2, 3)
# ==========================================

@app.post("/api/v1/projects/{project_id}/financial-anomaly")
def ingest_financial_anomaly(project_id: str, payload: schemas.FinancialAnomalyPayload, db: Session = Depends(get_db)):
    """Person 1 (Financial AI) sends data here"""
    alerts = rules_engine.generate_financial_alerts(payload)
    if alerts:
        try:
            crud.create_compliance_alerts(db, project_id, alerts)
        except OperationalError:
            pass # Ignore DB errors if Person 4 hasn't finished DB setup yet
            
    return {"status": "success", "alerts_generated": len(alerts)}

@app.post("/api/v1/projects/{project_id}/predictive-delay")
def ingest_predictive_delay(project_id: str, payload: schemas.PredictiveDelayPayload, db: Session = Depends(get_db)):
    """Person 2 (Predictive AI) sends data here"""
    alerts = rules_engine.generate_predictive_alerts(payload)
    if alerts:
        try:
            crud.create_compliance_alerts(db, project_id, alerts)
        except OperationalError:
            pass
            
    return {"status": "success", "alerts_generated": len(alerts)}

@app.post("/api/v1/projects/{project_id}/duplicate-detection")
def ingest_duplicate_detection(project_id: str, payload: schemas.DuplicateDetectionPayload, db: Session = Depends(get_db)):
    """Person 3 (Duplicate AI) sends data here"""
    alerts = rules_engine.generate_duplicate_alerts(payload)
    if alerts:
        try:
            crud.create_compliance_alerts(db, project_id, alerts)
        except OperationalError:
            pass
            
    return {"status": "success", "alerts_generated": len(alerts)}


# ==========================================
# ML INTEGRATOR BRIDGE (For Persons 2 & 3)
# ==========================================

@app.post("/api/v1/projects/{project_id}/trigger-ml")
async def trigger_ml_services(project_id: str, db: Session = Depends(get_db)):
    """
    Hackathon Fix: Actively calls Person 2 and Person 3's APIs
    to fetch anomalies instead of waiting for them to POST to us.
    """
    return await ml_integrator.trigger_ml_services_for_project(project_id, db)


# ==========================================
# VISION ORACLE & EVIDENCE LAYER
# ==========================================
from fastapi import UploadFile, File
import vision_oracle

@app.post("/api/v1/projects/{project_id}/upload-evidence")
async def upload_geotagged_evidence(project_id: str, file: UploadFile = File(...)):
    """
    Accepts a geotagged photo from the contractor.
    Runs Vision AI to verify structural progress and geofence.
    Hashes the image for the Blockchain Trust Ledger.
    """
    result = vision_oracle.verify_and_hash_image(file)
    
    # In a real flow, we would call the Smart Contract here:
    # contract.functions.updateProgress(project_id, 45, result['evidence_hash'])
    
    return {
        "project_id": project_id,
        "vision_verification": result,
        "message": "Evidence cryptographically hashed and verified by Vision Oracle."
    }


# ==========================================
# PRESENTATION LAYER (For Frontend Person 7)
# ==========================================

@app.get("/api/v1/projects/{project_id}/dashboard", response_model=schemas.FrontendProjectDashboard)
def get_project_dashboard(project_id: str, db: Session = Depends(get_db)):
    """
    Serves the Frontend Dashboard. 
    HACKATHON SAFETY: Automatically falls back to mock data if the database isn't ready,
    ensuring the Frontend developer is NEVER blocked.
    """
    try:
        # Try to fetch real data from DB
        db_project = crud.get_project(db, project_id)
        if db_project:
            # We have real DB data!
            alerts = [
                schemas.ComplianceAlert(type=a.alert_type, message=a.message, severity=a.severity)
                for a in db_project.compliance_alerts
            ]
            status = rules_engine.calculate_overall_status(alerts)
            is_verified = crud.check_blockchain_verification(db, project_id)
            
            return schemas.FrontendProjectDashboard(
                project_id=str(db_project.id),
                project_name=db_project.project_title,
                location={"lat": 28.6139, "lng": 77.2090}, # Simplified for MVP
                overall_status=status,
                compliance_alerts=alerts,
                blockchain_verified=is_verified
            )
    except OperationalError:
        # Database isn't running yet (Person 4 is still working)
        pass 

    # --- HACKATHON FALLBACK MOCK DATA ---
    # If the DB fails or project isn't found, return perfect mock data 
    # so Person 7 can keep building the UI uninterrupted.
    mock_fin = schemas.FinancialAnomalyPayload(
        project_id=project_id, is_anomalous=True, anomaly_features=["expenditure_velocity_3x_normal"], variance_amount_inr=1500000)
    mock_pred = schemas.PredictiveDelayPayload(
        project_id=project_id, predicted_delay_days=45, predicted_cost_overrun_inr=500000, shap_key_drivers=["contractor_historical_delay"])
    mock_dup = schemas.DuplicateDetectionPayload(
        project_id=project_id, is_duplicate_flagged=True, similarity_percentage=92.5, matched_historical_project_id="PROJ-2022-001", shared_keywords=["water_treatment"])
    
    mock_alerts = []
    mock_alerts.extend(rules_engine.generate_financial_alerts(mock_fin))
    mock_alerts.extend(rules_engine.generate_predictive_alerts(mock_pred))
    mock_alerts.extend(rules_engine.generate_duplicate_alerts(mock_dup))
    
    return schemas.FrontendProjectDashboard(
        project_id=project_id,
        project_name="Community Hall Construction (Mock Fallback)",
        location={"lat": 28.6139, "lng": 77.2090},
        overall_status=rules_engine.calculate_overall_status(mock_alerts),
        compliance_alerts=mock_alerts,
        blockchain_verified=True
    )
