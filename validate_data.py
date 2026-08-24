import pandas as pd

df = pd.read_csv("mplads_projects.csv")

# Print available columns to see exact naming
print("Available columns in dataset:", list(df.columns))
print("=" * 60)

sample_df = df.sample(3)

for idx, row in sample_df.iterrows():
    print(f"\n[-] Record ID: {row.get('work_recommendation_dtl_id', 'N/A')}")
    # Check alternative column names if primary is missing
    mp = row.get('mp_name') or row.get('mp') or 'N/A'
    const = row.get('constituency_name') or row.get('constituency') or row.get('pc_name') or 'N/A'
    activity = row.get('activity_name') or row.get('work_name') or 'N/A'
    amount = row.get('sanction_amount') or row.get('amount') or 0.0
    date = row.get('sanction_date') or row.get('date') or 'N/A'
    status = row.get('work_stage') or row.get('query_category') or 'N/A'

    print(f"    • MP Name       : {mp}")
    print(f"    • Constituency  : {const}")
    print(f"    • Project/Activity: {str(activity)[:60]}...")
    print(f"    • Amount (₹)    : {amount}")
    print(f"    • Date/Year     : {date}")
    print(f"    • Status        : {status}")
    print("-" * 60)