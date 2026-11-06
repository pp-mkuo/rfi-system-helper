#!/usr/bin/env python3
"""Export all Loopio library entries to CSV."""

import csv
import json
import os
import sys
import time
import urllib.request
import urllib.parse
import urllib.error

BASE_URL = "https://api.loopio.com"
CLIENT_ID = os.environ["LOOPIO_CLIENT_ID"]
CLIENT_SECRET = os.environ["LOOPIO_CLIENT_SECRET"]

def get_access_token():
    data = urllib.parse.urlencode({
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "scope": "library:read",
    }).encode()
    req = urllib.request.Request(f"{BASE_URL}/oauth2/access_token", data=data, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())["access_token"]

def api_get(token, path, params=None):
    url = f"{BASE_URL}{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/json")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())

def fetch_all_entries(token):
    """Paginate through all library entries."""
    all_entries = []
    page = 1
    page_size = 50
    while True:
        print(f"  Fetching page {page}...", flush=True)
        try:
            data = api_get(token, "/data/v2/libraryEntries", {
                "page": page,
                "pageSize": page_size,
            })
        except urllib.error.HTTPError as e:
            body = e.read().decode() if e.fp else ""
            print(f"  Error on page {page}: {e.code} {e.reason} — {body}")
            break
        items = data.get("items", [])
        all_entries.extend(items)
        total_items = data.get("totalItems", 0)
        total_pages = data.get("totalPages", 1)
        print(f"  Got {len(items)} entries (total: {total_items}, page {page}/{total_pages})")
        if page >= total_pages:
            break
        page += 1
        time.sleep(0.7)  # respect 100 calls/60s rate limit
    return all_entries

def flatten_entry(entry):
    """Flatten a library entry into a dict for CSV."""
    questions = entry.get("questions", [])
    q_text = "; ".join(q.get("text", "") for q in questions) if questions else ""
    compliance = ""
    if questions and questions[0].get("complianceOption"):
        compliance = questions[0]["complianceOption"].get("text", "")
    answer = entry.get("answer") or {}
    answer_text = answer.get("text", "")
    export_text = answer.get("exportText", "")
    footnotes = ""
    if answer.get("footnotes"):
        footnotes = "; ".join(f.get("name", f.get("text", "")) for f in answer["footnotes"])
    location = entry.get("location") or {}
    stack = location.get("stack") or {}
    category = location.get("category") or {}
    subcategory = location.get("subCategory") or {}
    owner = entry.get("libraryEntryOwner") or {}
    creator = entry.get("creator") or {}
    last_updated_by = entry.get("lastUpdatedBy") or {}
    tags = entry.get("tags", [])

    return {
        "id": entry.get("id", ""),
        "question": q_text,
        "compliance_option": compliance,
        "answer_html": answer_text,
        "answer_plain": export_text,
        "footnotes": footnotes,
        "alert_text": entry.get("alertText", ""),
        "stack_id": stack.get("id", ""),
        "stack_name": stack.get("name", ""),
        "category_id": category.get("id", ""),
        "category_name": category.get("name", ""),
        "subcategory_id": subcategory.get("id", ""),
        "subcategory_name": subcategory.get("name", ""),
        "tags": "; ".join(tags) if tags else "",
        "status": entry.get("status", ""),
        "language": entry.get("languageCode", ""),
        "owner_name": owner.get("name", "") if owner else "",
        "creator_name": creator.get("name", "") if creator else "",
        "last_updated_by": last_updated_by.get("name", "") if last_updated_by else "",
        "created_date": entry.get("createdDate", ""),
        "last_updated_date": entry.get("lastUpdatedDate", ""),
        "last_reviewed_date": entry.get("lastReviewedDate", ""),
        "attachment_count": entry.get("attachmentCount", 0),
        "score_time": entry.get("scores", {}).get("time", ""),
        "score_usage": entry.get("scores", {}).get("usage", ""),
        "score_freshness": entry.get("scores", {}).get("freshness", ""),
        "project_usage_count": (entry.get("usageCounts") or {}).get("projectUsageCount", ""),
        "times_copied": (entry.get("usageCounts") or {}).get("timesCopied", ""),
        "total_usage_count": (entry.get("usageCounts") or {}).get("totalUsageCount", ""),
    }

def main():
    output_file = os.path.expanduser("~/loopio_library_export.csv")

    print("Authenticating with Loopio API...")
    token = get_access_token()
    print("Authenticated successfully.\n")

    print("Fetching all library entries...")
    entries = fetch_all_entries(token)
    print(f"\nTotal entries fetched: {len(entries)}\n")

    if not entries:
        print("No entries found. Exiting.")
        return

    rows = [flatten_entry(e) for e in entries]
    fieldnames = list(rows[0].keys())

    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Exported {len(rows)} entries to {output_file}")

if __name__ == "__main__":
    main()
