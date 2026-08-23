import os
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# 1. Connect to your Supabase PostgreSQL database
load_dotenv()
SUPABASE_URL = os.environ.get("SUPABASE_URL")
if not SUPABASE_URL:
    raise RuntimeError("SUPABASE_URL not set. Copy .env.example to .env and fill in your credentials.")
engine = create_engine(SUPABASE_URL)

print("[*] Reading local mplads_projects.csv...")
df = pd.read_csv("mplads_projects.csv")

# 2. SQL commands to create the clean, normalized tables
ddl_query = """
CREATE TABLE IF NOT EXISTS states (
    state_id INTEGER PRIMARY KEY,
    state_name VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS constituencies (
    constituency_id SERIAL PRIMARY KEY,
    state_id INTEGER REFERENCES states(state_id),
    constituency_name VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS mps (
    mp_id SERIAL PRIMARY KEY,
    mp_name VARCHAR(255),
    house_of_parliament INTEGER,
    tenure_name VARCHAR(255),
    tenure_start_date TIMESTAMP,
    tenure_end_date TIMESTAMP
);

CREATE TABLE IF NOT EXISTS projects (
    work_recommendation_dtl_id BIGINT PRIMARY KEY,
    query_category VARCHAR(100),
    activity_name TEXT,
    work_description TEXT,
    work_category VARCHAR(255),
    work_stage VARCHAR(100),
    district_name VARCHAR(255),
    constituency_id INTEGER REFERENCES constituencies(constituency_id),
    mp_id INTEGER REFERENCES mps(mp_id),
    letter_no VARCHAR(255),
    recommendation_date DATE,
    sanction_date DATE
);

CREATE TABLE IF NOT EXISTS financial_records (
    financial_record_id SERIAL PRIMARY KEY,
    work_recommendation_dtl_id BIGINT REFERENCES projects(work_recommendation_dtl_id),
    sanction_amount NUMERIC(15, 2),
    actual_amount NUMERIC(15, 2),
    total_amt NUMERIC(15, 2)
);
"""

print("[*] Creating normalized tables in Supabase...")
with engine.begin() as conn:
    for statement in ddl_query.split(";"):
        if statement.strip():
            conn.execute(text(statement))

print(
    "[✓] Database schema successfully initialized based on MPLADS API fields!"
)