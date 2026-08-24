"""
MPLADS Duplicate & Similarity Detection AI — FastAPI Service
Person 3 | NIRMAN | SIH 2024 Problem Statement 26102

Endpoints:
  GET  /health              → service health + model status
  POST /compare-pair        → compare 2 custom projects
  POST /find-duplicates     → find all duplicates in a project corpus
  POST /check-new-project   → check a new project against existing corpus
"""
from __future__ import annotations

import logging
import sys
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Add current dir to path so imports resolve correctly when run from duplicate-ml/
sys.path.insert(0, ".")

from schemas.project import (
    ComparePairRequest,
    FindDuplicatesRequest,
    CheckNewProjectRequest,
    ProjectRecord,
)
from services.embeddings import load_model
from services import duplicate_detector as detector

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


# ── Lifespan: load model once at startup ────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up MPLADS Duplicate Detection ML Service…")
    try:
        load_model()
        logger.info("Sentence Transformer model ready.")
    except Exception as e:
        logger.error(f"Failed to load model at startup: {e}")
        # Do not crash — endpoints will attempt lazy load
    yield
    logger.info("Shutting down MPLADS Duplicate Detection ML Service.")


# ── App factory ──────────────────────────────────────────────────────────────
app = FastAPI(
    title="MPLADS Duplicate & Similarity Detection AI",
    description=(
        "Person 3 module for NIRMAN (SIH PS-26102). "
        "Detects potentially duplicate, overlapping, or suspiciously similar "
        "MPLADS projects using Sentence Transformers, FAISS, Haversine distance, "
        "category taxonomy, and temporal overlap."
    ),
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Helper ───────────────────────────────────────────────────────────────────
def _pair_to_dict(pair: detector.DuplicatePairResult) -> dict:
    return {
        "pair_id":                    pair.pair_id,
        "potential_duplicate_score":  pair.potential_duplicate_score,
        "similarity_percentage":      pair.similarity_percentage,
        "duplicate_probability":      pair.duplicate_probability,
        "risk_level":                 pair.risk_level,
        "risk_badge":                 pair.risk_badge,
        "explanation":                pair.explanation,
        "reasons":                    pair.reasons,
        "score_breakdown":            pair.score_breakdown,
        "project_a":                  pair.project_a,
        "project_b":                  pair.project_b,
        "metadata":                   pair.metadata,
    }


# ── Endpoints ────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    """Health check. Returns model load status."""
    from services.embeddings import _model
    return {
        "status": "online",
        "service": "MPLADS Duplicate & Similarity Detection AI",
        "version": "2.0.0",
        "model": "paraphrase-multilingual-MiniLM-L12-v2",
        "model_loaded": _model is not None,
    }


@app.post("/compare-pair")
def compare_pair(req: ComparePairRequest):
    """
    Compare exactly two projects and return a full similarity analysis.
    Used by the interactive Sandbox Tester in the Next.js frontend.
    """
    try:
        result = detector.compare_pair(req.projectA, req.projectB)
        return {
            "status": "success",
            "analysis": _pair_to_dict(result),
        }
    except Exception as e:
        logger.exception("Error in /compare-pair")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/find-duplicates")
def find_duplicates(req: FindDuplicatesRequest):
    """
    Scan a corpus of projects and return all flagged duplicate pairs.
    Main deliverable for Person 6 Unified Risk Engine.
    """
    try:
        pairs = detector.find_duplicates(req.projects, threshold=req.threshold)

        critical_count = sum(1 for p in pairs if p.risk_level == "CRITICAL REVIEW")
        very_high_count = sum(1 for p in pairs if p.risk_level == "VERY HIGH")
        high_count      = sum(1 for p in pairs if p.risk_level == "HIGH")

        return {
            "status": "success",
            "module": "MPLADS Duplicate & Similarity Detection AI Engine",
            "total_projects_scanned": len(req.projects),
            "flagged_pairs_count": len(pairs),
            "summary": {
                "critical_review":  critical_count,
                "very_high_risk":   very_high_count,
                "high_risk":        high_count,
                "total_flagged":    len(pairs),
                "threshold_used":   req.threshold,
            },
            "results": [_pair_to_dict(p) for p in pairs],
        }
    except Exception as e:
        logger.exception("Error in /find-duplicates")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/check-new-project")
def check_new_project(req: CheckNewProjectRequest):
    """
    Check a newly proposed project against an existing corpus.
    Used for real-time duplicate gating at project submission.
    """
    try:
        matches = detector.check_new_project(
            req.new_project,
            req.existing_projects,
            threshold=req.threshold,
        )

        highest_score = matches[0].potential_duplicate_score if matches else 0
        is_flagged    = highest_score >= 60   # HIGH or above

        recommendation = (
            "🔴 REJECT/HOLD: High Potential Duplicate Score detected with existing sanctioned project."
            if is_flagged else
            "🟢 CLEAR: Low duplicate risk — project appears sufficiently distinct."
        )

        return {
            "status": "success",
            "is_duplicate_flagged": is_flagged,
            "highest_risk_score": highest_score / 100,
            "highest_potential_duplicate_score": highest_score,
            "recommendation": recommendation,
            "top_matches": [_pair_to_dict(m) for m in matches[:5]],
        }
    except Exception as e:
        logger.exception("Error in /check-new-project")
        raise HTTPException(status_code=500, detail=str(e))
