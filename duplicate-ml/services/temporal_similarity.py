"""
Execution-period overlap scoring using real date arithmetic.

Returns the ratio of the overlapping calendar days to the union of
both projects total duration. This is a Jaccard-style interval overlap.

  overlap_ratio = max(0, overlap_days) / union_days

Returns None (not 0.85) when dates are missing, so the scoring layer
can renormalise weights. Never uses a hardcoded fallback score.
"""
from __future__ import annotations

from datetime import date
from typing import Optional

from dateutil import parser as dateparser


def _parse_date(s: Optional[str]) -> Optional[date]:
    """Parse an ISO date string to a date object, or return None on failure."""
    if not s:
        return None
    try:
        return dateparser.parse(s).date()
    except Exception:
        return None


def temporal_similarity(
    start_a: Optional[str], end_a: Optional[str],
    start_b: Optional[str], end_b: Optional[str]
) -> Optional[float]:
    """
    Return Jaccard interval overlap ratio [0.0, 1.0], or None if dates missing.

    Formula:
        overlap_days = max(0, min(end_a, end_b) - max(start_a, start_b)).days
        union_days   = (max(end_a, end_b) - min(start_a, start_b)).days
        score        = overlap_days / union_days  (0 if union == 0)

    A score of 1.0 means both projects have exactly the same execution window.
    A score of 0.0 means no overlap whatsoever.
    """
    sa = _parse_date(start_a)
    ea = _parse_date(end_a)
    sb = _parse_date(start_b)
    eb = _parse_date(end_b)

    # Require at least start dates from both projects
    if sa is None or sb is None:
        return None

    # If end dates are missing, treat end = start (instantaneous project)
    ea = ea or sa
    eb = eb or sb

    # Ensure logical order
    if ea < sa:
        sa, ea = ea, sa
    if eb < sb:
        sb, eb = eb, sb

    overlap_start = max(sa, sb)
    overlap_end   = min(ea, eb)
    overlap_days  = max(0, (overlap_end - overlap_start).days)

    union_start = min(sa, sb)
    union_end   = max(ea, eb)
    union_days  = (union_end - union_start).days

    if union_days == 0:
        # Both projects have the same single day — perfect overlap
        return 1.0

    return round(overlap_days / union_days, 4)
