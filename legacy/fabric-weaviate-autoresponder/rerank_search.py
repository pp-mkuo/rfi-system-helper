#!/usr/bin/env python3
"""Rerank-only search: retrieve from Pinecone, rerank, output top results (no Claude needed)."""

import csv
import os
import sys
from datetime import datetime
from pinecone import Pinecone
from openai import OpenAI

# -- Config ------------------------------------------------------------------
PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
INDEX_NAME = "loopio-library-2"
EMBEDDING_MODEL = "text-embedding-3-small"
RERANK_MODEL = "bge-reranker-v2-m3"
RETRIEVE_K = 20
RERANK_TOP_N = 5
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

for key_name, key_val in [("PINECONE_API_KEY", PINECONE_API_KEY), ("OPENAI_API_KEY", OPENAI_API_KEY)]:
    if not key_val:
        sys.exit(f"Error: Set {key_name} environment variable.")


def embed_query(client, text):
    """Generate embedding for a single query via OpenAI."""
    response = client.embeddings.create(model=EMBEDDING_MODEL, input=[text])
    return response.data[0].embedding


def retrieve(index, openai_client, query_text):
    """Embed query and retrieve top-K candidates from Pinecone."""
    vector = embed_query(openai_client, query_text)
    results = index.query(
        vector=vector,
        top_k=RETRIEVE_K,
        include_metadata=True,
        filter={"stack_name": {"$eq": "Client Strategy- Cleaned"}},
    )
    return results.matches


def rerank(pc, query_text, matches):
    """Rerank retrieved candidates using Pinecone's hosted reranker."""
    documents = []
    for match in matches:
        question = match.metadata.get("question", "")
        answer = match.metadata.get("answer_plain", "")
        documents.append(f"{question}\n{answer}")

    reranked = pc.inference.rerank(
        model=RERANK_MODEL,
        query=query_text,
        documents=documents,
        top_n=RERANK_TOP_N,
        return_documents=False,
    )

    results = []
    for item in reranked.data:
        original_match = matches[item.index]
        results.append((original_match, item.score))

    return results


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

    # Step 1: Retrieve
    print(f"Retrieving top-{RETRIEVE_K} candidates for: {query}\n")
    matches = retrieve(index, openai_client, query)
    print(f"Retrieved {len(matches)} candidates.\n")

    # Step 2: Rerank
    print(f"Reranking to top-{RERANK_TOP_N}...\n")
    reranked_results = rerank(pc, query, matches)

    # Step 3: Display results
    print("=" * 60)
    print("RERANKED RESULTS")
    print("=" * 60)

    for i, (match, rscore) in enumerate(reranked_results, 1):
        meta = match.metadata
        answer = meta.get("answer_plain", "")
        tags = meta.get("tags", [])
        if isinstance(tags, list):
            tags = "; ".join(tags)
        answer_preview = answer[:400] + "..." if len(answer) > 400 else answer

        print(f"\n--- Result {i} ---")
        print(f"Rerank Score: {rscore:.4f}  |  Vector Score: {match.score:.4f}")
        print(f"Stack:        {meta.get('stack_name', '')}")
        print(f"Tags:         {tags}")
        print(f"Question:     {meta.get('question', '')}")
        print(f"Last Updated: {meta.get('last_updated_date', 'unknown')}")
        print(f"Answer:       {answer_preview}")
    print()

    # Step 4: Save to CSV
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs(os.path.join(OUTPUT_DIR, "Results"), exist_ok=True)
    out_path = os.path.join(OUTPUT_DIR, "Results", f"rerank_result_{timestamp}.csv")
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "rank", "rerank_score", "vector_score",
            "question", "answer", "stack_name", "tags", "last_updated", "id",
        ])
        writer.writeheader()
        for i, (match, rscore) in enumerate(reranked_results, 1):
            meta = match.metadata
            tags = meta.get("tags", [])
            if isinstance(tags, list):
                tags = "; ".join(tags)
            writer.writerow({
                "rank": i,
                "rerank_score": round(rscore, 4),
                "vector_score": round(match.score, 4),
                "question": meta.get("question", ""),
                "answer": meta.get("answer_plain", ""),
                "stack_name": meta.get("stack_name", ""),
                "tags": tags,
                "last_updated": meta.get("last_updated_date", ""),
                "id": match.id,
            })

    print(f"Results saved to: {out_path}")


if __name__ == "__main__":
    main()
