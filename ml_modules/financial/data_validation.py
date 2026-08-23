"""
Data Validation & Guardrails Module for MPLADS Financial Anomaly Engine.

This module provides structural validation and financial consistency checks
for project records before they reach feature engineering or ML inference.

Core Principles:
- STRUCTURAL VALIDATION (is_valid = False): Rejects missing fields, non-numeric values,
  negative monetary amounts, sanctioned_amount <= 0, progress outside 0-100, or
  days_elapsed > project_duration_days.
- SUSPICIOUS FINANCIAL PATTERNS (is_valid = True, warnings populated): Flags financial
  over-expenditure, over-disbursal, zero progress with spending, and zero funds released
  without rejecting the record.
- NO VALUE MUTATION: Original financial values are preserved exactly as provided.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd


@dataclass
class ValidationResult:
    """Represents the outcome of validating a single project record."""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    validated_data: Optional[Dict[str, Any]] = None


class FinancialDataValidator:
    """
    Validates MPLADS project financial records against structural schema rules
    and financial consistency guardrails.
    """

    REQUIRED_FIELDS = [
        "project_id",
        "estimated_cost",
        "sanctioned_amount",
        "funds_released",
        "expenditure",
        "current_progress_pct",
        "project_duration_days",
        "days_elapsed",
    ]

    @staticmethod
    def validate_project_record(record: Dict[str, Any]) -> ValidationResult:
        """
        Validates a single project record dictionary.

        Returns:
            ValidationResult containing:
            - is_valid (bool): True if structural checks pass, False otherwise.
            - errors (List[str]): List of structural validation failure messages.
            - warnings (List[str]): List of suspicious financial pattern flags.
            - validated_data (Dict[str, Any]): Original unmutated input record.
        """
        errors: List[str] = []
        warnings: List[str] = []

        if not isinstance(record, dict):
            return ValidationResult(
                is_valid=False,
                errors=["Record must be a dictionary"],
                warnings=[],
                validated_data=None,
            )

        # 1. Structural Presence Checks
        for req_field in FinancialDataValidator.REQUIRED_FIELDS:
            if req_field not in record or record[req_field] is None:
                errors.append(f"Missing required field: '{req_field}'")
            elif isinstance(record[req_field], float) and np.isnan(record[req_field]):
                errors.append(f"Missing required field: '{req_field}'")

        # project_id check
        pid = record.get("project_id")
        if pid is not None and (not isinstance(pid, str) or len(str(pid).strip()) == 0):
            errors.append("Field 'project_id' must be a non-empty string")

        # Numeric field extraction without mutating original record
        parsed_vals = {}
        numeric_fields = [
            "estimated_cost",
            "sanctioned_amount",
            "funds_released",
            "expenditure",
            "current_progress_pct",
            "project_duration_days",
            "days_elapsed",
        ]

        for field_name in numeric_fields:
            if field_name in record and record[field_name] is not None:
                val = record[field_name]
                if isinstance(val, (int, float, np.integer, np.floating)) and not np.isnan(val):
                    parsed_vals[field_name] = float(val)
                else:
                    errors.append(f"Field '{field_name}' must be numeric")

        # Structural Boundary Checks
        if "estimated_cost" in parsed_vals:
            if parsed_vals["estimated_cost"] < 0:
                errors.append("Field 'estimated_cost' must be >= 0")

        if "sanctioned_amount" in parsed_vals:
            if parsed_vals["sanctioned_amount"] <= 0:
                errors.append("Field 'sanctioned_amount' must be > 0 for ratio calculations")

        if "funds_released" in parsed_vals:
            if parsed_vals["funds_released"] < 0:
                errors.append("Field 'funds_released' must be >= 0")

        if "expenditure" in parsed_vals:
            if parsed_vals["expenditure"] < 0:
                errors.append("Field 'expenditure' must be >= 0")

        if "current_progress_pct" in parsed_vals:
            prog = parsed_vals["current_progress_pct"]
            if prog < 0 or prog > 100:
                errors.append("Field 'current_progress_pct' must be between 0 and 100 inclusive")

        if "project_duration_days" in parsed_vals:
            dur = parsed_vals["project_duration_days"]
            if dur <= 0:
                errors.append("Field 'project_duration_days' must be > 0")

        if "days_elapsed" in parsed_vals:
            el = parsed_vals["days_elapsed"]
            if el < 0:
                errors.append("Field 'days_elapsed' must be >= 0")
            elif "project_duration_days" in parsed_vals and parsed_vals["project_duration_days"] > 0:
                if el > parsed_vals["project_duration_days"]:
                    errors.append(
                        f"Field 'days_elapsed' ({el}) exceeds 'project_duration_days' "
                        f"({parsed_vals['project_duration_days']})"
                    )

        # If any structural errors exist, reject record for ML inference
        if len(errors) > 0:
            return ValidationResult(
                is_valid=False,
                errors=errors,
                warnings=[],
                validated_data=record,
            )

        # 2. Financial Consistency Warnings (Valid record, suspicious patterns)
        sanc = parsed_vals["sanctioned_amount"]
        rel = parsed_vals["funds_released"]
        exp = parsed_vals["expenditure"]
        prog = parsed_vals["current_progress_pct"]
        dur = parsed_vals["project_duration_days"]
        el = parsed_vals["days_elapsed"]

        if exp > sanc:
            warnings.append("expenditure_exceeds_sanction")

        if exp > rel:
            warnings.append("expenditure_exceeds_funds_released")

        if rel > sanc:
            warnings.append("funds_released_exceeds_sanction")

        if rel == 0:
            warnings.append("zero_funds_released")

        if prog == 0 and (exp > 0 or rel > 0):
            warnings.append("zero_progress_with_financial_activity")

        if (exp / sanc >= 0.80) and (5 <= prog <= 20):
            warnings.append("high_expenditure_low_progress")

        if (el / dur >= 0.85) and (rel / sanc >= 0.75) and (prog <= 15):
            warnings.append("severe_progress_mismatch")

        return ValidationResult(
            is_valid=True,
            errors=[],
            warnings=warnings,
            validated_data=record,
        )


    @staticmethod
    def validate_dataset(df: pd.DataFrame) -> Dict[str, Any]:
        """
        Validates an entire pandas DataFrame of project records.

        Returns summary dictionary containing:
        - total_records: int
        - valid_records: int
        - invalid_records: int
        - records_with_warnings: int
        - warning_distribution: Dict[str, int]
        - results: List[ValidationResult]
        """
        results: List[ValidationResult] = []
        for _, row in df.iterrows():
            record = row.to_dict()
            res = FinancialDataValidator.validate_project_record(record)
            results.append(res)

        total = len(results)
        valid_count = sum(1 for r in results if r.is_valid)
        invalid_count = total - valid_count
        warning_records_count = sum(1 for r in results if r.is_valid and len(r.warnings) > 0)

        warning_counts: Dict[str, int] = {}
        for r in results:
            if r.is_valid:
                for w in r.warnings:
                    warning_counts[w] = warning_counts.get(w, 0) + 1

        return {
            "total_records": total,
            "valid_records": valid_count,
            "invalid_records": invalid_count,
            "records_with_warnings": warning_records_count,
            "warning_distribution": warning_counts,
            "results": results,
        }
