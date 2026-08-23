"""
Checkpoint 9 — Unit Tests for PostgreSQL Data Loader Integration

Tests:
  1. valid record mapping
  2. missing optional fields
  3. missing required fields handling
  4. correct field names mapping
  5. no value mutation
  6. database connection handling (error propagation)
  7. empty result handling
  8. integration compatibility with FinancialAnomalyInferencePipeline
"""

from unittest.mock import MagicMock, Mock
import pytest
import pandas as pd
import numpy as np

from ml_modules.financial.data_loader import (
    PostgreSQLDataLoader,
    normalize_db_record,
    DB_FIELD_MAP,
)
from ml_modules.financial.inference import FinancialAnomalyInferencePipeline


@pytest.fixture
def raw_sql_row():
    return {
        "id": "PROJ-2024-999",
        "sanctioned_amount": 1500000.0,
        "start_date": "2024-09-01",
        "sanction_date": "2024-11-20",
        "tenure_start_date": "2024-06-04",
        "district_authority": "MUMBAI NORTH",
    }


# ── 1. Valid Record Mapping ────────────────────────────────────────────────────
def test_valid_record_mapping(raw_sql_row):
    norm = normalize_db_record(raw_sql_row)
    assert norm["work_recommendation_dtl_id"] == "PROJ-2024-999"
    assert norm["sanction_amount"] == 1500000.0
    assert norm["recommendation_date"] == "2024-09-01"
    assert norm["sanction_date"] == "2024-11-20"
    assert norm["tenure_start_date"] == "2024-06-04"

    # Explicitly check absent fields are set to None
    assert norm["expenditure"] is None
    assert norm["funds_released"] is None
    assert norm["physical_progress_pct"] is None
    assert norm["pfms_status"] is None
    assert norm["transaction_type"] is None


# ── 2. Missing Optional Fields ─────────────────────────────────────────────────
def test_missing_optional_fields():
    minimal_row = {
        "id": "PROJ-MINIMAL",
        "sanction_amount": 500000.0,
        "recommendation_date": "2024-01-01",
        "sanction_date": "2024-03-01",
        "tenure_start_date": "2023-01-01",
    }
    norm = normalize_db_record(minimal_row)
    assert norm["work_recommendation_dtl_id"] == "PROJ-MINIMAL"
    assert norm["sanction_amount"] == 500000.0
    assert norm["expenditure"] is None


# ── 3. Missing Required Fields Handling ────────────────────────────────────────
def test_missing_required_fields_handling():
    incomplete_row = {
        "id": "PROJ-INCOMPLETE",
        # Missing sanction_amount and dates
    }
    norm = normalize_db_record(incomplete_row)
    assert norm["work_recommendation_dtl_id"] == "PROJ-INCOMPLETE"
    assert "sanction_amount" not in norm or norm.get("sanction_amount") is None


# ── 4. Correct Field Names Mapping ──────────────────────────────────────────────
def test_correct_field_names_mapping():
    row_variant = {
        "project_id": "141814",
        "sanctioned_amount": 2500000.0,
        "start_date": "2024-05-01",
        "sanction_date": "2024-08-15",
        "tenure_start_date": "2024-01-01",
    }
    norm = normalize_db_record(row_variant)
    assert "work_recommendation_dtl_id" in norm
    assert "sanction_amount" in norm
    assert "recommendation_date" in norm
    assert norm["sanction_amount"] == 2500000.0


# ── 5. No Value Mutation ───────────────────────────────────────────────────────
def test_no_value_mutation(raw_sql_row):
    original_copy = dict(raw_sql_row)
    _ = normalize_db_record(raw_sql_row)
    assert raw_sql_row == original_copy


# ── 6. Database Connection Handling ────────────────────────────────────────────
def test_database_connection_handling_missing_uri():
    loader = PostgreSQLDataLoader(db_uri=None)
    with pytest.raises(ConnectionError) as exc_info:
        loader.fetch_project_by_id("10001")
    assert "No database URI" in str(exc_info.value)


def test_database_connection_mock_query(raw_sql_row):
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_conn.execute.side_effect = Exception("Fallback to cursor")

    # Mock return values for DB-API cursor
    mock_cursor.description = [("id", None), ("sanctioned_amount", None), ("start_date", None),
                               ("sanction_date", None), ("tenure_start_date", None), ("district_authority", None)]
    mock_cursor.fetchone.return_value = (
        raw_sql_row["id"],
        raw_sql_row["sanctioned_amount"],
        raw_sql_row["start_date"],
        raw_sql_row["sanction_date"],
        raw_sql_row["tenure_start_date"],
        raw_sql_row["district_authority"],
    )

    loader = PostgreSQLDataLoader(connection=mock_conn)
    result = loader.fetch_project_by_id("PROJ-2024-999")

    assert result is not None
    assert result["work_recommendation_dtl_id"] == "PROJ-2024-999"
    assert result["sanction_amount"] == 1500000.0
    assert result["expenditure"] is None


# ── 7. Empty Result Handling ───────────────────────────────────────────────────
def test_empty_result_handling():
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_conn.execute.side_effect = Exception("Fallback to cursor")
    mock_cursor.fetchone.return_value = None

    loader = PostgreSQLDataLoader(connection=mock_conn)
    result = loader.fetch_project_by_id("NON_EXISTENT_ID")
    assert result is None


# ── 8. Integration with FinancialAnomalyInferencePipeline ─────────────────────
def test_integration_with_inference_pipeline(raw_sql_row):
    norm_record = normalize_db_record(raw_sql_row)
    pipeline = FinancialAnomalyInferencePipeline()
    res = pipeline.predict_single_record(norm_record)

    assert res["project_identifier"] == "PROJ-2024-999"
    assert "is_anomalous" in res
    assert res["variance_amount_inr"] is None
    assert res["validation_errors"] == []
