"""
Project category similarity using a taxonomy mapping.

Rather than exact-string match only, this module understands that
"Roads & Connectivity" and "Road Construction" are closely related categories.

Scores:
  1.0  →  exact same category (case-insensitive)
  0.7  →  closely related categories (same macro-sector)
  0.4  →  distantly related categories
  0.0  →  clearly unrelated categories
  None →  one or both categories missing (signal absent)
"""
from __future__ import annotations

from typing import Optional

# ── Category taxonomy ────────────────────────────────────────────────────────
# Maps canonical group names → set of category strings that belong to that group.
# Categories in the SAME group get score 0.7 if they are different strings.
CATEGORY_GROUPS: dict[str, set[str]] = {
    "roads_connectivity": {
        "roads & connectivity", "road construction", "roads and connectivity",
        "road", "pathway", "concrete road", "cc road", "paving", "connectivity"
    },
    "community_infrastructure": {
        "community infrastructure", "community hall", "community centre",
        "public building", "panchayat bhavan", "multipurpose hall",
        "social infrastructure"
    },
    "drinking_water": {
        "drinking water", "water supply", "borewell", "tube well",
        "hand pump", "water facility", "potable water"
    },
    "public_energy_amenities": {
        "public energy & amenities", "street lighting", "solar lights",
        "solar street lights", "led lights", "illumination", "electrification",
        "power"
    },
    "education": {
        "education", "school building", "school", "classroom",
        "toilet block", "educational infrastructure"
    },
    "health": {
        "health", "health centre", "hospital", "dispensary",
        "primary health centre", "phc", "sanitation"
    },
    "sports_recreation": {
        "sports", "stadium", "playground", "recreation", "parks",
        "sports infrastructure"
    },
    "drainage_sewerage": {
        "drainage", "sewerage", "nala", "canal", "drainage channel",
        "stormwater"
    },
}

# Macro-sector groupings for distant-relation score
MACRO_SECTORS: list[frozenset[str]] = [
    frozenset({"roads_connectivity", "drainage_sewerage"}),           # civil infra
    frozenset({"community_infrastructure", "sports_recreation"}),      # public buildings
    frozenset({"drinking_water", "health"}),                           # health & water
    frozenset({"public_energy_amenities", "education"}),               # amenities
]


def _normalise(cat: str) -> str:
    return cat.lower().strip()


def _find_group(cat_norm: str) -> Optional[str]:
    """Return the group name for a normalised category string, or None."""
    for group, members in CATEGORY_GROUPS.items():
        if cat_norm in members:
            return group
    # Fuzzy: check if any member is a substring of the category string
    for group, members in CATEGORY_GROUPS.items():
        for member in members:
            if member in cat_norm or cat_norm in member:
                return group
    return None


def category_similarity(cat_a: Optional[str], cat_b: Optional[str]) -> Optional[float]:
    """
    Return a score in {0.0, 0.4, 0.7, 1.0} or None if data missing.

    None is intentionally returned (not 0.0) for missing data, so the
    scoring layer can renormalise weights accordingly.
    """
    if cat_a is None or cat_b is None:
        return None

    na, nb = _normalise(cat_a), _normalise(cat_b)

    # Exact match
    if na == nb:
        return 1.0

    # Same group
    ga, gb = _find_group(na), _find_group(nb)
    if ga is not None and gb is not None:
        if ga == gb:
            return 0.7
        # Check macro-sector
        for macro in MACRO_SECTORS:
            if ga in macro and gb in macro:
                return 0.4

    return 0.0
