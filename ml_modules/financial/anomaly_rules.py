"""
Checkpoint 7B — Explainable Anomaly Rule Engine (SIH26102 / Person 1)

Provides an explainable rule engine that combines Isolation Forest statistical
anomaly detection with domain/context rules to produce human-readable,
deterministic anomaly explanations.

IMPORTANT SEMANTIC CONSTRAINTS:
  - Explanations indicate "statistical/project irregularity".
  - DO NOT use claims of "fraud", "corruption", "misuse of funds", or "unauthorized expenditure".
  - Evaluates ONLY available features: log1p_sanction_amount (or sanction_amount),
    rec_to_sanc_days, and days_since_tenure_start.
  - DO NOT require absent fields (funds_released, expenditure, physical_progress_pct, etc.).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Union

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# ── 1. Empirical Rule Threshold Constants ─────────────────────────────────────
# Sources: Checkpoint 5 EDA (docs/eda_feature_refinement.md) and Checkpoint 7A (docs/model_threshold_analysis.md)

#: Upper IQR outlier threshold for rec_to_sanc_days: Q3 + 1.5 * IQR = 163 + 1.5 * (163 - 41) = 286 days (5.47% population)
DEFAULT_DELAY_THRESHOLD_DAYS: int = 286

#: Upper IQR outlier threshold for sanction_amount: Q3 + 1.5 * IQR = ₹11,98,014 (~11.98 Lakhs; 8.09% population)
DEFAULT_SANCTION_AMOUNT_THRESHOLD_INR: float = 1198014.0

#: Lower P10 percentile threshold for days_since_tenure_start: 113 days (~first 3.7 months of MP tenure; 10.0% population)
DEFAULT_EARLY_TENURE_THRESHOLD_DAYS: int = 113

#: Approved Checkpoint 7A Isolation Forest score cutoff for 3.0% anomaly rate
DEFAULT_MODEL_SCORE_CUTOFF: float = -0.093716

# ── 2. Standardized Rule Output String Identifiers ──────────────────────────────
RULE_LONG_DELAY = "unusually_long_recommendation_to_sanction_delay"
RULE_HIGH_SANCTION = "unusually_high_sanction_amount"
RULE_EARLY_TENURE = "early_tenure_recommendation"
RULE_MULTI_SIGNAL = "multi_signal_statistical_anomaly"
RULE_MODEL_ANOMALY = "model_detected_statistical_anomaly"


@dataclass
class RuleEngineConfig:
    """Configuration container for domain rule thresholds and model cutoff.

    All default thresholds are derived from empirical EDA of the 73,789
    Works Sanctioned training records.
    """
    delay_threshold_days: int = DEFAULT_DELAY_THRESHOLD_DAYS
    sanction_amount_threshold_inr: float = DEFAULT_SANCTION_AMOUNT_THRESHOLD_INR
    early_tenure_threshold_days: int = DEFAULT_EARLY_TENURE_THRESHOLD_DAYS
    model_score_cutoff: float = DEFAULT_MODEL_SCORE_CUTOFF


def _extract_feature_values(record: Union[Dict[str, Any], pd.Series]) -> tuple[float, float, float]:
    """Extract raw sanction_amount, rec_to_sanc_days, and days_since_tenure_start from input.

    Handles input dicts or pd.Series containing either raw sanction_amount or log1p_sanction_amount.
    """
    if isinstance(record, pd.Series):
        rec_dict = record.to_dict()
    else:
        rec_dict = dict(record)

    # 1. Extract Sanction Amount (INR)
    if "sanction_amount" in rec_dict and pd.notna(rec_dict["sanction_amount"]):
        sanction_amount = float(rec_dict["sanction_amount"])
    elif "log1p_sanction_amount" in rec_dict and pd.notna(rec_dict["log1p_sanction_amount"]):
        sanction_amount = float(np.expm1(rec_dict["log1p_sanction_amount"]))
    else:
        raise KeyError("Input record must contain 'sanction_amount' or 'log1p_sanction_amount'.")

    # 2. Extract rec_to_sanc_days
    if "rec_to_sanc_days" in rec_dict and pd.notna(rec_dict["rec_to_sanc_days"]):
        rec_to_sanc_days = float(rec_dict["rec_to_sanc_days"])
    else:
        raise KeyError("Input record must contain 'rec_to_sanc_days'.")

    # 3. Extract days_since_tenure_start
    if "days_since_tenure_start" in rec_dict and pd.notna(rec_dict["days_since_tenure_start"]):
        days_since_tenure_start = float(rec_dict["days_since_tenure_start"])
    else:
        raise KeyError("Input record must contain 'days_since_tenure_start'.")

    return sanction_amount, rec_to_sanc_days, days_since_tenure_start


def evaluate_record_anomalies(
    record: Union[Dict[str, Any], pd.Series],
    model_prediction: Union[int, bool],
    anomaly_score: float,
    config: RuleEngineConfig | None = None,
) -> Dict[str, Any]:
    """Evaluate a single project record using domain rules and Isolation Forest score.

    Parameters
    ----------
    record : dict or pd.Series
        Feature values for the project. Must contain sanction_amount (or log1p_sanction_amount),
        rec_to_sanc_days, and days_since_tenure_start.
    model_prediction : int or bool
        Isolation Forest prediction (-1 or True for anomalous, 1 or False for normal).
    anomaly_score : float
        Continuous decision function score from Isolation Forest (lower/negative = more anomalous).
    config : RuleEngineConfig | None
        Optional rule configuration overrides. Uses empirical defaults if None.

    Returns
    -------
    dict
        {
            "is_anomalous": bool,
            "anomaly_features": list[str],
            "anomaly_score": float
        }
    """
    cfg = config or RuleEngineConfig()
    sanction_amount, rec_to_sanc_days, days_since_tenure_start = _extract_feature_values(record)

    # Determine if Isolation Forest considers this record an anomaly based on approved threshold
    # Note: raw model_prediction (-1/1) from contamination="auto" is ignored for final anomaly decision
    # to enforce the approved 3.0% operational MVP score cutoff (-0.093716).
    is_model_anomaly = anomaly_score <= cfg.model_score_cutoff


    triggered_domain_rules: List[str] = []

    # Rule 1: Unusually long recommendation-to-sanction delay
    if rec_to_sanc_days > cfg.delay_threshold_days:
        triggered_domain_rules.append(RULE_LONG_DELAY)

    # Rule 2: Unusually high sanction amount
    if sanction_amount > cfg.sanction_amount_threshold_inr:
        triggered_domain_rules.append(RULE_HIGH_SANCTION)

    # Rule 3: Early-tenure recommendation
    if days_since_tenure_start < cfg.early_tenure_threshold_days:
        triggered_domain_rules.append(RULE_EARLY_TENURE)

    # Rule 4: Multi-signal anomaly (multiple domain rules AND model anomaly)
    has_multi_signal = len(triggered_domain_rules) >= 2 and is_model_anomaly

    anomaly_features: List[str] = []
    anomaly_features.extend(triggered_domain_rules)

    if has_multi_signal:
        anomaly_features.append(RULE_MULTI_SIGNAL)

    # If model flagged anomaly but no domain rule triggered, label as model anomaly
    if is_model_anomaly and len(triggered_domain_rules) == 0:
        anomaly_features.append(RULE_MODEL_ANOMALY)

    # Record is overall anomalous if Isolation Forest flags it OR any domain rule triggers
    is_anomalous = is_model_anomaly or (len(triggered_domain_rules) > 0)

    return {
        "is_anomalous": bool(is_anomalous),
        "anomaly_features": anomaly_features,
        "anomaly_score": float(anomaly_score),
    }


def evaluate_dataset_rules(
    df: pd.DataFrame,
    predictions: np.ndarray,
    scores: np.ndarray,
    config: RuleEngineConfig | None = None,
) -> pd.DataFrame:
    """Batch evaluate rules on a DataFrame of project records.

    Returns a DataFrame with columns: ['is_anomalous', 'anomaly_features', 'anomaly_score'].
    """
    cfg = config or RuleEngineConfig()
    results = []

    for i in range(len(df)):
        row = df.iloc[i]
        pred = predictions[i]
        score = scores[i]
        res = evaluate_record_anomalies(row, pred, score, config=cfg)
        results.append(res)

    res_df = pd.DataFrame(results, index=df.index)
    return res_df
