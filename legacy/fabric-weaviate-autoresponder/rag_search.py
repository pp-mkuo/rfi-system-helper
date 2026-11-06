#!/usr/bin/env python3
"""RAG search: retrieve from Pinecone (OpenAI embeddings), synthesize with Claude."""

import csv
import os
import sys
from datetime import datetime
from pinecone import Pinecone
from openai import OpenAI
import anthropic

# ── Config ──────────────────────────────────────────────────────────────
PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
INDEX_NAME = "loopio-library-2"
EMBEDDING_MODEL = "text-embedding-3-small"
TOP_K = 10
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

SYSTEM_PROMPT = """\
You are a PulsePoint pre-sales assistant helping respond to RFP questions. \
You will be given retrieved entries from PulsePoint's internal knowledge library.

Rules:
- Synthesize a single, complete answer from the retrieved entries.
- Older entries may have stronger foundational detail — use them as the base.
- Newer entries may contain updated capabilities, stats, or product changes — layer these in.
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
    """Embed query and retrieve top-K matches from Pinecone."""
    vector = embed_query(openai_client, query_text)
    results = index.query(
        vector=vector,
        top_k=TOP_K,
        include_metadata=True,
    )
    return results.matches


def build_context(matches):
    """Format retrieved entries as context for Claude."""
    entries = []
    for i, match in enumerate(matches, 1):
        meta = match.metadata
        answer = meta.get("answer_plain", "")
        tags = meta.get("tags", [])
        if isinstance(tags, list):
            tags = ", ".join(tags)
        entry = (
            f"--- Entry {i} ---\n"
            f"ID: {match.id}\n"
            f"Score: {round(match.score, 4)}\n"
            f"Question: {meta.get('question', '')}\n"
            f"Tags: {tags}\n"
            f"Stack: {meta.get('stack_name', '')}\n"
            f"Last Updated: {meta.get('last_updated_date', 'unknown')}\n"
            f"Answer:\n{answer}\n"
        )
        entries.append(entry)
    return "\n".join(entries)


def synthesize(client, context, user_question):
    """Send retrieved context + question to Claude for synthesis."""
    user_message = (
        f"Retrieved library entries:\n\n{context}\n\n"
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

    # Step 1: Retrieve
    print(f"Searching Pinecone for: {query}\n")
    matches = retrieve(index, openai_client, query)
    print(f"Retrieved {len(matches)} entries.\n")

    # Step 2: Build context
    context = build_context(matches)

    # Step 3: Synthesize with Claude
    print("Synthesizing answer with Claude...\n")
    answer = synthesize(claude, context, query)

    # Print to terminal
    print("=" * 60)
    print("SYNTHESIZED ANSWER")
    print("=" * 60)
    print(answer)
    print("=" * 60)

    # Save to CSV
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = os.path.join(OUTPUT_DIR, f"rag_result_{timestamp}.csv")
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["question", "synthesized_answer", "source_ids", "source_scores"])
        writer.writeheader()
        writer.writerow({
            "question": query,
            "synthesized_answer": answer,
            "source_ids": "; ".join(m.id for m in matches),
            "source_scores": "; ".join(str(round(m.score, 4)) for m in matches),
        })

    print(f"\nResult saved to: {out_path}")


if __name__ == "__main__":
    main()
