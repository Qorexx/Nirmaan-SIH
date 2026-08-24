"""
Checkpoint 11 — End-to-End Financial Anomaly Integration Runner (SIH26102 / Person 1)

Demonstrates the complete ML inference chain:

  PostgreSQL
    ↓  PostgreSQLDataLoader
    ↓  FinancialAnomalyInferencePipeline
    ↓  Isolation Forest (-0.093716 approved cutoff)
    ↓  Explainable Rule Engine
    ↓  FinancialAlertClient
    ↓  POST /api/v1/financial-anomalies

STRICT CONSTRAINTS:
  - NEVER fabricates expenditure, funds_released, physical_progress_pct,
    pfms_status, or transaction_type.
  - NEVER converts variance_amount_inr = None to 0.
  - NEVER processes thousands of records automatically.
  - Default: ONE real project record.
  - Backend alert sending is OPT-IN via --send-alert.
  - If PostgreSQL is unavailable, prints DATABASE UNAVAILABLE and exits.
  - If backend is unavailable during --send-alert, prints clear error and exits.

Usage Examples:
  PYTHONPATH=. .venv/bin/python scripts/run_financial_pipeline.py --project-id 139500
  PYTHONPATH=. .venv/bin/python scripts/run_financial_pipeline.py --limit 5
  PYTHONPATH=. .venv/bin/python scripts/run_financial_pipeline.py --project-id 139500 --send-alert
  PYTHONPATH=. .venv/bin/python scripts/run_financial_pipeline.py --project-id 139500 \\
      --send-alert --backend-url http://localhost:8001
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from typing import Any, Dict, Optional

logging.basicConfig(
    level=logging.WARNING,
    format="%(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("run_financial_pipeline")

APPROVED_SCORE_CUTOFF: float = -0.093716
DEFAULT_BACKEND_URL: str = "http://localhost:8000"
MAX_SAFE_LIMIT: int = 50  # Safety cap — never process thousands in one run


def print_inference_result(result: Dict[str, Any], project_num: int = 1) -> None:
    """Print inference result fields in a structured, readable format."""
    sep = "─" * 60

    print(f"\n{sep}")
    print(f"  PROJECT #{project_num}  |  ID: {result.get('project_identifier', 'UNKNOWN')}")
    print(sep)

    fv = result.get("feature_values") or {}
    sanction_amount = fv.get("sanction_amount", None)
    rec_to_sanc = fv.get("rec_to_sanc_days", None)
    days_since_tenure = fv.get("days_since_tenure_start", None)

    if sanction_amount is not None:
        print(f"  Sanction Amount (INR)       : Rs {sanction_amount:,.2f}")
    else:
        print(f"  Sanction Amount (INR)       : N/A")

    if rec_to_sanc is not None:
        print(f"  Rec to Sanction Days        : {rec_to_sanc:.0f} days")
    else:
        print(f"  Rec to Sanction Days        : N/A")

    if days_since_tenure is not None:
        print(f"  Days Since Tenure Start     : {days_since_tenure:.0f} days")
    else:
        print(f"  Days Since Tenure Start     : N/A")

    anomaly_score = result.get("anomaly_score")
    if anomaly_score is not None:
        print(f"  Anomaly Score               : {anomaly_score:.6f}  (cutoff: {APPROVED_SCORE_CUTOFF})")
    else:
        print(f"  Anomaly Score               : N/A (validation failed)")

    raw_pred = result.get("model_prediction_for_diagnostics")
    if raw_pred is not None:
        raw_label = "ANOMALY (-1)" if raw_pred == -1 else "NORMAL (1)"
        print(f"  Raw Model Prediction (diag) : {raw_label}")
    else:
        print(f"  Raw Model Prediction (diag) : N/A")

    is_model_anomaly = (anomaly_score is not None) and (anomaly_score <= APPROVED_SCORE_CUTOFF)
    print(f"  Model Anomaly (score-based) : {'YES' if is_model_anomaly else 'NO'}")

    rule_tags = result.get("anomaly_features", [])
    if rule_tags:
        print(f"  Rule Tags                   : {', '.join(rule_tags)}")
    else:
        print(f"  Rule Tags                   : (none)")

    is_anomalous = result.get("is_anomalous", False)
    status_label = "*** ANOMALOUS ***" if is_anomalous else "[NORMAL]"
    print(f"  Final is_anomalous          : {status_label}")

    variance = result.get("variance_amount_inr")
    if variance is None:
        print(f"  variance_amount_inr         : null  (expenditure unavailable -- not fabricated)")
    else:
        print(f"  variance_amount_inr         : Rs {variance:,.2f}")

    val_errors = result.get("validation_errors", [])
    if val_errors:
        print(f"\n  Validation Errors:")
        for e in val_errors:
            print(f"    - {e}")

    val_warnings = result.get("validation_warnings", [])
    if val_warnings:
        print(f"\n  Validation Warnings:")
        for w in val_warnings:
            print(f"    - {w}")

    print(sep)


def run_pipeline_on_record(
    record: Dict[str, Any],
    send_alert: bool,
    backend_url: str,
    project_num: int = 1,
) -> Dict[str, Any]:
    """Run the complete inference pipeline on a single normalized record."""
    from ml_modules.financial.inference import FinancialAnomalyInferencePipeline

    pipeline = FinancialAnomalyInferencePipeline()
    result = pipeline.predict_single_record(record)
    print_inference_result(result, project_num=project_num)

    if send_alert:
        from ml_modules.financial.send_alert import FinancialAlertClient
        client = FinancialAlertClient(base_url=backend_url)

        print(f"\n  Sending alert to: {client.full_url}")
        alert_result = client.send_alert(result)

        if alert_result["success"]:
            print(f"  Backend response [{alert_result['status_code']}]: "
                  f"{json.dumps(alert_result['response_data'], indent=2)}")
        else:
            err_msg = alert_result.get("error", "Unknown error")
            status = alert_result.get("status_code")
            if status is None:
                print(
                    f"\nBACKEND UNAVAILABLE\n"
                    f"  Error: {err_msg}\n"
                    f"  Ensure the FastAPI server is running at: {backend_url}\n"
                    f"  Start it with: PYTHONPATH=. .venv/bin/uvicorn main:app --reload\n",
                    file=sys.stderr,
                )
                sys.exit(2)
            else:
                print(
                    f"\nBackend returned HTTP {status}\n"
                    f"  Error: {err_msg}\n",
                    file=sys.stderr,
                )
                sys.exit(3)

    return result


def run_single_project_by_id(
    project_id: str,
    db_uri: Optional[str],
    send_alert: bool,
    backend_url: str,
) -> None:
    """Fetch one project by ID from PostgreSQL and run inference."""
    from ml_modules.financial.data_loader import PostgreSQLDataLoader

    loader = PostgreSQLDataLoader(db_uri=db_uri)

    try:
        record = loader.fetch_project_by_id(project_id)
    except ConnectionError as e:
        print(
            f"\nDATABASE UNAVAILABLE\n"
            f"Could not connect to the database: {e}\n"
            f"Set DATABASE_URL environment variable or pass --db-uri.\n",
            file=sys.stderr,
        )
        sys.exit(1)
    except RuntimeError as e:
        print(f"\nDATABASE QUERY FAILED\n{e}\n", file=sys.stderr)
        sys.exit(1)

    if record is None:
        print(f"\nProject ID '{project_id}' not found in the database.\n", file=sys.stderr)
        sys.exit(1)

    print(f"\n[Pipeline] Loaded project '{project_id}' from database.")
    present = [k for k, v in record.items() if v is not None]
    absent = [k for k, v in record.items() if v is None]
    print(f"[Pipeline] Available fields : {present}")
    print(f"[Pipeline] Absent (None)    : {absent}  <- NOT fabricated")

    run_pipeline_on_record(record, send_alert=send_alert, backend_url=backend_url, project_num=1)


def run_batch_from_db(
    limit: int,
    db_uri: Optional[str],
    send_alert: bool,
    backend_url: str,
) -> None:
    """Fetch up to `limit` projects from PostgreSQL and run inference."""
    from ml_modules.financial.data_loader import PostgreSQLDataLoader

    if limit > MAX_SAFE_LIMIT:
        print(
            f"WARNING: Requested limit {limit} exceeds safe demo cap ({MAX_SAFE_LIMIT}). "
            f"Capping at {MAX_SAFE_LIMIT}.",
            file=sys.stderr,
        )
        limit = MAX_SAFE_LIMIT

    loader = PostgreSQLDataLoader(db_uri=db_uri)

    try:
        records = loader.fetch_sanctioned_projects_batch(limit=limit)
    except ConnectionError as e:
        print(
            f"\nDATABASE UNAVAILABLE\n"
            f"Could not connect to the database: {e}\n"
            f"Set DATABASE_URL environment variable or pass --db-uri.\n",
            file=sys.stderr,
        )
        sys.exit(1)
    except RuntimeError as e:
        print(f"\nDATABASE QUERY FAILED\n{e}\n", file=sys.stderr)
        sys.exit(1)

    if not records:
        print("\nNo sanctioned project records found in the database.\n", file=sys.stderr)
        sys.exit(1)

    print(f"\n[Pipeline] Loaded {len(records)} record(s) from database.")

    anomaly_count = 0
    for i, record in enumerate(records, start=1):
        result = run_pipeline_on_record(
            record,
            send_alert=send_alert,
            backend_url=backend_url,
            project_num=i,
        )
        if result.get("is_anomalous"):
            anomaly_count += 1

    print(f"\n[Pipeline] Summary: {anomaly_count}/{len(records)} records flagged as anomalous.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "SIH26102 Financial Anomaly Pipeline Runner — Checkpoint 11\n\n"
            "Loads real project records from PostgreSQL -> validates -> ML inference\n"
            "-> rule engine -> optionally sends to backend.\n\n"
            "NEVER fabricates financial values. variance_amount_inr is always null."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    project_group = parser.add_mutually_exclusive_group()
    project_group.add_argument(
        "--project-id",
        type=str,
        default=None,
        metavar="ID",
        help="Fetch and process a single project by ID from PostgreSQL.",
    )
    project_group.add_argument(
        "--limit",
        type=int,
        default=None,
        metavar="N",
        help=(
            f"Fetch and process a small batch of up to N projects (max {MAX_SAFE_LIMIT}). "
            "Cannot be used with --project-id."
        ),
    )

    parser.add_argument(
        "--send-alert",
        action="store_true",
        default=False,
        help=(
            "Send the inference result to POST /api/v1/financial-anomalies. "
            "Without this flag only ML inference runs and no HTTP request is made."
        ),
    )

    parser.add_argument(
        "--backend-url",
        type=str,
        default=DEFAULT_BACKEND_URL,
        metavar="URL",
        help=f"Base URL of the FastAPI backend (default: {DEFAULT_BACKEND_URL}).",
    )

    parser.add_argument(
        "--db-uri",
        type=str,
        default=None,
        metavar="URI",
        help=(
            "PostgreSQL connection string, e.g. postgresql://user:pass@localhost:5432/mplads. "
            "Falls back to DATABASE_URL environment variable if not set."
        ),
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    db_uri = args.db_uri or os.getenv("DATABASE_URL")

    print("=" * 60)
    print("  SIH26102 Financial Anomaly Pipeline -- Checkpoint 11")
    print("=" * 60)
    print(f"  Approved score cutoff : {APPROVED_SCORE_CUTOFF}")
    print(f"  Backend URL           : {args.backend_url}")
    print(f"  Send alert            : {'YES' if args.send_alert else 'NO (inference only)'}")
    print(f"  DB URI                : {'SET' if db_uri else 'NOT SET -- will fail if DB required'}")

    if args.project_id is not None:
        run_single_project_by_id(
            project_id=args.project_id,
            db_uri=db_uri,
            send_alert=args.send_alert,
            backend_url=args.backend_url,
        )
    elif args.limit is not None:
        run_batch_from_db(
            limit=args.limit,
            db_uri=db_uri,
            send_alert=args.send_alert,
            backend_url=args.backend_url,
        )
    else:
        # Default: attempt to load first 1 sanctioned record from DB
        print("\n  No --project-id or --limit given. Defaulting to --limit 1.")
        run_batch_from_db(
            limit=1,
            db_uri=db_uri,
            send_alert=args.send_alert,
            backend_url=args.backend_url,
        )


if __name__ == "__main__":
    main()
