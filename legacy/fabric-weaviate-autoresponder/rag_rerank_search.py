#!/usr/bin/env python3
"""RAG search with reranking: retrieve from Pinecone, rerank, synthesize with Claude."""

import csv
import os
import sys
from datetime import datetime
from pinecone import Pinecone
from openai import OpenAI
import anthropic

# -- Config ------------------------------------------------------------------
PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
INDEX_NAME = "loopio-library-2"
EMBEDDING_MODEL = "text-embedding-3-small"
RERANK_MODEL = "bge-reranker-v2-m3"
RETRIEVE_K = 20   # over-retrieve for reranking
RERANK_TOP_N = 5  # keep top-N after reranking
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

SYSTEM_PROMPT = """\
You are a PulsePoint pre-sales assistant helping respond to RFI questions. \
You will be given retrieved entries from PulsePoint's internal Loopio library.

Rules:
- Synthesize a single, complete answer from the retrieved entries.
- Older entries may have stronger foundational detail -- use them as the base.
- Newer entries may contain updated capabilities, stats, or product changes -- layer these in.
- If an older and newer entry conflict, prefer the newer one and briefly note what changed.
- Only use information from the provided entries. Do not make up facts.
- At the end, list which entry IDs you drew from under a "Sources" heading.
- Keep the tone professional and suitable for an RFP response.
- If none of the retrieved entries are relevant, say so clearly.\
"""

for key_name, key_val in [("PINECONE_API_KEY", PINECONE_API_KEY), ("OPENAI_API_KEY", OPENAI_API_KEY), ("ANTHROPIC_API_KEY", ANTHROPIC_API_KEY)]:
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


def build_context(reranked_results):
    """Format reranked entries as context for Claude."""
    entries = []
    for i, (match, rerank_score) in enumerate(reranked_results, 1):
        meta = match.metadata
        answer = meta.get("answer_plain", "")
        tags = meta.get("tags", [])
        if isinstance(tags, list):
            tags = ", ".join(tags)
        entry = (
            f"--- Entry {i} ---\n"
            f"ID: {match.id}\n"
            f"Vector Score: {round(match.score, 4)}\n"
            f"Rerank Score: {round(rerank_score, 4)}\n"
            f"Question: {meta.get('question', '')}\n"
            f"Tags: {tags}\n"
            f"Stack: {meta.get('stack_name', '')}\n"
            f"Last Updated: {meta.get('last_updated_date', 'unknown')}\n"
            f"Answer:\n{answer}\n"
        )
        entries.append(entry)
    return "\n".join(entries)


def synthesize(client, context, user_question):
    """Send reranked context + question to Claude for synthesis."""
    user_message = (
        f"Retrieved and reranked library entries:\n\n{context}\n\n"
        f"---\n\n"
        f"RFP Question: {user_question}\n\n"
        f"Please synthesize a complete answer using the entries above."
    )
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2048,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )
    return response.content[0].text


def main():
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        query = input("Enter your RFP question: ").strip()
        if not query:
            sys.exit("No question provided.")

    # Init clients
    pc = Pinecone(api_key=PINECONE_API_KEY)
    openai_client = OpenAI(api_key=OPENAI_API_KEY)
    index = pc.Index(INDEX_NAME)
    claude = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    # Step 1: Retrieve (wide net)
    print(f"Retrieving top-{RETRIEVE_K} candidates for: {query}\n")
    matches = retrieve(index, openai_client, query)
    print(f"Retrieved {len(matches)} candidates.")

    # Step 2: Rerank (narrow down)
    print(f"Reranking to top-{RERANK_TOP_N}...\n")
    reranked_results = rerank(pc, query, matches)

    # Show reranked results
    for i, (match, score) in enumerate(reranked_results, 1):
        print(f"  {i}. [rerank: {score:.4f} | vector: {match.score:.4f}] {match.metadata.get('question', '')[:80]}")
    print()

    # Step 3: Build context from reranked results
    context = build_context(reranked_results)

    # Step 4: Synthesize with Claude
    print("Synthesizing answer with Claude...\n")
    answer = synthesize(claude, context, query)

    print("=" * 60)
    print("SYNTHESIZED ANSWER")
    print("=" * 60)
    print(answer)
    print("=" * 60)

    # Save to CSV
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs(os.path.join(OUTPUT_DIR, "Results"), exist_ok=True)
    out_path = os.path.join(OUTPUT_DIR, "Results", f"rag_rerank_result_{timestamp}.csv")
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "question", "synthesized_answer",
            "source_ids", "vector_scores", "rerank_scores",
        ])
        writer.writeheader()
        writer.writerow({
            "question": query,
            "synthesized_answer": answer,
            "source_ids": "; ".join(m.id for m, _ in reranked_results),
            "vector_scores": "; ".join(str(round(m.score, 4)) for m, _ in reranked_results),
            "rerank_scores": "; ".join(str(round(s, 4)) for _, s in reranked_results),
        })

    print(f"\nResult saved to: {out_path}")


if __name__ == "__main__":
    main()
