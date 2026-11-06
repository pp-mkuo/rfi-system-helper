#!/usr/bin/env python3
"""Append new RFI Q&A pairs from rfi_new_parsed.json to the Loopio library CSV."""

import csv
import json
import os
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_PATH = os.path.join(SCRIPT_DIR, "rfi_new_parsed.json")
CSV_PATH = os.path.join(os.path.dirname(SCRIPT_DIR), "Loopio -> Claude", "loopio_library_export.csv")
OUTPUT_PATH = os.path.join(SCRIPT_DIR, "loopio_library_export_updated.csv")

# Find the max existing ID to continue from
def get_max_id(csv_path):
    max_id = 0
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                row_id = int(row["id"])
                if row_id > max_id:
                    max_id = row_id
            except (ValueError, KeyError):
                pass
    return max_id


def main():
    # Read existing CSV
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        existing_rows = list(reader)

    print(f"Existing CSV: {len(existing_rows)} rows")

    # Read new RFI entries
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        new_entries = json.load(f)

    print(f"New RFI entries: {len(new_entries)}")

    # Start IDs after the max existing
    max_id = get_max_id(CSV_PATH)
    today = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.000Z")

    new_rows = []
    for i, entry in enumerate(new_entries, 1):
        row = {field: "" for field in fieldnames}
        row["id"] = str(max_id + i)
        row["question"] = entry["question"]
        row["answer_plain"] = entry["answer"]
        row["answer_html"] = ""
        row["stack_name"] = "Client Strategy- Cleaned"
        row["category_name"] = entry["category"]
        row["tags"] = "DSP Pharma RFI; 2026"
        row["status"] = "approved"
        row["language"] = "en"
        row["created_date"] = today
        row["last_updated_date"] = today
        new_rows.append(row)

    # Write combined CSV
    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(existing_rows)
        writer.writerows(new_rows)

    total = len(existing_rows) + len(new_rows)
    print(f"\nWritten {total} rows to {OUTPUT_PATH}")
    print(f"  - Existing: {len(existing_rows)}")
    print(f"  - New:      {len(new_rows)} (IDs {max_id + 1} - {max_id + len(new_rows)})")


if __name__ == "__main__":
    main()
