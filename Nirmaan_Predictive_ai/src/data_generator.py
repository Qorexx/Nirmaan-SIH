"""
Task 1: Synthetic MPLADS Data Generator
========================================
Generates 8,000 realistic project records matching the MPLADS eSAKSHI portal
data structure. Embeds strong causal relationships between features and targets
so that trained models learn meaningful, actionable patterns.

Target columns:
  - actual_final_cost: True final cost (drives cost overrun calculation)
  - actual_delay_days: True delay beyond expected_duration_days
"""

import os
import numpy as np
import pandas as pd
from pathlib import Path


# ---------------------------------------------------------------------------
# Constants — aligned with real MPLADS dashboard categories and geography
# ---------------------------------------------------------------------------

INDIAN_STATES = [
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
    "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka",
    "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya",
    "Mizoram", "Nagaland", "Odisha", "Punjab", "Rajasthan", "Sikkim",
    "Tamil Nadu", "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand",
    "West Bengal", "Andaman and Nicobar Islands", "Chandigarh",
    "Dadra and Nagar Haveli and Daman and Diu", "Delhi", "Jammu and Kashmir",
    "Ladakh", "Lakshadweep", "Puducherry",
]

# MPLADS eligible work categories from scheme guidelines
PROJECT_CATEGORIES = [
    "Roads", "Sanitation", "Education", "Healthcare", "Drinking Water",
    "Community Halls", "Sports Infrastructure", "Bridges", "Electrification",
    "Other Public Assets",
]

TERRAIN_TYPES = ["PLAIN", "HILLY", "COASTAL", "DESERT"]

CONSTITUENCY_TYPES = ["LOK_SABHA", "RAJYA_SABHA"]

# Category-level complexity multipliers (some project types are inherently harder)
CATEGORY_COMPLEXITY = {
    "Roads": 1.0, "Sanitation": 0.8, "Education": 0.9, "Healthcare": 1.1,
    "Drinking Water": 0.85, "Community Halls": 0.7, "Sports Infrastructure": 0.95,
    "Bridges": 1.3, "Electrification": 1.05, "Other Public Assets": 0.9,
}

# State → likely terrain mapping for realistic data
STATE_TERRAIN_WEIGHTS = {
    "Himachal Pradesh": [0.1, 0.7, 0.0, 0.2],
    "Uttarakhand": [0.2, 0.7, 0.0, 0.1],
    "Jammu and Kashmir": [0.1, 0.8, 0.0, 0.1],
    "Ladakh": [0.0, 0.8, 0.0, 0.2],
    "Sikkim": [0.1, 0.8, 0.0, 0.1],
    "Arunachal Pradesh": [0.1, 0.8, 0.0, 0.1],
    "Meghalaya": [0.2, 0.7, 0.0, 0.1],
    "Nagaland": [0.1, 0.8, 0.0, 0.1],
    "Manipur": [0.2, 0.7, 0.0, 0.1],
    "Mizoram": [0.1, 0.8, 0.0, 0.1],
    "Rajasthan": [0.3, 0.1, 0.0, 0.6],
    "Gujarat": [0.4, 0.1, 0.3, 0.2],
    "Goa": [0.2, 0.1, 0.7, 0.0],
    "Kerala": [0.3, 0.2, 0.5, 0.0],
    "Tamil Nadu": [0.4, 0.1, 0.4, 0.1],
    "Andhra Pradesh": [0.5, 0.1, 0.3, 0.1],
    "Odisha": [0.4, 0.2, 0.3, 0.1],
    "West Bengal": [0.5, 0.1, 0.3, 0.1],
    "Maharashtra": [0.4, 0.2, 0.3, 0.1],
    "Karnataka": [0.5, 0.2, 0.2, 0.1],
    "Lakshadweep": [0.0, 0.0, 1.0, 0.0],
    "Andaman and Nicobar Islands": [0.1, 0.1, 0.8, 0.0],
}

# Monsoon intensity by state (higher = more disruption)
STATE_MONSOON_INTENSITY = {
    "Kerala": 0.9, "Goa": 0.85, "Maharashtra": 0.8, "Karnataka": 0.75,
    "Assam": 0.9, "Meghalaya": 0.95, "West Bengal": 0.7, "Odisha": 0.75,
    "Andhra Pradesh": 0.65, "Tamil Nadu": 0.5, "Uttar Pradesh": 0.6,
    "Bihar": 0.7, "Jharkhand": 0.65, "Chhattisgarh": 0.6,
    "Madhya Pradesh": 0.55, "Rajasthan": 0.35, "Gujarat": 0.5,
    "Punjab": 0.45, "Haryana": 0.4, "Delhi": 0.4,
    "Himachal Pradesh": 0.6, "Uttarakhand": 0.65,
    "Jammu and Kashmir": 0.4, "Ladakh": 0.15,
}


def _get_terrain(state: str, rng: np.random.Generator) -> str:
    """Assign terrain based on state geography with controlled randomness."""
    weights = STATE_TERRAIN_WEIGHTS.get(state, [0.6, 0.2, 0.1, 0.1])
    return rng.choice(TERRAIN_TYPES, p=weights)


def _compute_monsoon_overlap(
    state: str,
    start_month: int,
    duration_days: int,
    rng: np.random.Generator,
) -> int:
    """
    Calculate how many project days fall within monsoon season (Jun–Sep).
    Uses state-level monsoon intensity to add realistic variance.
    """
    intensity = STATE_MONSOON_INTENSITY.get(state, 0.5)
    # Monsoon months: June(6) through September(9)
    monsoon_months = {6, 7, 8, 9}
    overlap = 0
    for m in range(12):
        month = ((start_month - 1 + m) % 12) + 1
        days_in_month = 30
        if m * 30 > duration_days:
            break
        if month in monsoon_months:
            overlap += int(days_in_month * intensity * rng.uniform(0.8, 1.0))
    return min(overlap, 120)


def generate_dataset(
    n_records: int = 8000,
    seed: int = 42,
    output_dir: str = "data",
) -> pd.DataFrame:
    """
    Generate a realistic synthetic MPLADS dataset with strong causal signals.

    Args:
        n_records: Number of project records to generate.
        seed: Random seed for reproducibility.
        output_dir: Directory to save CSV output.

    Returns:
        DataFrame with all features and target columns.
    """
    rng = np.random.default_rng(seed)
    records = []

    # Pre-generate contractor profiles (200 contractors with varying reliability)
    n_contractors = 200
    contractor_reliability = {
        f"CTR-{i+1:03d}": int(rng.integers(0, 16)) for i in range(n_contractors)
    }

    for i in range(n_records):
        project_id = f"MPLADS-{i+1:04d}"

        # --- Core attributes ---
        state = rng.choice(INDIAN_STATES)
        constituency_type = rng.choice(
            CONSTITUENCY_TYPES, p=[0.65, 0.35]  # More Lok Sabha seats
        )
        project_category = rng.choice(PROJECT_CATEGORIES)
        terrain = _get_terrain(state, rng)
        sanction_year = int(rng.choice([2023, 2024, 2025], p=[0.25, 0.40, 0.35]))

        # --- Financial attributes ---
        # MPLADS per-work cost: log-normal centered around ₹25L, ranging ₹5L–₹5Cr
        # Log-normal clusters around typical values with occasional large projects
        log_cost = rng.normal(loc=14.7, scale=0.9)  # ln(₹25L) ≈ 14.7
        estimated_cost = float(np.clip(np.exp(log_cost), 500_000, 50_000_000))

        # Sanctioned amount: usually 80–105% of estimated (bureaucratic variance)
        sanction_ratio = rng.uniform(0.80, 1.05)
        sanctioned_amount = float(estimated_cost * sanction_ratio)

        # --- Timeline attributes ---
        # Expected duration: 90–540 days (MPLADS guideline ~1 year, with variance)
        expected_duration_days = int(rng.integers(90, 541))

        # Elapsed time: 0 to 1.5× expected (some projects are overdue)
        elapsed_days = int(rng.integers(0, int(expected_duration_days * 1.5) + 1))

        # Progress: loosely correlated with elapsed/expected ratio
        ideal_progress = min((elapsed_days / max(expected_duration_days, 1)) * 100, 100)
        progress_noise = rng.normal(0, 12)  # Tighter noise for more realistic progress
        progress_pct = float(np.clip(ideal_progress + progress_noise, 0, 100))

        # --- Contractor ---
        contractor_id = rng.choice(list(contractor_reliability.keys()))
        contractor_past_delays = contractor_reliability[contractor_id]

        # --- Environmental factors ---
        start_month = rng.integers(1, 13)
        monsoon_overlap_days = _compute_monsoon_overlap(
            state, start_month, expected_duration_days, rng
        )

        # Material inflation: WPI-based (0.95 = deflation, 1.35 = high inflation)
        material_inflation_index = float(rng.uniform(0.95, 1.35))

        # Labor shortage: regional factor (0 = abundant, 1 = severe shortage)
        labor_shortage_index = float(rng.uniform(0.0, 1.0))
        # Hilly/desert regions tend to have worse labor access
        if terrain in ("HILLY", "DESERT"):
            labor_shortage_index = float(np.clip(labor_shortage_index + 0.2, 0, 1))

        # Category complexity factor
        category_complexity = CATEGORY_COMPLEXITY.get(project_category, 1.0)

        # ===================================================================
        # TARGET GENERATION — with strong, clean causal relationships
        # ===================================================================

        # --- actual_final_cost ---
        cost_base = sanctioned_amount

        # Inflation effect (dominant cost driver) — amplified
        cost_inflation_effect = cost_base * (material_inflation_index - 1.0) * 1.8

        # Terrain difficulty multiplier — slightly stronger
        terrain_cost_multiplier = {
            "PLAIN": 1.0, "COASTAL": 1.10, "HILLY": 1.22, "DESERT": 1.14
        }[terrain]

        # Contractor inefficiency adds cost (bad contractors waste money)
        contractor_cost_effect = cost_base * (contractor_past_delays / 100) * 0.6

        # Labor shortage drives up labor costs — amplified
        labor_cost_effect = cost_base * labor_shortage_index * 0.10

        # Monsoon delays cause cost increases (idle equipment, rework)
        monsoon_cost_effect = cost_base * (monsoon_overlap_days / 500) * 0.18

        # Category-specific complexity cost
        category_cost_effect = cost_base * (category_complexity - 1.0) * 0.3

        actual_final_cost = float(
            (cost_base * terrain_cost_multiplier)
            + cost_inflation_effect
            + contractor_cost_effect
            + labor_cost_effect
            + monsoon_cost_effect
            + category_cost_effect
            + rng.normal(0, cost_base * 0.015)  # Tighter noise (~1.5% vs old 3%)
        )
        actual_final_cost = max(actual_final_cost, cost_base * 0.9)  # Floor

        # --- actual_delay_days ---
        # Deterministic base from each factor — cleaner signal-to-noise

        # Monsoon overlap is the #1 delay driver — use fixed coefficient, not random
        delay_monsoon = monsoon_overlap_days * 0.55

        # Contractor history: each past delay adds ~3.5 days expected delay
        delay_contractor = contractor_past_delays * 3.5

        # Labor shortage adds delay — fixed coefficient
        delay_labor = labor_shortage_index * 30.0

        # Terrain difficulty — stronger signal
        terrain_delay = {"PLAIN": 0, "COASTAL": 12, "HILLY": 30, "DESERT": 18}[terrain]

        # Progress gap: THE strongest real-world signal — if behind schedule,
        # delay compounds. Use a deterministic formula.
        expected_progress = min(
            (elapsed_days / max(expected_duration_days, 1)) * 100, 100
        )
        progress_gap = max(expected_progress - progress_pct, 0)
        delay_progress_gap = progress_gap * 0.6  # Fixed coefficient

        # Category complexity adds delay for harder project types
        delay_category = (category_complexity - 0.7) * 15.0

        actual_delay_days = float(
            delay_monsoon
            + delay_contractor
            + delay_labor
            + terrain_delay
            + delay_progress_gap
            + delay_category
            + rng.normal(0, 3)  # Much tighter noise (was 8)
        )
        actual_delay_days = max(actual_delay_days, 0)  # No negative delays

        records.append({
            "project_id": project_id,
            "state": state,
            "constituency_type": constituency_type,
            "project_category": project_category,
            "estimated_cost": round(estimated_cost, 2),
            "sanctioned_amount": round(sanctioned_amount, 2),
            "expected_duration_days": expected_duration_days,
            "elapsed_days": elapsed_days,
            "progress_pct": round(progress_pct, 2),
            "contractor_id": contractor_id,
            "contractor_past_delays": contractor_past_delays,
            "monsoon_overlap_days": monsoon_overlap_days,
            "material_inflation_index": round(material_inflation_index, 4),
            "labor_shortage_index": round(labor_shortage_index, 4),
            "terrain_difficulty": terrain,
            "sanction_year": sanction_year,
            # Targets
            "actual_final_cost": round(actual_final_cost, 2),
            "actual_delay_days": round(actual_delay_days, 2),
        })

    df = pd.DataFrame(records)

    # Save to CSV
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    csv_path = output_path / "synthetic_mplads_data.csv"
    df.to_csv(csv_path, index=False)
    print(f"[Task 1] ✅ Generated {n_records} records → {csv_path}")
    print(f"         Cost range: ₹{df['actual_final_cost'].min():,.0f} – ₹{df['actual_final_cost'].max():,.0f}")
    print(f"         Delay range: {df['actual_delay_days'].min():.0f} – {df['actual_delay_days'].max():.0f} days")
    print(f"         States: {df['state'].nunique()}, Categories: {df['project_category'].nunique()}")
    print(f"         Median cost: ₹{df['actual_final_cost'].median():,.0f}")
    print(f"         Median delay: {df['actual_delay_days'].median():.0f} days")

    return df


if __name__ == "__main__":
    df = generate_dataset()
    print(f"\nSample record:\n{df.iloc[0].to_dict()}")
