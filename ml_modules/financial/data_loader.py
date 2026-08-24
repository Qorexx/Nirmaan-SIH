"""
Checkpoint 9 — PostgreSQL Data Loader Integration (SIH26102 / Person 1)

Provides a read-only data loader that retrieves project records from PostgreSQL (or database connections)
and normalizes available fields into the input schema expected by FinancialAnomalyInferencePipeline.

IMPORTANT CONSTRAINTS:
  - Retrieves ONLY available fields: project_id / work_recommendation_dtl_id, sanction_amount / sanctioned_amount,
    recommendation_date / start_date, sanction_date, tenure_start_date.
  - DO NOT fabricate missing fields: expenditure, funds_released, physical_progress_pct, pfms_status, transaction_type.
  - Missing fields are explicitly mapped to None.
  - Does NOT modify database records (100% read-only).
  - Does NOT alter the inference contract (variance_amount_inr remains None).
  - Handles database connection failures and missing records gracefully.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional, Union

import pandas as pd

logger = logging.getLogger(__name__)

# Standardized column mapping from SQL / DB columns to inference pipeline fields
DB_FIELD_MAP = {
    "id": "work_recommendation_dtl_id",
    "project_id": "work_recommendation_dtl_id",
    "work_recommendation_dtl_id": "work_recommendation_dtl_id",
    "sanctioned_amount": "sanction_amount",
    "sanction_amount": "sanction_amount",
    "start_date": "recommendation_date",
    "recommendation_date": "recommendation_date",
    "sanction_date": "sanction_date",
    "tenure_start_date": "tenure_start_date",
}


def normalize_db_record(raw_record: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize a raw SQL row dictionary into the record format expected by inference pipeline.

    Available fields are mapped to standard names. Missing financial fields
    (expenditure, funds_released, physical_progress_pct, etc.) are explicitly set to None.
    """
    if not isinstance(raw_record, dict):
        raise TypeError("raw_record must be a dictionary")

    record: Dict[str, Any] = {}

    # 1. Map available fields
    for raw_key, val in raw_record.items():
        mapped_key = DB_FIELD_MAP.get(raw_key, raw_key)
        record[mapped_key] = val

    # 2. Ensure project identifier fallback
    if "work_recommendation_dtl_id" not in record or record["work_recommendation_dtl_id"] is None:
        for alt_id in ["project_id", "work_id", "id"]:
            if alt_id in raw_record and raw_record[alt_id] is not None:
                record["work_recommendation_dtl_id"] = raw_record[alt_id]
                break

    # 3. Explicitly mark absent financial signals as None (NO FABRICATION)
    record["expenditure"] = None
    record["funds_released"] = None
    record["physical_progress_pct"] = None
    record["pfms_status"] = None
    record["transaction_type"] = None

    return record


class PostgreSQLDataLoader:
    """Read-only data loader for fetching MPLADS project records from PostgreSQL or SQL engines."""

    def __init__(self, db_uri: Optional[str] = None, connection: Optional[Any] = None):
        """Initialize loader with a database URI or active connection.

        Parameters
        ----------
        db_uri : str | None
            PostgreSQL connection string (e.g. 'postgresql://user:pass@localhost:5432/mplads').
            Defaults to DATABASE_URL environment variable if provided.
        connection : Any | None
            Optional active DB-API / SQLAlchemy connection object (useful for mocking/testing).
        """
        self.db_uri = db_uri or os.getenv("DATABASE_URL")
        self._connection = connection

    def _get_connection(self) -> Any:
        """Retrieve or establish database connection."""
        if self._connection is not None:
            return self._connection

        if not self.db_uri:
            raise ConnectionError(
                "No database URI or active connection provided. Set DATABASE_URL environment variable."
            )

        try:
            # Lazy import to avoid mandating psycopg2 / sqlalchemy during non-DB unit tests
            from sqlalchemy import create_engine
            engine = create_engine(self.db_uri)
            return engine.connect()
        except Exception as e:
            logger.error("[PostgreSQLDataLoader] Failed to connect to database: %s", str(e))
            raise ConnectionError(f"Failed to connect to database at {self.db_uri}: {str(e)}") from e

    def fetch_project_by_id(self, project_id: Union[str, int]) -> Optional[Dict[str, Any]]:
        """Fetch a single project record by ID and return normalized inference dict.

        Returns None if record does not exist.
        """
        query = """
            SELECT 
                id,
                sanctioned_amount,
                start_date,
                sanction_date,
                tenure_start_date,
                category,
                district_authority
            FROM projects
            WHERE id = :project_id OR work_recommendation_dtl_id = :project_id
            LIMIT 1
        """
        try:
            conn = self._get_connection()
            # If using pandas / DB-API / SQLAlchemy execution
            if hasattr(conn, "execute"):
                # Handle SQLAlchemy connection or execute
                try:
                    from sqlalchemy import text
                    result = conn.execute(text(query), {"project_id": str(project_id)}).mappings().first()
                    if result:
                        return normalize_db_record(dict(result))
                except Exception:
                    # Fallback for plain DB-API connection mock
                    cursor = conn.cursor()
                    cursor.execute(query, (str(project_id), str(project_id)))
                    row = cursor.fetchone()
                    if row:
                        cols = [desc[0] for desc in cursor.description]
                        raw_dict = dict(zip(cols, row))
                        return normalize_db_record(raw_dict)
            elif hasattr(conn, "cursor"):
                cursor = conn.cursor()
                cursor.execute(query, (str(project_id), str(project_id)))
                row = cursor.fetchone()
                if row:
                    cols = [desc[0] for desc in cursor.description]
                    raw_dict = dict(zip(cols, row))
                    return normalize_db_record(raw_dict)

            return None
        except ConnectionError:
            raise
        except Exception as e:
            logger.error("[PostgreSQLDataLoader] Error querying project %s: %s", project_id, str(e))
            raise RuntimeError(f"Database query failed for project {project_id}: {str(e)}") from e

    def fetch_sanctioned_projects_batch(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Fetch a batch of sanctioned project records for bulk inference."""
        query = """
            SELECT 
                id,
                sanctioned_amount,
                start_date,
                sanction_date,
                tenure_start_date,
                category,
                district_authority
            FROM projects
            WHERE status = 'SANCTIONED' OR query_category = 'Works Sanctioned'
            LIMIT :limit OFFSET :offset
        """
        try:
            conn = self._get_connection()
            records: List[Dict[str, Any]] = []

            if hasattr(conn, "execute"):
                try:
                    from sqlalchemy import text
                    results = conn.execute(text(query), {"limit": limit, "offset": offset}).mappings().all()
                    for r in results:
                        records.append(normalize_db_record(dict(r)))
                    return records
                except Exception:
                    cursor = conn.cursor()
                    cursor.execute(query, (limit, offset))
                    rows = cursor.fetchall()
                    cols = [desc[0] for desc in cursor.description]
                    for row in rows:
                        records.append(normalize_db_record(dict(zip(cols, row))))
                    return records
            elif hasattr(conn, "cursor"):
                cursor = conn.cursor()
                cursor.execute(query, (limit, offset))
                rows = cursor.fetchall()
                cols = [desc[0] for desc in cursor.description]
                for row in rows:
                    records.append(normalize_db_record(dict(zip(cols, row))))
                return records

            return []
        except ConnectionError:
            raise
        except Exception as e:
            logger.error("[PostgreSQLDataLoader] Error querying batch: %s", str(e))
            raise RuntimeError(f"Database query failed: {str(e)}") from e
