"""Ingest Loopio library CSV into Pinecone."""

from __future__ import annotations

import csv
import io
import json
import time
import urllib.parse
import urllib.request

from openai import OpenAI
from pinecone import Pinecone

from . import config


def read_csv_rows(file_content: str) -> list[dict]:
    """Parse CSV content and return list of dicts with id, text, and metadata."""
    entries = []
    reader = csv.DictReader(io.StringIO(file_content))
    for row in reader:
        question = (row.get("question") or "").strip()
        answer = (row.get("answer_plain") or "").strip()
        if not question and not answer:
            continue
        text = f"{question}\n\n{answer}" if answer else question
        tags = [t.strip() for t in (row.get("tags") or "").split(";") if t.strip()]
        entries.append(
            {
                "id": str(row["id"]),
                "text": text,
                "metadata": {
                    "stack_name": row.get("stack_name", ""),
                    "question": question,
                    "answer_plain": answer,
                    "tags": tags,
                    "last_updated_date": row.get("last_updated_date", ""),
                },
            }
        )
    return entries


def embed_texts(client: OpenAI, texts: list[str]) -> list[list[float]]:
    """Generate embeddings via OpenAI API."""
    response = client.embeddings.create(model=config.EMBEDDING_MODEL, input=texts)
    return [item.embedding for item in response.data]


def ingest_csv(file_content: str) -> int:
    """Ingest CSV content into Pinecone. Returns number of vectors upserted."""
    pc = Pinecone(api_key=config.PINECONE_API_KEY)
    openai_client = OpenAI(api_key=config.OPENAI_API_KEY)

    # Create index if needed
    existing = [idx.name for idx in pc.list_indexes()]
    if config.INDEX_NAME not in existing:
        pc.create_index(
            name=config.INDEX_NAME,
            dimension=config.EMBEDDING_DIM,
            metric="cosine",
            spec={"serverless": {"cloud": "aws", "region": "us-east-1"}},
        )

    index = pc.Index(config.INDEX_NAME)
    entries = read_csv_rows(file_content)
    total_upserted = 0

    for i in range(0, len(entries), config.INGEST_BATCH_SIZE):
        batch = entries[i : i + config.INGEST_BATCH_SIZE]
        texts = [e["text"] for e in batch]
        vectors_data = embed_texts(openai_client, texts)

        vectors = []
        for entry, embedding in zip(batch, vectors_data):
            vectors.append(
                {
                    "id": entry["id"],
                    "values": embedding,
                    "metadata": entry["metadata"],
                }
            )

        index.upsert(vectors=vectors)
        total_upserted += len(vectors)

    return total_upserted


# -- Loopio API export (optional) ---------------------------------------------


def export_from_loopio() -> str:
    """Fetch all library entries from Loopio API and return CSV string."""
    if not config.LOOPIO_CLIENT_ID or not config.LOOPIO_CLIENT_SECRET:
        raise ValueError("LOOPIO_CLIENT_ID and LOOPIO_CLIENT_SECRET must be set.")

    # Authenticate
    data = urllib.parse.urlencode(
        {
            "grant_type": "client_credentials",
            "client_id": config.LOOPIO_CLIENT_ID,
            "client_secret": config.LOOPIO_CLIENT_SECRET,
            "scope": "library:read",
        }
    ).encode()
    req = urllib.request.Request(
        f"{config.LOOPIO_BASE_URL}/oauth2/access_token", data=data, method="POST"
    )
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    with urllib.request.urlopen(req) as resp:
        token = json.loads(resp.read())["access_token"]

    # Paginate entries
    all_entries = []
    page = 1
    while True:
        url = f"{config.LOOPIO_BASE_URL}/data/v2/libraryEntries?page={page}&pageSize=50"
        api_req = urllib.request.Request(url)
        api_req.add_header("Authorization", f"Bearer {token}")
        api_req.add_header("Accept", "application/json")
        with urllib.request.urlopen(api_req) as resp:
            body = json.loads(resp.read())

        items = body.get("items", [])
        all_entries.extend(items)
        if page >= body.get("totalPages", 1):
            break
        page += 1
        time.sleep(0.7)

    # Flatten to CSV
    output = io.StringIO()
    fieldnames = [
        "id", "question", "answer_plain", "stack_name", "category_name",
        "tags", "status", "last_updated_date",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()

    for entry in all_entries:
        questions = entry.get("questions", [])
        q_text = "; ".join(q.get("text", "") for q in questions) if questions else ""
        answer = entry.get("answer") or {}
        location = entry.get("location") or {}
        stack = location.get("stack") or {}
        category = location.get("category") or {}
        tags = entry.get("tags", [])

        writer.writerow(
            {
                "id": entry.get("id", ""),
                "question": q_text,
                "answer_plain": answer.get("exportText", ""),
                "stack_name": stack.get("name", ""),
                "category_name": category.get("name", ""),
                "tags": "; ".join(tags) if tags else "",
                "status": entry.get("status", ""),
                "last_updated_date": entry.get("lastUpdatedDate", ""),
            }
        )

    return output.getvalue()
