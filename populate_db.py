import os
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine

# 1. Connect to your Supabase PostgreSQL database
load_dotenv()
SUPABASE_URL = os.environ.get("SUPABASE_URL")
if not SUPABASE_URL:
    raise RuntimeError("SUPABASE_URL not set. Copy .env.example to .env and fill in your credentials.")
engine = create_engine(SUPABASE_URL)

print("[*] Reading local mplads_projects.csv...")
df = pd.read_csv("mplads_projects.csv")

# 2. Populate 'states' table
print("[*] Populating states table...")
if "state_id" in df.columns and "state_name" in df.columns:
    states_df = df[["state_id", "state_name"]].drop_duplicates().dropna(subset=["state_id"])
    states_df.to_sql("states", engine, if_exists="append", index=False, chunksize=5000)

# 3. Populate 'constituencies' table
print("[*] Populating constituencies table...")
if "constituency_name" in df.columns and "state_id" in df.columns:
    const_df = df[["state_id", "constituency_name"]].drop_duplicates().dropna(subset=["constituency_name"])
    # Let Supabase auto-increment constituency_id
    const_df.to_sql("constituencies", engine, if_exists="append", index=False, chunksize=5000)

# 4. Populate 'mps' table
print("[*] Populating mps table...")
mp_cols = [c for c in ["mp_name", "house_of_parliament", "tenure_name", "tenure_start_date", "tenure_end_date"] if c in df.columns]
if mp_cols:
    mp_df = df[mp_cols].drop_duplicates().dropna(subset=["mp_name"])
    mp_df.to_sql("mps", engine, if_exists="append", index=False, chunksize=5000)

# 5. Populate core 'projects' table
print("[*] Populating projects table...")
project_cols = [
    "work_recommendation_dtl_id", "query_category", "activity_name", 
    "work_description", "work_category", "work_stage", "district_name", 
    "letter_no", "recommendation_date", "sanction_date"
]
existing_proj_cols = [c for c in project_cols if c in df.columns]
if existing_proj_cols:
    proj_df = df[existing_proj_cols].drop_duplicates(subset=["work_recommendation_dtl_id"]).dropna(subset=["work_recommendation_dtl_id"])
    proj_df.to_sql("projects", engine, if_exists="append", index=False, chunksize=2000)

# 6. Populate 'financial_records' table
print("[*] Populating financial_records table...")
fin_cols = [c for c in ["work_recommendation_dtl_id", "sanction_amount", "actual_amount", "total_amt"] if c in df.columns]
if fin_cols:
    fin_df = df[fin_cols].dropna(subset=["work_recommendation_dtl_id"])
    fin_df.to_sql("financial_records", engine, if_exists="append", index=False, chunksize=2000)

print("[✓] All normalized tables successfully populated from CSV data!")