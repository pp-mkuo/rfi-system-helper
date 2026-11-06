"""Configuration and constants."""

import os


# -- API Keys (from environment) ----------------------------------------------
PINECONE_API_KEY = os.environ["PINECONE_API_KEY"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

# -- Pinecone -----------------------------------------------------------------
INDEX_NAME = "loopio-library-2"
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIM = 1536
RERANK_MODEL = "bge-reranker-v2-m3"
RETRIEVE_K = 20
RERANK_TOP_N = 5
RERANK_SCORE_FLOOR = 0.01
METADATA_FILTER = {"stack_name": {"$eq": "Client Strategy- Cleaned"}}

# -- LLM Generation -----------------------------------------------------------
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "openai")  # "openai" or "anthropic"
LLM_MODEL = os.environ.get("LLM_MODEL", "gpt-4o")
MAX_TOKENS = 2048

# -- Ingestion ----------------------------------------------------------------
INGEST_BATCH_SIZE = 96

# -- Loopio API (optional, for library refresh) --------------------------------
LOOPIO_CLIENT_ID = os.environ.get("LOOPIO_CLIENT_ID", "")
LOOPIO_CLIENT_SECRET = os.environ.get("LOOPIO_CLIENT_SECRET", "")
LOOPIO_BASE_URL = "https://api.loopio.com"

# -- System Prompt -------------------------------------------------------------
SYSTEM_PROMPT = """\
You are a PulsePoint pre-sales assistant helping respond to RFI questions. \
You will be given retrieved entries from PulsePoint's internal Loopio library.

Rules:
- Synthesize a single, complete answer from the retrieved entries.
- Older entries may have stronger foundational detail -- use them as the base.
- Newer entries may contain updated capabilities, stats, or product changes -- layer these in.
- If an older and newer entry conflict, prefer the newer one.
- Only use information from the provided entries. Do not make up facts.
- Keep the tone professional and suitable for an RFI response.
- If none of the retrieved entries are relevant, respond with exactly: \
"N/A - No relevant information found in library."
- Do NOT include source IDs or citations -- just the answer text.
- Be concise but thorough. Aim for 2-5 sentences unless the question demands more detail.\
"""
