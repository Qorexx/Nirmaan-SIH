"""
Geographic proximity scoring using the Haversine formula.

All distance thresholds are documented constants — never hardcoded
magic numbers mixed into production logic.

Scoring curve (configurable):
  0 – 10 m       → 1.00  (essentially same location)
  10 – 100 m     → exponential decay from 0.98 to 0.80
  100 – 500 m    → exponential decay from 0.80 to 0.40
  500 – 2000 m   → linear decay from 0.40 to 0.10
  > 2000 m       → 0.00
"""
from __future__ import annotations

import math
from typing import Optional

# ── Configurable threshold constants ────────────────────────────────────────
SAME_LOCATION_THRESHOLD_M    = 10      # below this → score 1.0
VERY_CLOSE_THRESHOLD_M       = 100     # below this → exponential near-perfect
MODERATE_CLOSE_THRESHOLD_M   = 500     # below this → exponential moderate
FAR_THRESHOLD_M              = 2000    # below this → linear decay
# Above FAR_THRESHOLD_M → score 0.0


def haversine_distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Return the great-circle distance in metres between two GPS coordinates
    using the Haversine formula.
    """
    R = 6_371_000.0  # Earth radius in metres

    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi        = math.radians(lat2 - lat1)
    dlambda     = math.radians(lon2 - lon1)

    a = (math.sin(dphi / 2) ** 2
         + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return round(R * c, 1)  # metres, rounded to 0.1 m


def distance_to_score(distance_m: float) -> float:
    """
    Convert a real Haversine distance (metres) to a proximity score [0, 1].

    Uses a piecewise exponential + linear curve so that:
    - Tiny distances produce near-perfect scores
    - The decay is smooth and physically motivated
    - No arbitrary lookup table / magic percentage

    This function is intentionally pure (no state, no globals) and is unit-testable.
    """
    if distance_m <= SAME_LOCATION_THRESHOLD_M:
        return 1.0

    if distance_m <= VERY_CLOSE_THRESHOLD_M:
        # Exponential decay: 0.98 → ~0.80 over [10, 100] m
        # score = 0.98 * exp(-k * (d - 10))   with k tuned so score(100) ≈ 0.80
        k = math.log(0.98 / 0.80) / (VERY_CLOSE_THRESHOLD_M - SAME_LOCATION_THRESHOLD_M)
        score = 0.98 * math.exp(-k * (distance_m - SAME_LOCATION_THRESHOLD_M))
        return round(min(0.98, max(0.0, score)), 4)

    if distance_m <= MODERATE_CLOSE_THRESHOLD_M:
        # Exponential decay: 0.80 → ~0.40 over [100, 500] m
        k = math.log(0.80 / 0.40) / (MODERATE_CLOSE_THRESHOLD_M - VERY_CLOSE_THRESHOLD_M)
        score = 0.80 * math.exp(-k * (distance_m - VERY_CLOSE_THRESHOLD_M))
        return round(min(0.80, max(0.0, score)), 4)

    if distance_m <= FAR_THRESHOLD_M:
        # Linear decay: 0.40 → 0.00 over [500, 2000] m
        ratio = (distance_m - MODERATE_CLOSE_THRESHOLD_M) / (FAR_THRESHOLD_M - MODERATE_CLOSE_THRESHOLD_M)
        score = 0.40 * (1.0 - ratio)
        return round(max(0.0, score), 4)

    return 0.0


def location_similarity(
    lat_a: Optional[float], lon_a: Optional[float],
    lat_b: Optional[float], lon_b: Optional[float]
) -> tuple[Optional[float], Optional[float]]:
    """
    Return (distance_m, proximity_score) or (None, None) if coordinates missing.

    Returns None (not 0) when data is missing so the scoring layer can
    renormalise weights rather than penalising missing data unfairly.
    """
    if any(v is None for v in (lat_a, lon_a, lat_b, lon_b)):
        return None, None

    dist = haversine_distance_m(lat_a, lon_a, lat_b, lon_b)
    score = distance_to_score(dist)
    return dist, score
