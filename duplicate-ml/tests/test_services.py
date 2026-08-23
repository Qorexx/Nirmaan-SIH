"""
Unit tests for all ML service modules.
Run from duplicate-ml/ directory: pytest tests/ -v
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import math
import pytest

# ── Location similarity tests ────────────────────────────────────────────────
from services.location_similarity import haversine_distance_m, distance_to_score, location_similarity

def test_haversine_same_point():
    d = haversine_distance_m(25.3176, 82.9739, 25.3176, 82.9739)
    assert d == 0.0

def test_haversine_known_distance():
    # Varanasi pair: (25.3176, 82.9739) vs (25.3180, 82.9741) ≈ 48m
    d = haversine_distance_m(25.3176, 82.9739, 25.3180, 82.9741)
    assert 40 < d < 60, f"Expected ~48m, got {d}m"

def test_distance_to_score_same_location():
    assert distance_to_score(0) == 1.0
    assert distance_to_score(5) == 1.0

def test_distance_to_score_very_close():
    s50 = distance_to_score(50)
    assert 0.80 < s50 <= 0.98, f"Score at 50m should be > 0.80, got {s50}"

def test_distance_to_score_far():
    assert distance_to_score(3000) == 0.0

def test_distance_to_score_monotone_decreasing():
    dists = [0, 5, 50, 200, 1000, 2500]
    scores = [distance_to_score(d) for d in dists]
    for i in range(len(scores) - 1):
        assert scores[i] >= scores[i+1], f"Score not monotone at index {i}"

def test_location_similarity_missing_coords():
    dist, score = location_similarity(None, None, 25.0, 80.0)
    assert dist is None
    assert score is None

def test_location_similarity_real():
    dist, score = location_similarity(25.3176, 82.9739, 25.3180, 82.9741)
    assert dist is not None and dist < 100
    assert score is not None and score > 0.80


# ── Category similarity tests ────────────────────────────────────────────────
from services.category_similarity import category_similarity

def test_category_exact_match():
    assert category_similarity("Roads & Connectivity", "Roads & Connectivity") == 1.0

def test_category_same_group():
    score = category_similarity("Community Infrastructure", "Community Hall")
    assert score is not None and score >= 0.7

def test_category_different():
    score = category_similarity("Drinking Water", "Roads & Connectivity")
    assert score is not None and score == 0.0

def test_category_missing():
    assert category_similarity(None, "Drinking Water") is None
    assert category_similarity("Roads", None) is None


# ── Temporal similarity tests ────────────────────────────────────────────────
from services.temporal_similarity import temporal_similarity

def test_temporal_full_overlap():
    score = temporal_similarity("2024-01-01", "2024-12-31", "2024-01-01", "2024-12-31")
    assert score == 1.0

def test_temporal_no_overlap():
    score = temporal_similarity("2024-01-01", "2024-03-31", "2024-05-01", "2024-08-31")
    assert score == 0.0

def test_temporal_partial_overlap():
    # A: Jan-Jun, B: Apr-Sep → overlap is Apr-Jun = 3 months, union is Jan-Sep = 9 months ≈ 0.33
    score = temporal_similarity("2024-01-01", "2024-06-30", "2024-04-01", "2024-09-30")
    assert score is not None
    assert 0.2 < score < 0.5, f"Expected partial overlap ~0.33, got {score}"

def test_temporal_missing_dates():
    assert temporal_similarity(None, "2024-08-30", None, "2024-11-30") is None

def test_temporal_varanasi_pair():
    # MPLAD-2024-1042: Feb-Aug, MPLAD-2025-0319: Apr-Nov
    # overlap: Apr-Aug = ~5 months, union: Feb-Nov = ~10 months ≈ 0.5
    score = temporal_similarity("2024-02-01", "2024-08-30", "2024-04-01", "2024-11-30")
    assert score is not None
    assert 0.35 < score < 0.65, f"Expected ~0.5, got {score}"


# ── Scoring tests ────────────────────────────────────────────────────────────
from services.scoring import compute_score

def test_scoring_all_signals_high():
    r = compute_score(text_sim=0.9, location_sim=0.95, category_sim=1.0, temporal_sim=0.8)
    assert r.potential_duplicate_score >= 90
    assert r.risk_level == "CRITICAL REVIEW"

def test_scoring_all_signals_low():
    r = compute_score(text_sim=0.1, location_sim=0.0, category_sim=0.0, temporal_sim=0.0)
    assert r.potential_duplicate_score < 40
    assert r.risk_level == "LOW"

def test_scoring_missing_location_renormalises():
    # With location missing, text gets more weight
    r_full = compute_score(text_sim=0.8, location_sim=0.5, category_sim=1.0, temporal_sim=0.5)
    r_no_loc = compute_score(text_sim=0.8, location_sim=None, category_sim=1.0, temporal_sim=0.5)
    # Both should return valid scores
    assert 0 <= r_full.potential_duplicate_score <= 100
    assert 0 <= r_no_loc.potential_duplicate_score <= 100
    # Effective weights should sum to 1
    assert abs(sum(r_no_loc.effective_weights.values()) - 1.0) < 0.001

def test_scoring_no_signals():
    r = compute_score(text_sim=None, location_sim=None, category_sim=None, temporal_sim=None)
    assert r.potential_duplicate_score == 0
    assert r.risk_level == "LOW"

def test_scoring_risk_tiers():
    assert compute_score(0.95, 0.98, 1.0, 0.9).risk_level == "CRITICAL REVIEW"
    assert compute_score(0.80, 0.85, 1.0, 0.7).risk_level in ("VERY HIGH", "CRITICAL REVIEW")
    assert compute_score(0.50, 0.50, 0.7, 0.5).risk_level in ("MODERATE", "HIGH")
    assert compute_score(0.10, 0.05, 0.0, 0.0).risk_level == "LOW"
