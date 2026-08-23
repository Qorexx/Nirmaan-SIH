# MPLADS Data Extraction & Database Pipeline

Automated extraction, cleaning, and database loading pipeline for **Members of Parliament Local Area Development Scheme (MPLADS)** project data from the [MoSPI official portal](https://mplads.mospi.gov.in/).

## Overview

This project scrapes project-level data across all 36 Indian states & UTs from the MPLADS pre-login dashboard API, cleans and deduplicates the records, and loads them into a normalized **Supabase PostgreSQL** database.

```
MoSPI Portal API ──► mplads_pipeline.py ──► mplads_projects.csv
                                                    │
                                                    ▼
                                            migrate_db.py  (create schema)
                                                    │
                                                    ▼
                                            populate_db.py (load data)
                                                    │
                                                    ▼
                                            validate_data.py (verify)
```

## Data Summary

| Metric | Value |
|--------|-------|
| States & UTs covered | 36 |
| Columns per record | 29 |
| Query categories | Works Sanctioned, Works Recommended, Works Completed |
| Source endpoint | `getTilesReportData` (pre-login dashboard) |

### Key Fields

`work_recommendation_dtl_id` · `mp_name` · `constituency` · `state_name` · `activity_name` · `work_description` · `work_category` · `work_stage` · `sanction_amount` · `actual_amount` · `total_amt` · `recommendation_date` · `sanction_date` · `house_of_parliament` · `tenure_start_date` · `tenure_end_date`

## Database Schema

The pipeline normalizes flat CSV data into 5 relational tables:

```
states (state_id, state_name)
  └── constituencies (constituency_id, state_id, constituency_name)

mps (mp_id, mp_name, house_of_parliament, tenure_name, tenure_start_date, tenure_end_date)

projects (work_recommendation_dtl_id, query_category, activity_name, work_description,
          work_category, work_stage, district_name, constituency_id → constituencies,
          mp_id → mps, letter_no, recommendation_date, sanction_date)

financial_records (financial_record_id, work_recommendation_dtl_id → projects,
                   sanction_amount, actual_amount, total_amt)
```

## Repository Structure

```
├── mplads_api_test.py        # Initial MoSPI pre-login endpoint tests
├── mplads_pipeline.py        # Multi-state scraper, cleaner & deduplication pipeline
├── migrate_db.py             # Database migration for normalized Supabase tables
├── populate_db.py            # Relational database population script
├── feature_engineering.py    # Derived features for analytics & ML
├── validate_data.py          # Data verification against official portal values
├── requirements.txt          # Package dependencies
├── .env.example              # Environment variable template
└── .gitignore                # Git ignore rules
```

## Setup

### 1. Clone & install dependencies

```bash
git clone https://github.com/Qorexx/Nirmaan-SIH.git
cd Nirmaan-SIH
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env and set your Supabase PostgreSQL connection string
```

### 3. Run the pipeline

```bash
# Step 1: Extract data from MoSPI portal (takes ~5-10 min)
python mplads_pipeline.py

# Step 2: Create database tables in Supabase
python migrate_db.py

# Step 3: Populate tables from CSV
python populate_db.py

# Step 4: Generate derived features
python feature_engineering.py

# Step 5: Verify extracted data
python validate_data.py
```

## Scripts

| Script | Purpose |
|--------|---------|
| `mplads_api_test.py` | Tests the MoSPI pre-login API endpoints — verifies connectivity and response structure before running the full pipeline |
| `mplads_pipeline.py` | Iterates over all 36 states, fetches Works Sanctioned/Recommended/Completed records, cleans column names, coerces types, deduplicates, and saves to CSV |
| `migrate_db.py` | Creates 5 normalized tables (`states`, `constituencies`, `mps`, `projects`, `financial_records`) in Supabase with foreign key relationships |
| `populate_db.py` | Reads the CSV and populates each normalized table with deduplicated, chunked inserts |
| `feature_engineering.py` | Derives ~20 new columns: time gaps (approval lag, completion duration), financial ratios (utilization, cost overrun), amount buckets, stage encodings, MP/state/constituency aggregations, and text features |
| `validate_data.py` | Samples random records and prints key fields for manual cross-verification against the official portal |

## Tech Stack

- **Python 3.10+**
- **Requests** — HTTP client for MoSPI API
- **Pandas** — Data cleaning, deduplication & transformation
- **SQLAlchemy** — Database ORM & connection management
- **Supabase (PostgreSQL)** — Cloud database hosting
- **python-dotenv** — Secure credential management

## License

This project is for educational and research purposes. MPLADS data is sourced from the publicly accessible MoSPI portal.
