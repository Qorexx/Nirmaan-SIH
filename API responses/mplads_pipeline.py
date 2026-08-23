import json
import time
import pandas as pd
import requests

ENDPOINT_URL = (
    "https://mplads.mospi.gov.in/rest/PreLoginDashboardData/getTilesReportData"
)
OUTPUT_CSV = "mplads_projects.csv"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Content-Type": "application/json; charset=UTF-8",
    "Accept": "application/json, text/plain, */*",
}

WORK_KEYS = ["Works Sanctioned", "Works Recommended", "Works Completed"]
STATE_IDS = range(1, 37)  # States & UTs (1 to 36)
HOUSE_ID = "2"  # Lok Sabha


def fetch_tile_data(state_id: int, key: str) -> list:
    combo = f"{state_id},0,0,{HOUSE_ID}"
    payload = {"combo": combo, "key": key}

    try:
        response = requests.post(
            ENDPOINT_URL,
            json=payload,
            headers=HEADERS,
            timeout=25,
            allow_redirects=False,
        )
        if response.status_code != 200:
            return []

        data = response.json()
        for _, raw_val in data.items():
            if raw_val:
                records = (
                    json.loads(raw_val) if isinstance(raw_val, str) else raw_val
                )
                if isinstance(records, list) and len(records) > 0:
                    for item in records:
                        item["QUERY_CATEGORY"] = key
                    return records
        return []
    except Exception as e:
        print(f"  [!] Error on State {state_id} ({key}): {e}")
        return []


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

    if "sanction_amount" in df.columns:
        df["sanction_amount"] = pd.to_numeric(
            df["sanction_amount"], errors="coerce"
        ).fillna(0.0)

    date_cols = [
        "recommendation_date",
        "sanction_date",
        "tenure_start_date",
        "tenure_end_date",
    ]
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    if "work_recommendation_dtl_id" in df.columns:
        df = df.drop_duplicates(
            subset=["work_recommendation_dtl_id", "query_category"]
        )

    return df


def main():
    all_records = []
    print(f"[*] Starting extraction across {len(STATE_IDS)} states...")

    for state_id in STATE_IDS:
        print(f" -> Fetching State ID: {state_id}...")
        for key in WORK_KEYS:
            records = fetch_tile_data(state_id, key)
            if records:
                all_records.extend(records)
                print(f"    [+] {key}: {len(records)} records")
            time.sleep(0.3)

    if not all_records:
        print("[!] No records extracted.")
        return

    print(
        f"\n[*] Total records collected: {len(all_records)}. Cleaning data..."
    )
    df = clean_dataframe(pd.DataFrame(all_records))
    df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8")
    print(
        f"[✓] Pipeline complete! Saved {len(df)} project rows to '{OUTPUT_CSV}'"
    )


if __name__ == "__main__":
    main()