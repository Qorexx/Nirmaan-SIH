"""
Task 3: SHAP Explainability Utility
=====================================
Provides human-readable explanations for model predictions using SHAP
TreeExplainer (optimized for XGBoost). Returns the top-N contributing
features ranked by absolute SHAP value.
"""

import numpy as np
import shap
from typing import List, Dict, Any


# Human-readable labels for feature names (for government official consumption)
FEATURE_DISPLAY_NAMES = {
    "state": "Project state/location",
    "constituency_type": "Constituency type (Lok/Rajya Sabha)",
    "project_category": "Project category",
    "terrain_difficulty": "Terrain difficulty",
    "estimated_cost": "Estimated project cost",
    "sanctioned_amount": "Sanctioned amount",
    "expected_duration_days": "Expected project duration",
    "elapsed_days": "Time already elapsed",
    "progress_pct": "Current progress percentage",
    "contractor_past_delays": "Contractor's history of delays",
    "monsoon_overlap_days": "Monsoon season overlap",
    "material_inflation_index": "Material price inflation",
    "labor_shortage_index": "Labor shortage severity",
    "sanction_year": "Year of sanction",
}


def get_top_factors(
    model,
    preprocessed_input: np.ndarray,
    feature_names: list,
    top_n: int = 3,
    use_display_names: bool = False,
) -> List[str]:
    """
    Extract the top-N driving factors for a single prediction using SHAP.

    Args:
        model: Trained XGBRegressor model.
        preprocessed_input: Single sample, already preprocessed (shape: 1×n_features).
        feature_names: List of feature names in the same order as preprocessed columns.
        top_n: Number of top factors to return.
        use_display_names: If True, returns human-readable names instead of feature IDs.

    Returns:
        List of top-N feature names ranked by absolute SHAP impact.
    """
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(preprocessed_input)

    # shap_values shape: (1, n_features) — take the first (only) sample
    if isinstance(shap_values, list):
        shap_values = shap_values[0]

    sample_shap = np.abs(shap_values[0]) if shap_values.ndim > 1 else np.abs(shap_values)

    # Rank features by absolute SHAP value (descending)
    top_indices = np.argsort(sample_shap)[::-1][:top_n]

    factors = []
    for idx in top_indices:
        if idx < len(feature_names):
            name = feature_names[idx]
            if use_display_names and name in FEATURE_DISPLAY_NAMES:
                factors.append(FEATURE_DISPLAY_NAMES[name])
            else:
                factors.append(name)

    return factors


def get_full_explanation(
    model,
    preprocessed_input: np.ndarray,
    feature_names: list,
    top_n: int = 3,
) -> Dict[str, Any]:
    """
    Get a full SHAP explanation including factor names, SHAP values,
    and direction (increasing/decreasing the prediction).

    Args:
        model: Trained XGBRegressor.
        preprocessed_input: Single preprocessed sample.
        feature_names: Feature name list.
        top_n: Number of top factors.

    Returns:
        Dictionary with detailed explanation breakdown.
    """
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(preprocessed_input)

    if isinstance(shap_values, list):
        shap_values = shap_values[0]

    sample_shap = shap_values[0] if shap_values.ndim > 1 else shap_values
    abs_shap = np.abs(sample_shap)
    top_indices = np.argsort(abs_shap)[::-1][:top_n]

    explanation = {
        "base_value": float(explainer.expected_value),
        "factors": [],
    }

    for idx in top_indices:
        if idx < len(feature_names):
            factor = {
                "feature": feature_names[idx],
                "display_name": FEATURE_DISPLAY_NAMES.get(
                    feature_names[idx], feature_names[idx]
                ),
                "shap_value": float(sample_shap[idx]),
                "abs_impact": float(abs_shap[idx]),
                "direction": "increases" if sample_shap[idx] > 0 else "decreases",
            }
            explanation["factors"].append(factor)

    return explanation


if __name__ == "__main__":
    # Quick self-test with a dummy model
    print("[Task 3] SHAP Explainer module loaded successfully.")
    print("         Use get_top_factors() for factor names.")
    print("         Use get_full_explanation() for detailed breakdown.")
