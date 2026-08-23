import json
import requests

# 1. API Target URL (check Headers tab in DevTools if full path differs)
url = "https://mplads.mospi.gov.in/rest/dashboard/getTilesReportData"

# 2. Request Headers (User-Agent prevents bot blocking)
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Content-Type": "application/json; charset=UTF-8",
    "Accept": "application/json, text/plain, */*",
}

# 3. Payload discovered from previous steps
payload = {
    "combo": "31,417,3042484,2",  # Or "31,0,0,2" for statewide test
    "key": "Works Sanctioned",
}

# 4. Send the POST request
response = requests.post(url, json=payload, headers=headers)

# 5. Output inspection
print(f"Status Code: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    print("\nTop-level keys in response:", list(data.keys()))

    # Parse inner JSON string if returned escaped
    sanction_work_raw = data.get("Total Sanction Work", "[]")
    if isinstance(sanction_work_raw, str):
        works = json.loads(sanction_work_raw)
    else:
        works = sanction_work_raw

    print(f"Total records retrieved: {len(works)}")
    if works:
        print("\nSample Record Preview:")
        print(json.dumps(works[0], indent=2))
else:
    print("Response text:", response.text[:300])