import httpx
import schemas
import rules_engine
import crud
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError

# Person 2 & 3 Service URLs
PREDICTIVE_AI_URL = "http://localhost:8002/api/v1/predict-early-warning"
DUPLICATE_AI_URL = "http://localhost:8003/check-new-project"

async def trigger_ml_services_for_project(project_id: str, db: Session):
    """
    Bridge function: Calls Person 2 and Person 3's isolated FastAPI services,
    retrieves their JSON, generates alerts, and stores them in our DB.
    """
    alerts_to_save = []

    async with httpx.AsyncClient() as client:
        # 1. Call Person 2 (Predictive AI)
        try:
            # Note: Depending on Person 2's exact input requirement, we send project_id.
            pred_resp = await client.post(PREDICTIVE_AI_URL, json={"project_id": project_id}, timeout=5.0)
            if pred_resp.status_code == 200:
                payload = schemas.PredictiveDelayPayload(**pred_resp.json())
                alerts_to_save.extend(rules_engine.generate_predictive_alerts(payload))
        except Exception as e:
            print(f"Warning: Could not reach Predictive AI service: {e}")

        # 2. Call Person 3 (Duplicate AI)
        try:
            dup_resp = await client.post(DUPLICATE_AI_URL, json={"project_id": project_id}, timeout=5.0)
            if dup_resp.status_code == 200:
                payload = schemas.DuplicateDetectionPayload(**dup_resp.json())
                alerts_to_save.extend(rules_engine.generate_duplicate_alerts(payload))
        except Exception as e:
            print(f"Warning: Could not reach Duplicate AI service: {e}")

    # Save to Database if we got any alerts
    if alerts_to_save:
        try:
            crud.create_compliance_alerts(db, project_id, alerts_to_save)
            return {"status": "success", "alerts_generated": len(alerts_to_save)}
        except OperationalError:
            print("Warning: Database not ready, skipping save.")
            return {"status": "db_error", "alerts_generated": len(alerts_to_save)}
    
    return {"status": "success", "alerts_generated": 0, "message": "No alerts generated or services unavailable."}
