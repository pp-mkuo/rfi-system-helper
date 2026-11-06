#!/usr/bin/env python3
"""Seed the Loopio RFP library into Fabric Weaviate.

This script reads the Loopio library CSV and inserts entries into a Weaviate
collection via the Fabric admin API (BI Studio). Requires IAP auth.

Usage:
  # Set required env vars
  export FABRIC_BI_STUDIO_BASE_URL="https://bi-api-dev.example.com"
  export BI_FABRIC_SVC_JSON="<base64 SA JSON>"
  export FABRIC_IAP_CLIENT_ID="<IAP client ID>"
  export LOOPIO_WEAVIATE_TENANT_ID="<your tenant ID>"

  # Create collection (first time only)
  python3 seed_weaviate.py --create

  # Seed data (upsert mode — safe to re-run)
  python3 seed_weaviate.py

  # Seed from a specific CSV
  python3 seed_weaviate.py --csv /path/to/export.csv
"""

import argparse
import base64
import csv
import json
import os
import sys
import time
import uuid

import requests
from google.auth.transport.requests import Request
from google.oauth2 import service_account

# -- Config -------------------------------------------------------------------

COLLECTION_NAME = "loopio_rfp_library"
BATCH_SIZE = 50  # Weaviate batch insert limit
RATE_LIMIT_PAUSE = 0.5  # seconds between batches

COLLECTION_SCHEMA = {
    "name": COLLECTION_NAME,
    "description": "PulsePoint Loopio RFI/RFP knowledge library for pre-sales",
    "properties": [
        {"name": "question", "type": "text", "vector_source": True},
        {"name": "answer", "type": "text"},
        {"name": "stack_name", "type": "text"},
        {"name": "tags", "type": "text"},
        {"name": "last_updated", "type": "text"},
        {"name": "category_name", "type": "text"},
        {"name": "source_id", "type": "text"},
    ],
}

DEFAULT_CSV = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "loopio_library_export_updated.csv",
)


# -- IAP auth -----------------------------------------------------------------


def _get_id_token():
    """Mint a Google ID token for IAP auth."""
    iap_client_id = os.environ.get("FABRIC_IAP_CLIENT_ID", "").strip()
    sa_b64 = os.environ.get("BI_FABRIC_SVC_JSON", "").strip()

    if not iap_client_id or not sa_b64:
        sys.exit("Error: Set FABRIC_IAP_CLIENT_ID and BI_FABRIC_SVC_JSON env vars.")

    sa_info = json.loads(base64.b64decode(sa_b64).decode("utf-8"))
    credentials = service_account.IDTokenCredentials.from_service_account_info(
        sa_info, target_audience=iap_client_id
    )
    credentials.refresh(Request())
    return credentials.token


def _iap_request(method, url, json_body=None, timeout=30):
    """Make an IAP-authenticated request."""
    token = _get_id_token()
    headers = {"Authorization": f"Bearer {token}"}
    if json_body is not None:
        headers["Content-Type"] = "application/json"

    resp = requests.request(
        method, url, headers=headers, json=json_body, timeout=timeout
    )
    return resp


# -- URL helpers --------------------------------------------------------------


def _base_url():
    url = os.environ.get("FABRIC_BI_STUDIO_BASE_URL", "").strip().rstrip("/")
    if not url:
        sys.exit("Error: Set FABRIC_BI_STUDIO_BASE_URL env var.")
    return url


def _tenant_id():
    tid = os.environ.get("LOOPIO_WEAVIATE_TENANT_ID", "").strip()
    if not tid:
        sys.exit("Error: Set LOOPIO_WEAVIATE_TENANT_ID env var.")
    return tid


# -- Commands -----------------------------------------------------------------


def create_collection():
    """Create the Weaviate collection."""
    url = f"{_base_url()}/v7/fabric/collections"
    print(f"Creating collection '{COLLECTION_NAME}'...")

    resp = _iap_request("POST", url, json_body=COLLECTION_SCHEMA)

    if resp.status_code == 200:
        print(f"Collection created successfully.")
        print(json.dumps(resp.json(), indent=2))
    elif resp.status_code == 409:
        print(f"Collection '{COLLECTION_NAME}' already exists.")
    else:
        print(f"Error creating collection: HTTP {resp.status_code}")
        print(resp.text)
        sys.exit(1)


def describe_collection():
    """Check collection status."""
    tenant = _tenant_id()
    url = f"{_base_url()}/v7/fabric/collections/{tenant}/{COLLECTION_NAME}"
    resp = _iap_request("GET", url)

    if resp.status_code == 200:
        data = resp.json()
        print(f"Collection: {COLLECTION_NAME}")
        print(f"  Objects: {data.get('object_count', 'unknown')}")
        print(f"  Cold start: {data.get('cold_start', 'unknown')}")
    else:
        print(f"Error: HTTP {resp.status_code} — {resp.text}")


def read_csv(csv_path):
    """Read CSV and return list of Weaviate objects."""
    objects = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            question = (row.get("question") or "").strip()
            answer = (row.get("answer_plain") or "").strip()
            if not question and not answer:
                continue

            # Only include entries from the cleaned stack or new RFI entries
            stack = (row.get("stack_name") or "").strip()

            # Generate a deterministic UUID from the source ID for upsert
            source_id = str(row.get("id", ""))
            obj_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"loopio.{source_id}"))

            objects.append({
                "id": obj_id,
                "properties": {
                    "question": question,
                    "answer": answer,
                    "stack_name": stack,
                    "tags": (row.get("tags") or "").strip(),
                    "last_updated": (row.get("last_updated_date") or "").strip(),
                    "category_name": (row.get("category_name") or "").strip(),
                    "source_id": source_id,
                },
            })
    return objects


def seed_data(csv_path):
    """Seed CSV data into Weaviate collection."""
    tenant = _tenant_id()
    url = f"{_base_url()}/v7/fabric/collections/{tenant}/{COLLECTION_NAME}/objects:insert"

    objects = read_csv(csv_path)
    print(f"Loaded {len(objects)} entries from {csv_path}")

    if not objects:
        print("No entries to seed.")
        return

    total_inserted = 0
    total_errors = 0

    for i in range(0, len(objects), BATCH_SIZE):
        batch = objects[i : i + BATCH_SIZE]

        body = {"upsert": True, "objects": batch}
        resp = _iap_request("POST", url, json_body=body, timeout=60)

        if resp.status_code in (200, 207):
            data = resp.json()
            inserted = len(data.get("inserted", []))
            errors = data.get("errors", [])
            total_inserted += inserted
            total_errors += len(errors)

            if errors:
                print(f"  Batch {i // BATCH_SIZE + 1}: {inserted} inserted, {len(errors)} errors")
                for err in errors[:3]:
                    print(f"    Error: {err}")
            else:
                print(f"  Batch {i // BATCH_SIZE + 1}: {inserted} inserted ({total_inserted}/{len(objects)})")
        else:
            print(f"  Batch {i // BATCH_SIZE + 1}: HTTP {resp.status_code}")
            print(f"    {resp.text[:500]}")
            total_errors += len(batch)

        time.sleep(RATE_LIMIT_PAUSE)

    print(f"\nDone. Inserted: {total_inserted}, Errors: {total_errors}")


# -- Main ---------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(description="Seed Loopio library into Fabric Weaviate")
    parser.add_argument("--create", action="store_true", help="Create the collection (first time only)")
    parser.add_argument("--describe", action="store_true", help="Describe collection status")
    parser.add_argument("--csv", default=DEFAULT_CSV, help="Path to CSV file")
    args = parser.parse_args()

    if args.create:
        create_collection()
    elif args.describe:
        describe_collection()
    else:
        seed_data(args.csv)


if __name__ == "__main__":
    main()
