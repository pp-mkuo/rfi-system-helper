#!/usr/bin/env python3
"""Ingest Loopio library CSV into Pinecone using OpenAI text-embedding-3-small."""

import csv
import os
import sys
from pinecone import Pinecone
from openai import OpenAI

# ── Config ──────────────────────────────────────────────────────────────
PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
INDEX_NAME = "loopio-library-2"
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIM = 1536
CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Loopio -> Claude", "loopio_library_export.csv")
BATCH_SIZE = 96

for key_name, key_val in [("PINECONE_API_KEY", PINECONE_API_KEY), ("OPENAI_API_KEY", OPENAI_API_KEY)]:
    if not key_val:
        sys.exit(f"Error: Set {key_name} environment variable.")


def embed_texts(client, texts):
    """Generate embeddings via OpenAI API."""
    response = client.embeddings.create(model=EMBEDDING_MODEL, input=texts)
    return [item.embedding for item in response.data]


def read_csv(path):
    """Read CSV and return list of dicts with id, text, and metadata."""
    entries = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            question = (row.get("question") or "").strip()
            answer = (row.get("answer_plain") or "").strip()
            if not question and not answer:
                continue
            text = f"{question}\n\n{answer}" if answer else question
            tags = [t.strip() for t in (row.get("tags") or "").split(";") if t.strip()]
            entries.append({
                "id": str(row["id"]),
                "text": text,
                "metadata": {
                    "stack_name": row.get("stack_name", ""),
                    "question": question,
                    "answer_plain": answer,
                    "tags": tags,
                    "last_updated_date": row.get("last_updated_date", ""),
                },
            })
    return entries


def main():
    pc = Pinecone(api_key=PINECONE_API_KEY)
    openai_client = OpenAI(api_key=OPENAI_API_KEY)

    # Create index if it doesn't exist
    existing = [idx.name for idx in pc.list_indexes()]
    if INDEX_NAME not in existing:
        print(f"Creating index '{INDEX_NAME}'...")
        pc.create_index(
            name=INDEX_NAME,
            dimension=EMBEDDING_DIM,
            metric="cosine",
            spec={"serverless": {"cloud": "aws", "region": "us-east-1"}},
        )
        print("Index created.")
    else:
        print(f"Index '{INDEX_NAME}' already exists.")

    index = pc.Index(INDEX_NAME)

    # Read entries
    entries = read_csv(CSV_PATH)
    print(f"Loaded {len(entries)} entries from CSV.")

    # Embed and upsert in batches
    total_upserted = 0
    for i in range(0, len(entries), BATCH_SIZE):
        batch = entries[i : i + BATCH_SIZE]
        texts = [e["text"] for e in batch]

        # Generate embeddings via OpenAI
        vectors_data = embed_texts(openai_client, texts)

        # Build upsert vectors
        vectors = []
        for entry, embedding in zip(batch, vectors_data):
            vectors.append({
                "id": entry["id"],
                "values": embedding,
                "metadata": entry["metadata"],
            })

        index.upsert(vectors=vectors)
        total_upserted += len(vectors)
        print(f"  Upserted {total_upserted}/{len(entries)}")

    print(f"\nDone. {total_upserted} vectors stored in '{INDEX_NAME}'.")


if __name__ == "__main__":
    main()
