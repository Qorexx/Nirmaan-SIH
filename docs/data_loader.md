# PostgreSQL Data Loader Integration — Technical Specification

**Project:** SIH 2026 — Problem Statement SIH26102 (MoSPI)  
**Lead:** Person 1 (Financial AI / Anomaly Detection Engine)  
**Module:** `ml_modules/financial/data_loader.py`  
**Date:** 2026-08-23  

---

## 1. Database Source

The **PostgreSQL Data Loader** (`PostgreSQLDataLoader`) connects the core relational database configuration to Person 1's Financial Anomaly Detection Engine.

It retrieves project records directly from PostgreSQL tables and maps them cleanly into normalized Python dictionaries compatible with `FinancialAnomalyInferencePipeline.predict_single_record()`.

---

## 2. Tables Inspected

Based on repository inspection of `sih_context_full.md` (Section 5: Database DDL Architecture) and official dataset specifications:

| Table Name | Inspected Role & Purpose | Key Primary / Foreign Keys |
| :--- | :--- | :--- |
| `projects` | Primary MPLADS core project table storing sanctions, timelines, and metadata. | `id` (UUID / Primary Key), `agency_id` (FK to `agencies`) |
| `transactions` | Prospective DDL table for financial disbursals and expenditures. | `id` (Primary Key), `project_id` (FK to `projects`) |
| `agencies` | Contractor and implementing agency registry. | `id` (Primary Key), `gstin` |

---

## 3. Available Fields

The following project fields are verified as available in the current dataset and database mapping:

| Field Name | Database Column | Data Type | Pipeline Target Key | Description |
| :--- | :--- | :--- | :--- | :--- |
| `project_id` | `projects.id` | VARCHAR / UUID | `work_recommendation_dtl_id` | Unique project identifier |
| `sanction_amount` | `projects.sanctioned_amount` | DECIMAL(15,2) | `sanction_amount` | Approved project sanction amount in INR |
| `recommendation_date` | `projects.start_date` / `recommendation_date` | DATE / TIMESTAMP | `recommendation_date` | Date MP recommended the work |
| `sanction_date` | `projects.sanction_date` | DATE / TIMESTAMP | `sanction_date` | Date District Authority sanctioned the project |
| `tenure_start_date` | `projects.tenure_start_date` | DATE / TIMESTAMP | `tenure_start_date` | Commencement date of MP Lok Sabha tenure |
| `category` | `projects.category` | VARCHAR | `category` | Project work category |
| `district_authority` | `projects.district_authority` | VARCHAR | `district_authority` | Implementing district authority name |

---

## 4. Missing Fields

The following prospective fields are **ABSENT** from the official dataset snapshot and runtime data:

| Field Name | Prospective Table | Status in Loader | Rationale / Limitation |
| :--- | :--- | :---: | :--- |
| `expenditure` | `transactions` | `None` | Transaction logs unavailable; no expenditure recorded |
| `funds_released` | `transactions` | `None` | Disbursal logs unavailable; no release recorded |
| `physical_progress_pct` | `projects` | `None` | Site progress update telemetry unavailable |
| `pfms_status` | `transactions` | `None` | PFMS payout gateway logs unavailable |
| `transaction_type` | `transactions` | `None` | Transaction categorization logs unavailable |

> [!IMPORTANT]
> **No Value Fabrication Policy:** The data loader explicitly maps all missing financial fields to `None`. It NEVER invents, fabricates, or imputes zero/synthetic values for absent financial tracking signals.

---

## 5. Query Logic

The loader executes read-only SQL queries via SQLAlchemy text execution or DB-API cursor mappings:

```sql
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
LIMIT 1;
```

---

## 6. Record Mapping

The function `normalize_db_record()` translates database column aliases into standardized pipeline feature names:

```python
{
    "work_recommendation_dtl_id": raw_dict.get("id"),
    "sanction_amount": float(raw_dict.get("sanctioned_amount")),
    "recommendation_date": raw_dict.get("start_date"),
    "sanction_date": raw_dict.get("sanction_date"),
    "tenure_start_date": raw_dict.get("tenure_start_date"),
    "expenditure": None,
    "funds_released": None,
    "physical_progress_pct": None,
    "pfms_status": None,
    "transaction_type": None
}
```

---

## 7. Error Handling

1. **Missing Connection URI:** If `DATABASE_URL` is missing and no connection is passed, raises `ConnectionError`.
2. **Database Query Failure:** Network or SQL syntax failures catch exceptions and raise `RuntimeError` without crashing unhandled.
3. **Record Not Found:** `fetch_project_by_id()` returns `None` gracefully if no matching record exists in the table.
4. **Mock Connection Support:** Supports dependency-injected mock connection objects for unit testing without live PostgreSQL servers.

---

## 8. Limitations

1. **Read-Only Scope:** The data loader does NOT write, update, or alter any database records.
2. **No Financial Variance Calculation:** Because expenditure data is absent, `variance_amount_inr` remains `None` when passed to `FinancialAnomalyInferencePipeline`.
