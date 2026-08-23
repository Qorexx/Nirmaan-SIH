"""
Main orchestrator: FAISS candidate retrieval + full multi-factor scoring pipeline.

Flow for find-duplicates:
  1. Build FAISS index from all project embeddings (once per request)
  2. For each project, query FAISS for top-K candidates
  3. For each candidate pair (above embedding threshold), compute all 4 signals
  4. Apply weighted scoring, produce DuplicatePairResult
  5. Deduplicate pairs, filter by threshold, sort by score descending

Flow for compare-pair:
  1. Embed both projects directly
  2. Compute cosine similarity
  3. Compute all other signals
  4. Score and explain

Flow for check-new-project:
  1. Embed new project
  2. Search existing FAISS index (or brute-force if small set)
  3. Score top candidates
  4. Return sorted matches above threshold
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

from schemas.project import ProjectRecord
from services.embeddings import embed, embed_batch, build_text, cosine_similarity
from services.faiss_index import FAISSProjectIndex
from services.location_similarity import location_similarity
from services.category_similarity import category_similarity
from services.temporal_similarity import temporal_similarity
from services.scoring import compute_score, ScoreResult
from services.explanation import build_explanation, build_reasons

logger = logging.getLogger(__name__)

# Minimum embedding cosine similarity to proceed to full scoring
# (avoids scoring completely unrelated pairs)
FAISS_PREFILTER_THRESHOLD = 0.20

# FAISS k: number of neighbours to retrieve per query
FAISS_K = 15


@dataclass
class DuplicatePairResult:
    # Core identity
    pair_id: str
    project_a: dict
    project_b: dict

    # Score (replaces "duplicate_probability" — this is NOT a calibrated classifier probability)
    potential_duplicate_score: int   # 0-100

    # Frontend backward-compatibility aliases (mapped in adapter layer)
    similarity_percentage: int       # same as potential_duplicate_score
    duplicate_probability: float     # same as score/100 (kept for backward compat)
    risk_level: str
    risk_badge: str

    # Human-readable output
    explanation: str
    reasons: list[str]

    # Score breakdown (frontend expects these exact field names)
    score_breakdown: dict

    # For Person 6 Risk Engine export
    metadata: dict = field(default_factory=dict)


def _project_to_dict(p: ProjectRecord) -> dict:
    """Convert a ProjectRecord to a JSON-serialisable dict, normalising coordinates."""
    d = p.model_dump(exclude_none=False)
    # Always include nested coordinates object for frontend compatibility
    if p.latitude is not None and p.longitude is not None:
        d["coordinates"] = {"lat": p.latitude, "lng": p.longitude}
    return d


def _score_pair(
    proj_a: ProjectRecord,
    proj_b: ProjectRecord,
    text_sim: float,
) -> DuplicatePairResult:
    """Run full multi-factor analysis on a project pair."""

    # --- Geographic ---
    dist_m, loc_sim = location_similarity(
        proj_a.latitude, proj_a.longitude,
        proj_b.latitude, proj_b.longitude,
    )

    # --- Category ---
    cat_sim = category_similarity(proj_a.category, proj_b.category)

    # --- Temporal ---
    temp_sim = temporal_similarity(
        proj_a.execution_start, proj_a.execution_end,
        proj_b.execution_start, proj_b.execution_end,
    )

    # --- Composite score ---
    score_result: ScoreResult = compute_score(
        text_sim=text_sim,
        location_sim=loc_sim,
        category_sim=cat_sim,
        temporal_sim=temp_sim,
    )

    final_score = score_result.potential_duplicate_score

    # --- Explanation ---
    explanation = build_explanation(
        text_sim=text_sim,
        location_sim=loc_sim,
        distance_m=dist_m,
        category_sim=cat_sim,
        temporal_sim=temp_sim,
        risk_badge=score_result.risk_badge,
        final_score=final_score,
    )
    reasons = build_reasons(
        text_sim=text_sim,
        location_sim=loc_sim,
        distance_m=dist_m,
        category_sim=cat_sim,
        temporal_sim=temp_sim,
    )

    # --- Score breakdown (frontend field names preserved) ---
    text_pct = round(text_sim * 100) if text_sim is not None else None
    loc_pct  = round(loc_sim * 100)  if loc_sim  is not None else None

    score_breakdown = {
        "text_similarity":              round(text_sim, 4) if text_sim is not None else None,
        "text_similarity_percentage":   text_pct,
        "location_proximity":           round(loc_sim, 4)  if loc_sim  is not None else None,
        "location_proximity_percentage": loc_pct,
        "distance_meters":              dist_m,
        "category_match":               round(cat_sim, 4)  if cat_sim  is not None else None,
        "time_overlap":                 round(temp_sim, 4) if temp_sim is not None else None,
        "effective_weights":            score_result.effective_weights,
    }

    return DuplicatePairResult(
        pair_id=f"DUP-{proj_a.id}-{proj_b.id}",
        project_a=_project_to_dict(proj_a),
        project_b=_project_to_dict(proj_b),
        potential_duplicate_score=final_score,
        similarity_percentage=final_score,
        duplicate_probability=round(final_score / 100, 4),
        risk_level=score_result.risk_level,
        risk_badge=score_result.risk_badge,
        explanation=explanation,
        reasons=reasons,
        score_breakdown=score_breakdown,
        metadata={
            "model": "paraphrase-multilingual-MiniLM-L12-v2",
            "embedding_cosine_similarity": round(text_sim, 4) if text_sim is not None else None,
            "faiss_prefilter_threshold": FAISS_PREFILTER_THRESHOLD,
        },
    )


def compare_pair(proj_a: ProjectRecord, proj_b: ProjectRecord) -> DuplicatePairResult:
    """Directly compare two projects. Used by /compare-pair endpoint."""
    text_a = build_text(proj_a.title, proj_a.description)
    text_b = build_text(proj_b.title, proj_b.description)
    emb_a  = embed(text_a)
    emb_b  = embed(text_b)
    text_sim = cosine_similarity(emb_a, emb_b)
    return _score_pair(proj_a, proj_b, text_sim)


def find_duplicates(
    projects: list[ProjectRecord],
    threshold: float = 40.0,
) -> list[DuplicatePairResult]:
    """
    Find all duplicate pairs among a list of projects.

    Uses FAISS for efficient candidate retrieval, then scores each
    candidate pair with all four signals.

    Returns pairs with potential_duplicate_score >= threshold, sorted
    by score descending.
    """
    n = len(projects)
    if n < 2:
        return []

    # Build text corpus and embeddings
    texts = [build_text(p.title, p.description) for p in projects]
    embeddings = embed_batch(texts)

    # Build FAISS index
    project_ids = [p.id for p in projects]
    findex = FAISSProjectIndex()
    findex.build(embeddings, project_ids)

    id_to_proj  = {p.id: p      for p in projects}
    id_to_emb   = {p.id: embeddings[i] for i, p in enumerate(projects)}

    seen_pairs: set[frozenset] = set()
    results: list[DuplicatePairResult] = []

    for i, proj_a in enumerate(projects):
        candidates = findex.search(embeddings[i], k=FAISS_K)

        for cand_id, raw_cosine_sim in candidates:
            if cand_id == proj_a.id:
                continue  # skip self

            pair_key = frozenset({proj_a.id, cand_id})
            if pair_key in seen_pairs:
                continue
            seen_pairs.add(pair_key)

            # Pre-filter by embedding similarity
            if raw_cosine_sim < FAISS_PREFILTER_THRESHOLD:
                continue

            proj_b = id_to_proj[cand_id]
            result = _score_pair(proj_a, proj_b, text_sim=raw_cosine_sim)

            if result.potential_duplicate_score >= threshold:
                results.append(result)

    results.sort(key=lambda r: r.potential_duplicate_score, reverse=True)
    return results


def check_new_project(
    new_project: ProjectRecord,
    existing_projects: list[ProjectRecord],
    threshold: float = 40.0,
) -> list[DuplicatePairResult]:
    """
    Compare a new (proposed) project against an existing corpus.

    Returns a list of flagged existing projects sorted by score descending.
    """
    if not existing_projects:
        return []

    # Embed new project
    new_text = build_text(new_project.title, new_project.description)
    new_emb  = embed(new_text)

    # Build or use brute-force (small corpus acceptable for real-time check)
    existing_texts = [build_text(p.title, p.description) for p in existing_projects]
    existing_embs  = embed_batch(existing_texts)

    results: list[DuplicatePairResult] = []

    for i, proj_b in enumerate(existing_projects):
        text_sim = cosine_similarity(new_emb, existing_embs[i])
        if text_sim < FAISS_PREFILTER_THRESHOLD:
            continue
        result = _score_pair(new_project, proj_b, text_sim=text_sim)
        if result.potential_duplicate_score >= threshold:
            results.append(result)

    results.sort(key=lambda r: r.potential_duplicate_score, reverse=True)
    return results
