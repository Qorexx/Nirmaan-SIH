"""
Human-readable explanation generator.

Generates evidence-based reason strings from actual computed values.
No hardcoded descriptions — every claim is derived from real signal scores.
"""
from __future__ import annotations

from typing import Optional


def build_explanation(
    text_sim:            Optional[float],
    location_sim:        Optional[float],
    distance_m:          Optional[float],
    category_sim:        Optional[float],
    temporal_sim:        Optional[float],
    risk_badge:          str,
    final_score:         int,
) -> str:
    """Return a one-line plain-text explanation string for the AI output banner."""
    parts = []

    if text_sim is not None:
        parts.append(f"Description similarity: {round(text_sim * 100)}%")

    if location_sim is not None and distance_m is not None:
        dist_str = f"{distance_m:.0f}m apart" if distance_m < 10_000 else f"{distance_m/1000:.1f}km apart"
        parts.append(f"Location proximity: {round(location_sim * 100)}% ({dist_str})")
    elif location_sim is not None:
        parts.append(f"Location proximity: {round(location_sim * 100)}%")

    if category_sim is not None:
        if category_sim >= 1.0:
            parts.append("Same project category")
        elif category_sim >= 0.6:
            parts.append("Closely related category")
        else:
            parts.append("Different category")

    if temporal_sim is not None:
        pct = round(temporal_sim * 100)
        if pct >= 50:
            parts.append(f"Overlapping execution period ({pct}% overlap)")
        elif pct > 0:
            parts.append(f"Partial execution overlap ({pct}%)")
        else:
            parts.append("Non-overlapping execution periods")

    evidence = " | ".join(parts) if parts else "Insufficient data for full comparison"
    return f"{risk_badge} — {final_score}% Potential Duplicate Score. {evidence}."


def build_reasons(
    text_sim:            Optional[float],
    location_sim:        Optional[float],
    distance_m:          Optional[float],
    category_sim:        Optional[float],
    temporal_sim:        Optional[float],
) -> list[str]:
    """
    Return a structured list of evidence strings for Person 6 Risk Engine export.
    Each item is a self-contained finding.
    """
    reasons: list[str] = []

    if text_sim is not None:
        pct = round(text_sim * 100)
        if pct >= 80:
            reasons.append(f"STRONG TEXT MATCH: Semantic similarity is {pct}% — descriptions are nearly identical in meaning.")
        elif pct >= 60:
            reasons.append(f"MODERATE TEXT MATCH: Semantic similarity is {pct}% — descriptions share significant common subject matter.")
        elif pct >= 40:
            reasons.append(f"WEAK TEXT MATCH: Semantic similarity is {pct}% — descriptions have some topical overlap.")
        else:
            reasons.append(f"LOW TEXT MATCH: Semantic similarity is {pct}% — descriptions appear largely distinct.")

    if distance_m is not None:
        if distance_m <= 10:
            reasons.append(f"SAME LOCATION: Projects are {distance_m:.1f}m apart — likely targeting the same physical site.")
        elif distance_m <= 100:
            reasons.append(f"VERY CLOSE PROXIMITY: Projects are {distance_m:.0f}m apart — within walking distance of each other.")
        elif distance_m <= 500:
            reasons.append(f"CLOSE PROXIMITY: Projects are {distance_m:.0f}m apart — within the same locality.")
        elif distance_m <= 2000:
            reasons.append(f"MODERATE PROXIMITY: Projects are {distance_m:.0f}m apart — in the same general area.")
        else:
            reasons.append(f"DISTANT LOCATIONS: Projects are {distance_m/1000:.1f}km apart — geographically separated.")

    if category_sim is not None:
        if category_sim >= 1.0:
            reasons.append("CATEGORY EXACT MATCH: Both projects belong to the same project category.")
        elif category_sim >= 0.6:
            reasons.append("CATEGORY RELATED: Projects are in closely related categories within the same sector.")
        elif category_sim >= 0.3:
            reasons.append("CATEGORY DISTANT: Projects are in distantly related categories.")
        else:
            reasons.append("CATEGORY MISMATCH: Projects belong to clearly different categories.")

    if temporal_sim is not None:
        pct = round(temporal_sim * 100)
        if pct >= 80:
            reasons.append(f"HIGH TEMPORAL OVERLAP: Execution windows overlap {pct}% — projects run concurrently.")
        elif pct >= 40:
            reasons.append(f"PARTIAL TEMPORAL OVERLAP: Execution windows overlap {pct}% — projects share part of their timeline.")
        elif pct > 0:
            reasons.append(f"MINIMAL TEMPORAL OVERLAP: Execution windows overlap only {pct}%.")
        else:
            reasons.append("NO TEMPORAL OVERLAP: Projects have non-overlapping execution periods.")

    return reasons
