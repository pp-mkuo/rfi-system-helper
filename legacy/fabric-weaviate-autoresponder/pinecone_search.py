#!/usr/bin/env python3
"""Search Loopio library in Pinecone by RFP question (OpenAI embeddings)."""

import csv
import os
import sys
from datetime import datetime
from pinecone import Pinecone
from openai import OpenAI

# ── Config ──────────────────────────────────────────────────────────────
PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
INDEX_NAME = "loopio-library-2"
EMBEDDING_MODEL = "text-embedding-3-small"
TOP_K = 5
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

for key_name, key_val in [("PINECONE_API_KEY", PINECONE_API_KEY), ("OPENAI_API_KEY", OPENAI_API_KEY)]:
    if not key_val:
        sys.exit(f"Error: Set {key_name} environment variable.")


def embed_query(client, text):
    """Generate embedding for a single query via OpenAI."""
    response = client.embeddings.create(model=EMBEDDING_MODEL, input=[text])
    return response.data[0].embedding


def search(index, openai_client, query_text):
    """Embed a query and return top-K matches."""
    vector = embed_query(openai_client, query_text)
    results = index.query(
        vector=vector,
        top_k=TOP_K,
        include_metadata=True,
        filter={"stack_name": {"$eq": "Client Strategy- Cleaned"}},
    )
    return results.matches


def main():
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        query = input("Enter your RFP question: ").strip()
        if not query:
            sys.exit("No question provided.")

    pc = Pinecone(api_key=PINECONE_API_KEY)
    openai_client = OpenAI(api_key=OPENAI_API_KEY)
    index = pc.Index(INDEX_NAME)

    print(f"\nSearching for: {query}\n")
    matches = search(index, openai_client, query)

    # Build output rows
    output_rows = []
    for rank, match in enumerate(matches, 1):
        tags = match.metadata.get("tags", [])
        row = {
            "rank": rank,
            "score": round(match.score, 4),
            "question": match.metadata.get("question", ""),
            "answer": match.metadata.get("answer_plain", ""),
            "stack_name": match.metadata.get("stack_name", ""),
            "tags": "; ".join(tags) if isinstance(tags, list) else tags,
            "id": match.id,
        }
        output_rows.append(row)

    # Print to terminal
    for row in output_rows:
        print(f"--- Result {row['rank']} (score: {row['score']}) ---")
        print(f"Stack:    {row['stack_name']}")
        print(f"Tags:     {row['tags']}")
        print(f"Question: {row['question']}")
        answer_preview = row["answer"][:300] + "..." if len(row["answer"]) > 300 else row["answer"]
        print(f"Answer:   {answer_preview}")
        print()

    # Save to CSV
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = os.path.join(OUTPUT_DIR, f"search_results_{timestamp}.csv")
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["rank", "score", "question", "answer", "stack_name", "tags", "id"])
        writer.writeheader()
        writer.writerows(output_rows)

    print(f"Results saved to: {out_path}")


if __name__ == "__main__":
    main()
