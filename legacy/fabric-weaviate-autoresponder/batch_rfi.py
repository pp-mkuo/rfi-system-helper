#!/usr/bin/env python3
"""Batch RFI processor: read Dentsu XLSX, RAG+rerank+synthesize each question, write answers back."""

import json
import os
import sys
import time
from copy import copy
from datetime import datetime

import anthropic
import openpyxl
from openpyxl.utils import get_column_letter
from pinecone import Pinecone
from openai import OpenAI

# -- Config ------------------------------------------------------------------
PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY", "REDACTED-set-PINECONE_API_KEY-env")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
INDEX_NAME = "loopio-library-2"
EMBEDDING_MODEL = "text-embedding-3-small"
RERANK_MODEL = "bge-reranker-v2-m3"
RETRIEVE_K = 20
RERANK_TOP_N = 5
GENERATION_MODEL = "claude-sonnet-5"

INPUT_PATH = os.path.expanduser(
    "~/Documents/Dentsu US 26-27 Integrated RFI_Template (2).xlsx"
)
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
CHECKPOINT_PATH = os.path.join(OUTPUT_DIR, "batch_checkpoint.json")

SKIP_SHEETS = ["TERMS OF RFI - PLEASE READ", "Instructions For Completion"]

# Columns in most sheets: A=Category, B=Q#, C=Question, D=Partner Response
Q_NUM_COL = 2   # B
QUESTION_COL = 3  # C
RESPONSE_COL = 4  # D

SYSTEM_PROMPT = """\
You are a PulsePoint pre-sales assistant helping respond to RFI questions from Dentsu. \
You will be given retrieved entries from PulsePoint's internal Loopio knowledge library.

Rules:
- Synthesize a single, complete answer from the retrieved entries.
- Older entries may have stronger foundational detail -- use them as the base.
- Newer entries may contain updated capabilities, stats, or product changes -- layer these in.
- If an older and newer entry conflict, prefer the newer one.
- Only use information from the provided entries. Do not make up facts.
- Keep the tone professional and suitable for an RFI response.
- If none of the retrieved entries are relevant, respond with exactly: "N/A - No relevant information found in library."
- Do NOT include source IDs or citations -- just the answer text.
- Be concise but thorough. Aim for 2-5 sentences unless the question demands more detail.\
"""

for key_name, key_val in [
    ("PINECONE_API_KEY", PINECONE_API_KEY),
    ("OPENAI_API_KEY", OPENAI_API_KEY),
    ("ANTHROPIC_API_KEY", ANTHROPIC_API_KEY),
]:
    if not key_val:
        sys.exit(f"Error: Set {key_name} environment variable.")


# -- Core pipeline (from rag_rerank_search.py) --------------------------------

def embed_query(client, text):
    response = client.embeddings.create(model=EMBEDDING_MODEL, input=[text])
    return response.data[0].embedding


def retrieve(index, openai_client, query_text):
    vector = embed_query(openai_client, query_text)
    results = index.query(
        vector=vector,
        top_k=RETRIEVE_K,
        include_metadata=True,
    )
    return results.matches


def rerank(pc, query_text, matches):
    if not matches:
        return []
    documents = []
    for match in matches:
        question = match.metadata.get("question", "")
        answer = match.metadata.get("answer_plain", "")
        documents.append(f"{question}\n{answer}")

    for attempt in range(5):
        try:
            reranked = pc.inference.rerank(
                model=RERANK_MODEL,
                query=query_text,
                documents=documents,
                top_n=RERANK_TOP_N,
                return_documents=False,
                parameters={"truncate": "END"},
            )
            break
        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                wait = 15 * (attempt + 1)
                print(f"    [rerank 429] waiting {wait}s...")
                time.sleep(wait)
            else:
                raise
    else:
        return []

    results = []
    for item in reranked.data:
        original_match = matches[item.index]
        results.append((original_match, item.score))
    return results


def build_context(reranked_results):
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
            f"Rerank Score: {round(rerank_score, 4)}\n"
            f"Question: {meta.get('question', '')}\n"
            f"Tags: {tags}\n"
            f"Stack: {meta.get('stack_name', '')}\n"
            f"Last Updated: {meta.get('last_updated_date', 'unknown')}\n"
            f"Answer:\n{answer}\n"
        )
        entries.append(entry)
    return "\n".join(entries)


def synthesize(anthropic_client, context, user_question):
    user_message = (
        f"Retrieved and reranked library entries:\n\n{context}\n\n"
        f"---\n\n"
        f"RFI Question: {user_question}\n\n"
        f"Please synthesize a complete answer using the entries above."
    )
    response = anthropic_client.messages.create(
        model=GENERATION_MODEL,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[
            {"role": "user", "content": user_message},
        ],
    )
    return response.content[0].text


def process_question(question_text, pc, index, openai_client, anthropic_client):
    """Full pipeline for one question: retrieve -> rerank -> synthesize."""
    matches = retrieve(index, openai_client, question_text)
    reranked = rerank(pc, question_text, matches)

    if not reranked:
        return "N/A - No relevant information found in library."

    # Check if top rerank score is very low (likely irrelevant)
    top_score = reranked[0][1]
    if top_score < 0.01:
        return "N/A - No relevant information found in library."

    context = build_context(reranked)
    answer = synthesize(anthropic_client, context, question_text)
    return answer


# -- Checkpoint ---------------------------------------------------------------

def load_checkpoint():
    if os.path.exists(CHECKPOINT_PATH):
        with open(CHECKPOINT_PATH, "r") as f:
            return json.load(f)
    return {}


def save_checkpoint(data):
    with open(CHECKPOINT_PATH, "w") as f:
        json.dump(data, f, indent=2)


# -- Extract questions from XLSX ----------------------------------------------

def extract_questions(wb):
    """Return list of (sheet_name, row_number, q_id, question_text)."""
    questions = []
    for sheet_name in wb.sheetnames:
        if sheet_name in SKIP_SHEETS:
            continue
        ws = wb[sheet_name]
        for row_idx in range(1, ws.max_row + 1):
            q_num = ws.cell(row=row_idx, column=Q_NUM_COL).value
            q_text = ws.cell(row=row_idx, column=QUESTION_COL).value
            if q_num and q_text and str(q_num).strip() and str(q_text).strip():
                # Skip header rows
                q_num_str = str(q_num).strip()
                if q_num_str.lower() in ("q#", "question", "q1"):
                    # Q1 could be a header in Gaming tab (column is "Q1" not "Q#")
                    # but also a real question ID -- check if q_text looks like a header
                    if q_text.strip().lower() == "question":
                        continue
                questions.append((sheet_name, row_idx, q_num_str, str(q_text).strip()))
    return questions


# -- Main ---------------------------------------------------------------------

def main():
    print("Loading Dentsu RFI workbook...")
    wb = openpyxl.load_workbook(INPUT_PATH)

    questions = extract_questions(wb)
    print(f"Found {len(questions)} questions across {len(wb.sheetnames) - len(SKIP_SHEETS)} tabs.\n")

    # Load checkpoint
    checkpoint = load_checkpoint()
    already_done = set(checkpoint.keys())
    remaining = [(s, r, q, t) for s, r, q, t in questions if f"{s}|{q}" not in already_done]
    print(f"Checkpoint: {len(already_done)} already answered, {len(remaining)} remaining.\n")

    if not remaining:
        print("All questions already processed. Writing output...")
    else:
        # Init clients
        pc = Pinecone(api_key=PINECONE_API_KEY)
        openai_client = OpenAI(api_key=OPENAI_API_KEY)
        anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        index = pc.Index(INDEX_NAME)

        for i, (sheet_name, row_idx, q_id, q_text) in enumerate(remaining, 1):
            key = f"{sheet_name}|{q_id}"
            print(f"[{i}/{len(remaining)}] {sheet_name} / {q_id}: {q_text[:70]}...")

            try:
                answer = process_question(q_text, pc, index, openai_client, anthropic_client)
                checkpoint[key] = {
                    "sheet": sheet_name,
                    "row": row_idx,
                    "q_id": q_id,
                    "question": q_text,
                    "answer": answer,
                }
                save_checkpoint(checkpoint)
                print(f"    -> {'N/A' if answer.startswith('N/A') else answer[:80]}...")
            except Exception as e:
                print(f"    !! ERROR: {e}")
                # Save progress and continue
                save_checkpoint(checkpoint)

            # Rate limiting: stay under Pinecone rerank limit (60 req/min)
            time.sleep(2.0)

    # -- Write output XLSX ----------------------------------------------------
    print("\nWriting answers to output file...")

    for sheet_name, row_idx, q_id, q_text in questions:
        key = f"{sheet_name}|{q_id}"
        if key in checkpoint:
            ws = wb[sheet_name]
            ws.cell(row=row_idx, column=RESPONSE_COL).value = checkpoint[key]["answer"]

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = os.path.join(
        OUTPUT_DIR, "Results", f"Dentsu_RFI_Answered_{timestamp}.xlsx"
    )
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    wb.save(out_path)
    print(f"\nDone! Output saved to:\n  {out_path}")
    print(f"Checkpoint file: {CHECKPOINT_PATH}")
    print(f"  (Delete checkpoint to re-run from scratch)")


if __name__ == "__main__":
    main()
