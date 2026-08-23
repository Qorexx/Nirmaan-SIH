"""
Pytest Unit Tests for Financial Data Validator (Checkpoint 3).

Verifies structural validation errors, financial warning guardrails, and no value mutation.
"""

import pytest
from ml_modules.financial.data_validation import FinancialDataValidator, ValidationResult


@pytest.fixture
def base_valid_record():
    return {
        "project_id": "MPLADS-2026-0001",
        "estimated_cost": 1000000.0,
        "sanctioned_amount": 950000.0,
        "funds_released": 500000.0,
        "expenditure": 450000.0,
        "current_progress_pct": 50,
        "project_duration_days": 365,
        "days_elapsed": 180,
    }


# 1. Valid normal project
def test_valid_normal_project(base_valid_record):
    res = FinancialDataValidator.validate_project_record(base_valid_record)
    assert res.is_valid is True
    assert len(res.errors) == 0
    assert len(res.warnings) == 0
    assert res.validated_data == base_valid_record


# 2. Missing project_id
def test_missing_project_id(base_valid_record):
    record = base_valid_record.copy()
    del record["project_id"]
    res = FinancialDataValidator.validate_project_record(record)
    assert res.is_valid is False
    assert any("project_id" in err for err in res.errors)


# 3. Missing expenditure
def test_missing_expenditure(base_valid_record):
    record = base_valid_record.copy()
    del record["expenditure"]
    res = FinancialDataValidator.validate_project_record(record)
    assert res.is_valid is False
    assert any("expenditure" in err for err in res.errors)


# 4. Negative expenditure
def test_negative_expenditure(base_valid_record):
    record = base_valid_record.copy()
    record["expenditure"] = -500.0
    res = FinancialDataValidator.validate_project_record(record)
    assert res.is_valid is False
    assert any("expenditure" in err for err in res.errors)


# 5. Negative sanctioned_amount
def test_negative_sanctioned_amount(base_valid_record):
    record = base_valid_record.copy()
    record["sanctioned_amount"] = -1000.0
    res = FinancialDataValidator.validate_project_record(record)
    assert res.is_valid is False
    assert any("sanctioned_amount" in err for err in res.errors)


# 6. sanctioned_amount = 0
def test_sanctioned_amount_zero(base_valid_record):
    record = base_valid_record.copy()
    record["sanctioned_amount"] = 0.0
    res = FinancialDataValidator.validate_project_record(record)
    assert res.is_valid is False
    assert any("sanctioned_amount" in err for err in res.errors)


# 7. funds_released = 0
def test_funds_released_zero(base_valid_record):
    record = base_valid_record.copy()
    record["funds_released"] = 0.0
    record["expenditure"] = 0.0
    res = FinancialDataValidator.validate_project_record(record)
    assert res.is_valid is True
    assert "zero_funds_released" in res.warnings


# 8. current_progress_pct = 0
def test_current_progress_zero(base_valid_record):
    record = base_valid_record.copy()
    record["current_progress_pct"] = 0
    record["funds_released"] = 0.0
    record["expenditure"] = 0.0
    res = FinancialDataValidator.validate_project_record(record)
    assert res.is_valid is True


# 9. current_progress_pct < 0
def test_current_progress_negative(base_valid_record):
    record = base_valid_record.copy()
    record["current_progress_pct"] = -5
    res = FinancialDataValidator.validate_project_record(record)
    assert res.is_valid is False
    assert any("current_progress_pct" in err for err in res.errors)


# 10. current_progress_pct > 100
def test_current_progress_greater_than_100(base_valid_record):
    record = base_valid_record.copy()
    record["current_progress_pct"] = 105
    res = FinancialDataValidator.validate_project_record(record)
    assert res.is_valid is False
    assert any("current_progress_pct" in err for err in res.errors)


# 11. days_elapsed > project_duration_days
def test_days_elapsed_exceeds_duration(base_valid_record):
    record = base_valid_record.copy()
    record["days_elapsed"] = 400
    record["project_duration_days"] = 365
    res = FinancialDataValidator.validate_project_record(record)
    assert res.is_valid is False
    assert any("days_elapsed" in err for err in res.errors)


# 12. expenditure > sanctioned_amount
def test_expenditure_exceeds_sanctioned(base_valid_record):
    record = base_valid_record.copy()
    record["expenditure"] = 1200000.0  # > sanctioned (950000.0)
    res = FinancialDataValidator.validate_project_record(record)
    assert res.is_valid is True
    assert "expenditure_exceeds_sanction" in res.warnings


# 13. funds_released > sanctioned_amount
def test_funds_released_exceeds_sanctioned(base_valid_record):
    record = base_valid_record.copy()
    record["funds_released"] = 1100000.0  # > sanctioned (950000.0)
    res = FinancialDataValidator.validate_project_record(record)
    assert res.is_valid is True
    assert "funds_released_exceeds_sanction" in res.warnings


# 14. expenditure > funds_released
def test_expenditure_exceeds_funds_released(base_valid_record):
    record = base_valid_record.copy()
    record["expenditure"] = 700000.0
    record["funds_released"] = 500000.0
    res = FinancialDataValidator.validate_project_record(record)
    assert res.is_valid is True
    assert "expenditure_exceeds_funds_released" in res.warnings


# 15. Multiple invalid fields simultaneously
def test_multiple_invalid_fields():
    record = {
        "project_id": "",
        "estimated_cost": 100000.0,
        "sanctioned_amount": -50.0,
        "funds_released": 0.0,
        "expenditure": -20.0,
        "current_progress_pct": 150,
        "project_duration_days": 100,
        "days_elapsed": 120,
    }
    res = FinancialDataValidator.validate_project_record(record)
    assert res.is_valid is False
    assert len(res.errors) >= 4


# 16. Zero-progress project with expenditure
def test_zero_progress_with_expenditure(base_valid_record):
    record = base_valid_record.copy()
    record["current_progress_pct"] = 0
    record["expenditure"] = 300000.0
    res = FinancialDataValidator.validate_project_record(record)
    assert res.is_valid is True
    assert "zero_progress_with_financial_activity" in res.warnings


# 17. Valid anomaly-like project must remain valid
def test_valid_anomaly_like_projects():
    anomalies = [
        # high_expenditure_low_progress
        {
            "project_id": "ANOM-01",
            "estimated_cost": 1000000.0,
            "sanctioned_amount": 900000.0,
            "funds_released": 850000.0,
            "expenditure": 800000.0,
            "current_progress_pct": 10,
            "project_duration_days": 300,
            "days_elapsed": 200,
        },
        # expenditure_exceeds_sanction
        {
            "project_id": "ANOM-02",
            "estimated_cost": 1000000.0,
            "sanctioned_amount": 900000.0,
            "funds_released": 850000.0,
            "expenditure": 1200000.0,
            "current_progress_pct": 60,
            "project_duration_days": 300,
            "days_elapsed": 200,
        },
        # severe_progress_mismatch
        {
            "project_id": "ANOM-03",
            "estimated_cost": 1000000.0,
            "sanctioned_amount": 900000.0,
            "funds_released": 750000.0,
            "expenditure": 200000.0,
            "current_progress_pct": 10,
            "project_duration_days": 300,
            "days_elapsed": 280,
        },
        # zero_progress_high_release
        {
            "project_id": "ANOM-04",
            "estimated_cost": 1000000.0,
            "sanctioned_amount": 900000.0,
            "funds_released": 600000.0,
            "expenditure": 450000.0,
            "current_progress_pct": 0,
            "project_duration_days": 300,
            "days_elapsed": 150,
        },
    ]

    for record in anomalies:
        res = FinancialDataValidator.validate_project_record(record)
        assert res.is_valid is True, f"Record {record['project_id']} failed validation unexpectedly: {res.errors}"
        assert len(res.warnings) > 0, f"Record {record['project_id']} should have generated warnings"
