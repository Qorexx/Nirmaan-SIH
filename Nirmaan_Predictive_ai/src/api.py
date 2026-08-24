"""
Task 4: FastAPI Early Warning Backend
=======================================
Single unified endpoint for the MPLADS Early Warning & Decision Support System.

Endpoint: POST /api/v1/predict-early-warning
  - Accepts project feature data
  - Returns forecasts, SHAP explanations, and actionable triggers
  - JSON schema matches Person 6 (Backend Lead) specification exactly
"""

import os
import numpy as np
import joblib
from pathlib import Path
from typing import List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.shap_explainer import get_top_factors


# ---------------------------------------------------------------------------
# Pydantic schemas — strict contract with Person 6
# ---------------------------------------------------------------------------

class ProjectInput(BaseModel):
    """Input schema: project data from the MPLADS monitoring frontend."""
    project_id: str = Field(..., description="Unique project identifier, e.g. MPLADS-1234")
    state: str = Field(..., description="Indian state or UT")
    constituency_type: str = Field(..., description="LOK_SABHA or RAJYA_SABHA")
    project_category: str = Field(..., description="MPLADS work category")
    estimated_cost: float = Field(..., gt=0, description="Estimated cost in ₹")
    sanctioned_amount: float = Field(..., gt=0, description="Sanctioned amount in ₹")
    expected_duration_days: int = Field(..., gt=0, description="Expected duration in days")
    elapsed_days: int = Field(..., ge=0, description="Days elapsed since sanction")
    progress_pct: float = Field(..., ge=0, le=100, description="Completion percentage")
    contractor_id: str = Field(..., description="Contractor identifier")
    contractor_past_delays: int = Field(..., ge=0, description="Historical delay count")
    monsoon_overlap_days: int = Field(..., ge=0, description="Monsoon overlap in days")
    material_inflation_index: float = Field(..., gt=0, description="WPI inflation factor")
    labor_shortage_index: float = Field(..., ge=0, le=1, description="Labor shortage 0-1")
    terrain_difficulty: str = Field(..., description="PLAIN, HILLY, COASTAL, or DESERT")
    sanction_year: int = Field(..., ge=2023, description="Year of sanction")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "project_id": "MPLADS-1234",
                    "state": "Uttar Pradesh",
                    "constituency_type": "LOK_SABHA",
                    "project_category": "Roads",
                    "estimated_cost": 2500000,
                    "sanctioned_amount": 2400000,
                    "expected_duration_days": 365,
                    "elapsed_days": 280,
                    "progress_pct": 35.0,
                    "contractor_id": "CTR-042",
                    "contractor_past_delays": 8,
                    "monsoon_overlap_days": 90,
                    "material_inflation_index": 1.22,
                    "labor_shortage_index": 0.7,
                    "terrain_difficulty": "HILLY",
                    "sanction_year": 2024,
                }
            ]
        }
    }


class ActionableTrigger(BaseModel):
    """A single actionable alert trigger."""
    type: str
    severity: str
    threshold_violated: str
    message: str


class Forecasts(BaseModel):
    """Tangible business forecasts — no abstract scores."""
    predicted_delay_days: int
    predicted_cost_overrun_amount: int
    predicted_final_cost: int


class Explanations(BaseModel):
    """SHAP-driven top contributing factors."""
    top_delay_factors: List[str]
    top_cost_factors: List[str]


class EarlyWarningResponse(BaseModel):
    """
    Unified response payload — matches Person 6's exact specification.
    """
    project_id: str
    forecasts: Forecasts
    explanations: Explanations
    actionable_triggers: List[ActionableTrigger]


# ---------------------------------------------------------------------------
# Application setup with model loading lifecycle
# ---------------------------------------------------------------------------

# Global model references
_models = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load ML models at startup, release at shutdown."""
    model_dir = Path("models")

    required_files = [
        "cost_model.joblib",
        "delay_model.joblib",
        "preprocessor.joblib",
        "feature_names.joblib",
    ]

    for f in required_files:
        path = model_dir / f
        if not path.exists():
            raise RuntimeError(
                f"Model file not found: {path}. "
                f"Run 'python run_pipeline.py' first to generate data and train models."
            )

    _models["cost_model"] = joblib.load(model_dir / "cost_model.joblib")
    _models["delay_model"] = joblib.load(model_dir / "delay_model.joblib")
    _models["preprocessor"] = joblib.load(model_dir / "preprocessor.joblib")
    _models["feature_names"] = joblib.load(model_dir / "feature_names.joblib")

    print("[Task 4] ✅ Models loaded successfully.")
    print(f"         Features: {_models['feature_names']}")

    yield

    _models.clear()
    print("[Task 4] Models unloaded.")


app = FastAPI(
    title="MPLADS Early Warning & Decision Support System",
    description=(
        "Predictive AI backend for MPLADS project monitoring. "
        "Provides tangible forecasts (delay days, cost overrun ₹), "
        "SHAP explanations, and actionable alert triggers."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow Person 6's frontend to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Business logic: Actionable trigger generation
# ---------------------------------------------------------------------------

def generate_triggers(
    predicted_delay_days: float,
    predicted_cost_overrun: float,
    expected_duration_days: int,
    sanctioned_amount: float,
    progress_pct: float,
    elapsed_days: int,
) -> List[ActionableTrigger]:
    """
    Apply business rules to generate explicit, actionable warnings.
    No abstract scores — only tangible thresholds and instructions.
    """
    triggers = []

    # ---- TIME WARNING ----
    timeline_buffer_pct = (predicted_delay_days / max(expected_duration_days, 1)) * 100

    if timeline_buffer_pct > 20:
        triggers.append(ActionableTrigger(
            type="TIME_WARNING",
            severity="RED",
            threshold_violated=f">{20}% timeline buffer exceeded ({timeline_buffer_pct:.0f}% projected)",
            message=(
                f"Project forecasted to be {int(predicted_delay_days)} days late "
                f"({timeline_buffer_pct:.0f}% over expected {expected_duration_days}-day timeline). "
                f"Initiate physical inspection and seek contractor explanation."
            ),
        ))
    elif timeline_buffer_pct > 10:
        triggers.append(ActionableTrigger(
            type="TIME_WARNING",
            severity="AMBER",
            threshold_violated=f">{10}% timeline buffer exceeded ({timeline_buffer_pct:.0f}% projected)",
            message=(
                f"Project may be delayed by {int(predicted_delay_days)} days "
                f"({timeline_buffer_pct:.0f}% over timeline). "
                f"Schedule review meeting with implementing agency."
            ),
        ))

    # ---- COST ESCALATION ----
    cost_overrun_pct = (predicted_cost_overrun / max(sanctioned_amount, 1)) * 100

    if cost_overrun_pct > 15:
        triggers.append(ActionableTrigger(
            type="COST_ESCALATION",
            severity="RED",
            threshold_violated=f">{15}% cost overrun ({cost_overrun_pct:.1f}% projected)",
            message=(
                f"Predicted cost overrun of ₹{int(predicted_cost_overrun):,} "
                f"({cost_overrun_pct:.1f}% above sanctioned ₹{int(sanctioned_amount):,}). "
                f"Escalate to District Authority for revised sanction or scope reduction."
            ),
        ))
    elif cost_overrun_pct > 5:
        triggers.append(ActionableTrigger(
            type="COST_ESCALATION",
            severity="AMBER",
            threshold_violated=f">{5}% cost overrun ({cost_overrun_pct:.1f}% projected)",
            message=(
                f"Potential cost overrun of ₹{int(predicted_cost_overrun):,} "
                f"({cost_overrun_pct:.1f}% above sanctioned amount). "
                f"Review material procurement and labor costs."
            ),
        ))

    # ---- STALLED PROJECT ----
    elapsed_pct = (elapsed_days / max(expected_duration_days, 1)) * 100
    if progress_pct < 40 and elapsed_pct > 60:
        triggers.append(ActionableTrigger(
            type="STALLED_PROJECT",
            severity="RED",
            threshold_violated=(
                f"Progress {progress_pct:.0f}% but {elapsed_pct:.0f}% time elapsed"
            ),
            message=(
                f"Project has only {progress_pct:.0f}% completion despite "
                f"{elapsed_pct:.0f}% of expected duration elapsed ({elapsed_days}/{expected_duration_days} days). "
                f"Project may be stalled. Recommend immediate site visit and contractor audit."
            ),
        ))

    return triggers


# ---------------------------------------------------------------------------
# Main prediction endpoint
# ---------------------------------------------------------------------------

@app.post(
    "/api/v1/predict-early-warning",
    response_model=EarlyWarningResponse,
    summary="Predict early warning for an MPLADS project",
    description=(
        "Accepts project data and returns tangible forecasts "
        "(predicted delay days, cost overrun amount), SHAP-based explanations, "
        "and actionable trigger alerts."
    ),
)
async def predict_early_warning(project: ProjectInput) -> EarlyWarningResponse:
    """
    Unified early warning prediction endpoint.

    Flow:
    1. Extract features from input → preprocess
    2. Run through cost model → predicted final cost → cost overrun
    3. Run through delay model → predicted delay days
    4. SHAP: extract top factors for both predictions
    5. Business logic: generate actionable triggers
    6. Return structured JSON matching Person 6's spec
    """
    try:
        preprocessor = _models["preprocessor"]
        cost_model = _models["cost_model"]
        delay_model = _models["delay_model"]
        feature_names = _models["feature_names"]
    except KeyError:
        raise HTTPException(
            status_code=503,
            detail="Models not loaded. Run the training pipeline first.",
        )

    # --- Step 1: Build feature array in exact column order ---
    import pandas as pd

    feature_dict = {
        "state": project.state,
        "constituency_type": project.constituency_type,
        "project_category": project.project_category,
        "terrain_difficulty": project.terrain_difficulty,
        "estimated_cost": project.estimated_cost,
        "sanctioned_amount": project.sanctioned_amount,
        "expected_duration_days": project.expected_duration_days,
        "elapsed_days": project.elapsed_days,
        "progress_pct": project.progress_pct,
        "contractor_past_delays": project.contractor_past_delays,
        "monsoon_overlap_days": project.monsoon_overlap_days,
        "material_inflation_index": project.material_inflation_index,
        "labor_shortage_index": project.labor_shortage_index,
        "sanction_year": project.sanction_year,
    }

    # Create a single-row DataFrame for the preprocessor
    input_df = pd.DataFrame([feature_dict])
    preprocessed = preprocessor.transform(input_df)

    # --- Step 2: Cost prediction ---
    predicted_final_cost = float(cost_model.predict(preprocessed)[0])
    predicted_cost_overrun = max(predicted_final_cost - project.sanctioned_amount, 0)

    # --- Step 3: Delay prediction ---
    predicted_delay_days = max(float(delay_model.predict(preprocessed)[0]), 0)

    # --- Step 4: SHAP explanations ---
    top_delay_factors = get_top_factors(
        delay_model, preprocessed, feature_names, top_n=3
    )
    top_cost_factors = get_top_factors(
        cost_model, preprocessed, feature_names, top_n=3
    )

    # --- Step 5: Actionable triggers ---
    triggers = generate_triggers(
        predicted_delay_days=predicted_delay_days,
        predicted_cost_overrun=predicted_cost_overrun,
        expected_duration_days=project.expected_duration_days,
        sanctioned_amount=project.sanctioned_amount,
        progress_pct=project.progress_pct,
        elapsed_days=project.elapsed_days,
    )

    # --- Step 6: Build response ---
    response = EarlyWarningResponse(
        project_id=project.project_id,
        forecasts=Forecasts(
            predicted_delay_days=int(round(predicted_delay_days)),
            predicted_cost_overrun_amount=int(round(predicted_cost_overrun)),
            predicted_final_cost=int(round(predicted_final_cost)),
        ),
        explanations=Explanations(
            top_delay_factors=top_delay_factors,
            top_cost_factors=top_cost_factors,
        ),
        actionable_triggers=triggers,
    )

    return response


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@app.get("/health", summary="Health check")
async def health():
    models_loaded = all(
        k in _models for k in ["cost_model", "delay_model", "preprocessor"]
    )
    return {
        "status": "healthy" if models_loaded else "models_not_loaded",
        "models_loaded": models_loaded,
        "service": "MPLADS Early Warning & Decision Support System",
        "version": "1.0.0",
    }


# ---------------------------------------------------------------------------
# Direct run support
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
