"""`fabric.loopio.rfp_search` — RAG search over PulsePoint's Loopio RFI/RFP library.

Retrieves relevant entries from the Loopio library in Pinecone (OpenAI
embeddings), reranks with Pinecone's hosted reranker, and returns the top
results for the model to synthesize an answer.

Pipeline: embed query → vector search (top-20) → rerank (top-5) → return context

Env vars
--------
``PINECONE_API_KEY``   — Pinecone API key with access to ``loopio-library-2``.
``OPENAI_API_KEY``     — OpenAI API key for ``text-embedding-3-small`` embeddings.

Index details
-------------
- Index: ``loopio-library-2`` (serverless, AWS us-east-1, cosine, 1536d)
- Embedding model: ``text-embedding-3-small`` (1536 dimensions)
- Rerank model: ``bge-reranker-v2-m3`` (Pinecone Inference)
- Metadata filter: ``stack_name = "Client Strategy- Cleaned"``
"""

from __future__ import annotations

import os
import time
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING

from google.genai import types as genai_types

from adk_runtime.tools._spec import ToolSpec

if TYPE_CHECKING:
    from adk_runtime.tool_registry import FabricToolContext

# -- Config -------------------------------------------------------------------

_PINECONE_API_KEY_ENV = "PINECONE_API_KEY"
_OPENAI_API_KEY_ENV = "OPENAI_API_KEY"
_INDEX_NAME = "loopio-library-2"
_EMBEDDING_MODEL = "text-embedding-3-small"
_RERANK_MODEL = "bge-reranker-v2-m3"
_RETRIEVE_K = 20
_RERANK_TOP_N = 5
_RERANK_SCORE_FLOOR = 0.01
_METADATA_FILTER = {"stack_name": {"$eq": "Client Strategy- Cleaned"}}
_MAX_QUERY_CHARS = 2000
_RERANK_RETRY_ATTEMPTS = 5
_RERANK_RETRY_BASE_WAIT = 15  # seconds

# -- Lazy-init clients --------------------------------------------------------

_pc = None
_index = None
_openai_client = None


def _get_pinecone():
    global _pc, _index
    if _pc is None:
        from pinecone import Pinecone

        api_key = os.environ.get(_PINECONE_API_KEY_ENV, "").strip()
        if not api_key:
            return None, None
        _pc = Pinecone(api_key=api_key)
        _index = _pc.Index(_INDEX_NAME)
    return _pc, _index


def _get_openai():
    global _openai_client
    if _openai_client is None:
        from openai import OpenAI

        api_key = os.environ.get(_OPENAI_API_KEY_ENV, "").strip()
        if not api_key:
            return None
        _openai_client = OpenAI(api_key=api_key)
    return _openai_client


def _is_configured() -> bool:
    return bool(
        os.environ.get(_PINECONE_API_KEY_ENV, "").strip()
        and os.environ.get(_OPENAI_API_KEY_ENV, "").strip()
    )


# -- Error helper -------------------------------------------------------------


def _err(code: str, desc: str) -> Dict[str, Any]:
    return {"error": True, "errorCode": code, "errorDesc": desc}


# -- Pipeline steps -----------------------------------------------------------


def _embed_query(query: str) -> Optional[List[float]]:
    client = _get_openai()
    if client is None:
        return None
    response = client.embeddings.create(model=_EMBEDDING_MODEL, input=[query])
    return response.data[0].embedding


def _retrieve(query: str) -> Optional[list]:
    _, index = _get_pinecone()
    if index is None:
        return None
    vector = _embed_query(query)
    if vector is None:
        return None
    results = index.query(
        vector=vector,
        top_k=_RETRIEVE_K,
        include_metadata=True,
        filter=_METADATA_FILTER,
    )
    return results.matches


def _rerank(query: str, matches: list) -> List[Dict[str, Any]]:
    if not matches:
        return []

    pc, _ = _get_pinecone()
    if pc is None:
        return []

    documents = []
    for match in matches:
        question = match.metadata.get("question", "")
        answer = match.metadata.get("answer_plain", "")
        documents.append(f"{question}\n{answer}")

    # Retry with backoff on rate limits
    for attempt in range(_RERANK_RETRY_ATTEMPTS):
        try:
            reranked = pc.inference.rerank(
                model=_RERANK_MODEL,
                query=query,
                documents=documents,
                top_n=_RERANK_TOP_N,
                return_documents=False,
                parameters={"truncate": "END"},
            )
            break
        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                wait = _RERANK_RETRY_BASE_WAIT * (attempt + 1)
                time.sleep(wait)
            else:
                raise
    else:
        return []

    results = []
    for item in reranked.data:
        m = matches[item.index]
        meta = m.metadata
        tags = meta.get("tags", [])
        if isinstance(tags, str):
            tags = [t.strip() for t in tags.split(";") if t.strip()]
        results.append({
            "rerank_score": round(item.score, 4),
            "vector_score": round(m.score, 4),
            "question": meta.get("question", ""),
            "answer": meta.get("answer_plain", ""),
            "stack_name": meta.get("stack_name", ""),
            "tags": tags,
            "last_updated": meta.get("last_updated_date", "unknown"),
            "entry_id": m.id,
        })
    return results


# -- Handler ------------------------------------------------------------------


def _loopio_rfp_search_handler(
    args: Dict[str, Any], context: "FabricToolContext"
) -> Dict[str, Any]:
    if not _is_configured():
        return _err(
            "loopio_tool_disabled",
            f"Loopio RFP search is not configured: set {_PINECONE_API_KEY_ENV} "
            f"and {_OPENAI_API_KEY_ENV} environment variables.",
        )

    # Validate query
    raw_query = args.get("query")
    if not isinstance(raw_query, str):
        return _err("loopio_query_invalid", "query is required and must be a string")
    query = raw_query.strip()
    if not query:
        return _err("loopio_query_invalid", "query must be non-empty after trim")
    if len(query) > _MAX_QUERY_CHARS:
        return _err(
            "loopio_query_invalid",
            f"query exceeds {_MAX_QUERY_CHARS} characters",
        )

    # Validate top_n
    top_n = args.get("top_n")
    if top_n is not None:
        if not isinstance(top_n, int) or isinstance(top_n, bool):
            return _err("loopio_top_n_invalid", "top_n must be an integer or omitted")
        if top_n < 1 or top_n > 10:
            return _err("loopio_top_n_invalid", "top_n must be between 1 and 10")

    # Step 1: Retrieve candidates from Pinecone
    try:
        matches = _retrieve(query)
    except Exception as e:
        return _err("loopio_retrieve_error", f"Pinecone retrieval failed: {type(e).__name__}")

    if matches is None:
        return _err("loopio_tool_disabled", "Failed to initialize Pinecone or OpenAI clients")
    if not matches:
        return {
            "query": query,
            "entries": [],
            "count": 0,
            "message": "No matching entries found in the Loopio library.",
        }

    # Step 2: Rerank
    try:
        reranked = _rerank(query, matches)
    except Exception as e:
        return _err("loopio_rerank_error", f"Reranking failed: {type(e).__name__}")

    if not reranked or reranked[0]["rerank_score"] < _RERANK_SCORE_FLOOR:
        return {
            "query": query,
            "entries": [],
            "count": 0,
            "message": "No relevant entries found after reranking.",
        }

    # Apply top_n override if provided
    if top_n is not None:
        reranked = reranked[:top_n]

    return {
        "query": query,
        "entries": reranked,
        "count": len(reranked),
    }


# -- Tool Spec ----------------------------------------------------------------

_TOOL_DESCRIPTION = (
    "Search PulsePoint's internal Loopio RFI/RFP knowledge library. Returns the "
    "most relevant pre-approved answers from the library, reranked for precision.\n"
    "\n"
    "Use this tool when the user asks an RFI or RFP question about PulsePoint's "
    "capabilities, products, compliance, data, partnerships, or any topic that "
    "would appear in a vendor questionnaire.\n"
    "\n"
    "Pipeline: embeds the query → retrieves top-20 candidates from Pinecone → "
    "reranks to top-5 using a cross-encoder → returns structured entries.\n"
    "\n"
    "Hard rules:\n"
    "- Pass only `query` and optional `top_n`.\n"
    "- Each returned entry has: `question`, `answer`, `rerank_score`, "
    "`vector_score`, `tags`, `stack_name`, `last_updated`, `entry_id`.\n"
    "- Synthesize a single professional answer from the returned entries.\n"
    "- Older entries may have stronger foundational detail — use them as the base.\n"
    "- Newer entries may contain updated capabilities or stats — layer these in.\n"
    "- If older and newer entries conflict, prefer the newer one.\n"
    "- Only use information from the returned entries. Do not make up facts.\n"
    "- If no entries are returned (count=0), tell the user clearly.\n"
    "\n"
    "Error recovery:\n"
    "- `loopio_tool_disabled` — env vars not set; tell the user, do not retry.\n"
    "- `loopio_query_invalid` / `loopio_top_n_invalid` — fix arguments and retry.\n"
    "- `loopio_retrieve_error` / `loopio_rerank_error` — upstream failure; retry "
    "once or answer without library grounding.\n"
)

_QUERY_DESCRIPTION = (
    "The RFI/RFP question or natural-language query to search the Loopio library. "
    "Non-empty after trim; max 2000 characters."
)

_TOP_N_DESCRIPTION = (
    "Maximum number of reranked entries to return (default 5). Integer from 1 to 10. "
    "Use 3-5 for focused answers; raise toward 10 for broad coverage."
)


SPECS: List[ToolSpec] = [
    ToolSpec(
        tool_id="fabric.loopio.rfp_search",
        genai_name="loopio_rfp_search",
        display_name="Loopio RFP Library Search",
        description=_TOOL_DESCRIPTION,
        schema=genai_types.Schema(
            type="OBJECT",
            description="Arguments for `fabric.loopio.rfp_search`.",
            properties={
                "query": genai_types.Schema(
                    type="STRING",
                    description=_QUERY_DESCRIPTION,
                ),
                "top_n": genai_types.Schema(
                    type="INTEGER",
                    description=_TOP_N_DESCRIPTION,
                ),
            },
            required=["query"],
        ),
        handler=_loopio_rfp_search_handler,
    ),
]
