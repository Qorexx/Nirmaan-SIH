"""
Multi-factor scoring and risk classification.

Potential Duplicate Score (0-100) is a weighted combination of four signals.
When a signal is missing (None), its weight is redistributed proportionally
among the available signals — the score is never artificially inflated or
deflated by absent data.

Default weights (configurable):
  text_similarity    50%
  location_proximity 25%
  category_match     15%
  temporal_overlap   10%

Risk thresholds (spec-mandated):
  0  - 39   LOW
  40 - 59   MODERATE
  60 - 74   HIGH
  75 - 89   VERY HIGH
  90 - 100  CRITICAL REVIEW
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

# ── Default weights ──────────────────────────────────────────────────────────
DEFAULT_WEIGHTS = {
    "text":     0.50,
    "location": 0.25,
    "category": 0.15,
    "temporal": 0.10,
}

# ── Risk tier thresholds ─────────────────────────────────────────────────────
RISK_TIERS = [
    (90, "CRITICAL REVIEW", "🔴 Critical Duplicate Risk"),
    (75, "VERY HIGH",       "🟠 Very High Overlap Risk"),
    (60, "HIGH",            "🟠 High Risk Overlap"),
    (40, "MODERATE",        "🟡 Moderate Similarity"),
    (0,  "LOW",             "🟢 Low Similarity"),
]


@dataclass
class ScoreResult:
    potential_duplicate_score: int         # 0–100
    risk_level: str
    risk_badge: str
    effective_weights: dict[str, float]    # weights after renormalisation
    signal_scores: dict[str, Optional[float]]  # raw [0,1] per signal


def compute_score(
    text_sim:     Optional[float],
    location_sim: Optional[float],
    category_sim: Optional[float],
    temporal_sim: Optional[float],
    weights: dict[str, float] = DEFAULT_WEIGHTS,
) -> ScoreResult:
    """
    Combine four similarity signals into a Potential Duplicate Score.

    Parameters
    ----------
    text_sim, location_sim, category_sim, temporal_sim :
        Raw similarity scores in [0, 1] from each service module.
        Pass None to indicate the signal is unavailable.
    weights :
        Base weights (must sum to 1.0).

    Returns
    -------
    ScoreResult with final score (0-100), risk tier, and diagnostic info.
    """
    signal_map = {
        "text":     text_sim,
        "location": location_sim,
        "category": category_sim,
        "temporal": temporal_sim,
    }

    # Filter to available signals only
    available = {k: v for k, v in signal_map.items() if v is not None}

    if not available:
        # No signals at all — return score 0, LOW risk
        return ScoreResult(
            potential_duplicate_score=0,
            risk_level="LOW",
            risk_badge="🟢 Low Similarity",
            effective_weights={k: 0.0 for k in signal_map},
            signal_scores=signal_map,
        )

    # Renormalise weights to available signals only
    raw_weight_sum = sum(weights[k] for k in available)
    eff_weights = {k: (weights[k] / raw_weight_sum if k in available else 0.0)
                   for k in signal_map}

    # Compute weighted score
    raw_score = sum(eff_weights[k] * available[k] for k in available)
    final_score = max(0, min(100, round(raw_score * 100)))

    # Determine risk tier
    risk_level, risk_badge = "LOW", "🟢 Low Similarity"
    for threshold, level, badge in RISK_TIERS:
        if final_score >= threshold:
            risk_level, risk_badge = level, badge
            break

    return ScoreResult(
        potential_duplicate_score=final_score,
        risk_level=risk_level,
        risk_badge=risk_badge,
        effective_weights=eff_weights,
        signal_scores=signal_map,
    )
