import os
import json
from datetime import datetime
import requests
import pytz
from dotenv import load_dotenv

# Load .env file from current directory
load_dotenv(".env")  # Adjust path if needed

# Constants
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
TABLE_NAME = "financials"

headers = {
    "apikey": SUPABASE_SERVICE_KEY,
    "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
    "Content-Type": "application/json",
}

ADDED_AT_TIME = datetime.now(pytz.timezone("Asia/Kolkata")).isoformat()


def delete_all_rows():
    print("🧹 Deleting existing rows...")
    url = f"{SUPABASE_URL}/rest/v1/{TABLE_NAME}?id=not.is.null"
    response = requests.delete(url, headers=headers)
    if response.status_code == 204:
        print("✅ All rows deleted.")
    else:
        print(f"❌ Failed to delete rows. Status: {response.status_code}")
        print(response.text)


def upload_json(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Optional: Add timestamp to each row
    # for row in data:
    #     row["added_at"] = ADDED_AT_TIME

    response = requests.post(
        f"{SUPABASE_URL}/rest/v1/{TABLE_NAME}",
        headers=headers,
        json=data,
    )

    if response.status_code == 201:
        print(f"✅ Inserted {len(data)} rows from {file_path}")
    else:
        print(f"❌ Failed to insert data. Status: {response.status_code}")
        print(response.text)


if __name__ == "__main__":
    delete_all_rows()
    upload_json("output.json")
