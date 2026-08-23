"""
Checkpoint 8 — End-to-End Financial Anomaly Inference Pipeline (SIH26102 / Person 1)

Provides a unified end-to-end inference engine for official MPLADS project records.
Connects data validation, feature preparation, model loading/scoring, score thresholding,
and the explainable anomaly rule engine into a single call.

IMPORTANT CONSTRAINTS:
  - Model Anomaly Cutoff: anomaly_score <= -0.093716 (Approved Checkpoint 7A threshold)
  - Raw Isolation Forest prediction (-1/1) is stored for diagnostics ONLY.
  - variance_amount_inr = None (expenditure data is unavailable in official snapshot).
  - Terminology: "model-detected statistical anomaly", "statistical/project irregularity".
  - DO NOT claim fraud, corruption, misuse of funds, or unauthorized expenditure.
"""

from __future__ import annotations

import logging
import os
import sys
from typing import Any, Dict, List, Optional, Union

import numpy as np
import pandas as pd

from ml_modules.financial.anomaly_model import (
    FEATURE_NAMES,
    anomaly_scores,
    load_model,
    predict_anomalies,
)
from ml_modules.financial.anomaly_rules import (
    DEFAULT_MODEL_SCORE_CUTOFF,
    RuleEngineConfig,
    evaluate_record_anomalies,
)

logger = logging.getLogger(__name__)

DEFAULT_MODEL_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "models",
    "financial_isolation_forest.pkl",
)


def extract_project_identifier(record: Union[Dict[str, Any], pd.Series]) -> str:
    """Extract a human-readable project identifier from record fields."""
    if isinstance(record, pd.Series):
        rec_dict = record.to_dict()
    else:
        rec_dict = dict(record)

    for id_col in ["work_recommendation_dtl_id", "work_id", "project_id", "constituency"]:
        if id_col in rec_dict and pd.notna(rec_dict[id_col]):
            val = str(rec_dict[id_col]).strip()
            if len(val) > 0:
                return val

    return "UNKNOWN"


def validate_inference_record(record: Union[Dict[str, Any], pd.Series]) -> tuple[bool, List[str], List[str]]:
    """Validate that the record contains valid required fields for anomaly feature preparation.

    Returns
    -------
    is_valid : bool
    errors : list[str]
    warnings : list[str]
    """
    errors: List[str] = []
    warnings: List[str] = []

    if isinstance(record, pd.Series):
        rec_dict = record.to_dict()
    elif isinstance(record, dict):
        rec_dict = dict(record)
    else:
        return False, ["Input record must be a dictionary or pandas Series"], []

    # 1. Required field existence check
    req_amount = "sanction_amount" in rec_dict or "log1p_sanction_amount" in rec_dict
    if not req_amount:
        errors.append("Missing required financial field: 'sanction_amount' or 'log1p_sanction_amount'")

    for date_field in ["recommendation_date", "sanction_date", "tenure_start_date"]:
        if date_field not in rec_dict or pd.isna(rec_dict[date_field]):
            errors.append(f"Missing required date field: '{date_field}'")

    if len(errors) > 0:
        return False, errors, warnings

    # 2. Sanction amount numeric & non-zero check
    if "sanction_amount" in rec_dict and pd.notna(rec_dict["sanction_amount"]):
        try:
            s_amt = float(rec_dict["sanction_amount"])
            if np.isnan(s_amt) or s_amt <= 0:
                errors.append("Field 'sanction_amount' must be a positive number > 0")
        except (ValueError, TypeError):
            errors.append("Field 'sanction_amount' must be numeric")

    # 3. Date parsing checks
    rec_dt = pd.to_datetime(rec_dict.get("recommendation_date"), errors="coerce")
    sanc_dt = pd.to_datetime(rec_dict.get("sanction_date"), errors="coerce")
    ten_dt = pd.to_datetime(rec_dict.get("tenure_start_date"), errors="coerce")

    if pd.isna(rec_dt):
        errors.append("Field 'recommendation_date' could not be parsed as a valid datetime")
    if pd.isna(sanc_dt):
        errors.append("Field 'sanction_date' could not be parsed as a valid datetime")
    if pd.isna(ten_dt):
        errors.append("Field 'tenure_start_date' could not be parsed as a valid datetime")

    if len(errors) > 0:
        return False, errors, warnings

    # 4. Chronological consistency checks
    rec_to_sanc = (sanc_dt - rec_dt).days
    days_since_tenure = (rec_dt - ten_dt).days

    if rec_to_sanc < 0:
        warnings.append("recommendation_date_after_sanction_date")

    if days_since_tenure < 0:
        warnings.append("recommendation_date_before_tenure_start")

    return True, errors, warnings


class FinancialAnomalyInferencePipeline:
    """End-to-End inference pipeline for financial anomaly detection on MPLADS projects.

    Connects data validation, feature preparation, Isolation Forest model scoring,
    approved cutoff thresholding (-0.093716), and explainable anomaly rules.
    """

    def __init__(
        self,
        model_path: Optional[str] = None,
        config: Optional[RuleEngineConfig] = None,
    ):
        path = model_path or DEFAULT_MODEL_PATH
        self.model, self.feature_names = load_model(path)

        # Enforce feature contract
        if self.feature_names != FEATURE_NAMES:
            raise ValueError(
                f"Loaded model feature contract {self.feature_names} does not match expected {FEATURE_NAMES}"
            )

        self.config = config or RuleEngineConfig()
        logger.info(
            "[InferencePipeline] Initialized pipeline with model from %s — cutoff score: %.6f",
            path,
            self.config.model_score_cutoff,
        )

    def predict_single_record(self, record: Union[Dict[str, Any], pd.Series]) -> Dict[str, Any]:
        """Perform end-to-end anomaly prediction on a single project record.

        Parameters
        ----------
        record : dict or pd.Series
            Project record containing sanction_amount (or log1p_sanction_amount),
            recommendation_date, sanction_date, and tenure_start_date.

        Returns
        -------
        dict
            Structured result dictionary with project_identifier, is_anomalous,
            anomaly_features, anomaly_score, model_prediction_for_diagnostics,
            feature_values, validation_errors, validation_warnings, and variance_amount_inr.
        """
        project_id = extract_project_identifier(record)
        is_valid, errors, warnings = validate_inference_record(record)

        if not is_valid:
            return {
                "project_identifier": project_id,
                "is_anomalous": False,
                "anomaly_features": [],
                "anomaly_score": None,
                "model_prediction_for_diagnostics": None,
                "feature_values": None,
                "validation_errors": errors,
                "validation_warnings": warnings,
                "variance_amount_inr": None,
            }

        # 1. Feature Derivation
        if isinstance(record, pd.Series):
            rec_dict = record.to_dict()
        else:
            rec_dict = dict(record)

        if "sanction_amount" in rec_dict and pd.notna(rec_dict["sanction_amount"]):
            sanction_amount = float(rec_dict["sanction_amount"])
            log1p_sanction_amount = float(np.log1p(sanction_amount))
        else:
            log1p_sanction_amount = float(rec_dict["log1p_sanction_amount"])
            sanction_amount = float(np.expm1(log1p_sanction_amount))

        rec_dt = pd.to_datetime(rec_dict["recommendation_date"])
        sanc_dt = pd.to_datetime(rec_dict["sanction_date"])
        ten_dt = pd.to_datetime(rec_dict["tenure_start_date"])

        rec_to_sanc_days = float((sanc_dt - rec_dt).days)
        days_since_tenure_start = float((rec_dt - ten_dt).days)

        rec_dict["sanction_amount"] = sanction_amount
        rec_dict["log1p_sanction_amount"] = log1p_sanction_amount
        rec_dict["rec_to_sanc_days"] = rec_to_sanc_days
        rec_dict["days_since_tenure_start"] = days_since_tenure_start

        # 2. Build Feature Matrix (Strictly enforcing FEATURE_NAMES order)
        # FEATURE_NAMES: ["log1p_sanction_amount", "rec_to_sanc_days", "days_since_tenure_start"]
        feature_map = {
            "log1p_sanction_amount": log1p_sanction_amount,
            "rec_to_sanc_days": rec_to_sanc_days,
            "days_since_tenure_start": days_since_tenure_start,
        }
        X = np.array([[feature_map[f] for f in self.feature_names]], dtype=np.float64)

        # 3. Model Inference
        score = float(anomaly_scores(self.model, X)[0])
        raw_pred = int(predict_anomalies(self.model, X)[0])

        # 4. Rule Engine Evaluation
        rule_res = evaluate_record_anomalies(
            record=rec_dict,
            model_prediction=raw_pred,
            anomaly_score=score,
            config=self.config,
        )


        # 5. Build Final Output Schema
        return {
            "project_identifier": project_id,
            "is_anomalous": bool(rule_res["is_anomalous"]),
            "anomaly_features": list(rule_res["anomaly_features"]),
            "anomaly_score": score,
            "model_prediction_for_diagnostics": raw_pred,
            "feature_values": {
                "sanction_amount": sanction_amount,
                "log1p_sanction_amount": log1p_sanction_amount,
                "rec_to_sanc_days": rec_to_sanc_days,
                "days_since_tenure_start": days_since_tenure_start,
            },
            "validation_errors": errors,
            "validation_warnings": warnings,
            "variance_amount_inr": None,
        }
