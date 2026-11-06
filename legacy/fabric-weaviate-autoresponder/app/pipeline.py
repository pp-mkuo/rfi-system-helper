"""Core RAG pipeline: embed, retrieve, rerank, synthesize."""

from __future__ import annotations

import time
from dataclasses import dataclass

import anthropic
from openai import OpenAI
from pinecone import Pinecone

from . import config


@dataclass
class RerankedMatch:
    id: str
    vector_score: float
    rerank_score: float
    question: str
    answer: str
    stack_name: str
    tags: list[str]
    last_updated: str


# -- Singleton clients (initialized once) -------------------------------------

_pc: Pinecone | None = None
_index = None
_openai: OpenAI | None = None
_anthropic: anthropic.Anthropic | None = None


def _get_pinecone():
    global _pc, _index
    if _pc is None:
        _pc = Pinecone(api_key=config.PINECONE_API_KEY)
        _index = _pc.Index(config.INDEX_NAME)
    return _pc, _index


def _get_openai():
    global _openai
    if _openai is None:
        _openai = OpenAI(api_key=config.OPENAI_API_KEY)
    return _openai


def _get_anthropic():
    global _anthropic
    if _anthropic is None:
        _anthropic = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    return _anthropic


# -- Pipeline steps -----------------------------------------------------------


def embed_query(text: str) -> list[float]:
    """Generate embedding for a single query via OpenAI."""
    client = _get_openai()
    response = client.embeddings.create(model=config.EMBEDDING_MODEL, input=[text])
    return response.data[0].embedding


def retrieve(query_text: str) -> list:
    """Embed query and retrieve top-K candidates from Pinecone."""
    _, index = _get_pinecone()
    vector = embed_query(query_text)
    results = index.query(
        vector=vector,
        top_k=config.RETRIEVE_K,
        include_metadata=True,
        filter=config.METADATA_FILTER,
    )
    return results.matches


def rerank(query_text: str, matches: list) -> list[RerankedMatch]:
    """Rerank retrieved candidates using Pinecone's hosted reranker."""
    if not matches:
        return []

    pc, _ = _get_pinecone()
    documents = []
    for match in matches:
        question = match.metadata.get("question", "")
        answer = match.metadata.get("answer_plain", "")
        documents.append(f"{question}\n{answer}")

    # Retry with backoff on rate limits
    for attempt in range(5):
        try:
            reranked = pc.inference.rerank(
                model=config.RERANK_MODEL,
                query=query_text,
                documents=documents,
                top_n=config.RERANK_TOP_N,
                return_documents=False,
                parameters={"truncate": "END"},
            )
            break
        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                wait = 15 * (attempt + 1)
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
        results.append(
            RerankedMatch(
                id=m.id,
                vector_score=round(m.score, 4),
                rerank_score=round(item.score, 4),
                question=meta.get("question", ""),
                answer=meta.get("answer_plain", ""),
                stack_name=meta.get("stack_name", ""),
                tags=tags,
                last_updated=meta.get("last_updated_date", "unknown"),
            )
        )
    return results


def build_context(entries: list[RerankedMatch]) -> str:
    """Format reranked entries as context for the LLM."""
    parts = []
    for i, entry in enumerate(entries, 1):
        tags = ", ".join(entry.tags) if entry.tags else ""
        part = (
            f"--- Entry {i} ---\n"
            f"ID: {entry.id}\n"
            f"Rerank Score: {entry.rerank_score}\n"
            f"Question: {entry.question}\n"
            f"Tags: {tags}\n"
            f"Stack: {entry.stack_name}\n"
            f"Last Updated: {entry.last_updated}\n"
            f"Answer:\n{entry.answer}\n"
        )
        parts.append(part)
    return "\n".join(parts)


def synthesize(context: str, user_question: str) -> tuple[str, str]:
    """Send reranked context + question to LLM. Returns (answer, model_used)."""
    user_message = (
        f"Retrieved and reranked library entries:\n\n{context}\n\n"
        f"---\n\n"
        f"RFI Question: {user_question}\n\n"
        f"Please synthesize a complete answer using the entries above."
    )

    if config.LLM_PROVIDER == "anthropic" and config.ANTHROPIC_API_KEY:
        client = _get_anthropic()
        model = config.LLM_MODEL if config.LLM_MODEL != "gpt-4o" else "claude-sonnet-4-20250514"
        response = client.messages.create(
            model=model,
            max_tokens=config.MAX_TOKENS,
            system=config.SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}],
        )
        return response.content[0].text, model
    else:
        client = _get_openai()
        model = config.LLM_MODEL
        response = client.chat.completions.create(
            model=model,
            max_tokens=config.MAX_TOKENS,
            messages=[
                {"role": "system", "content": config.SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
        )
        return response.choices[0].message.content, model


def answer_question(question: str) -> tuple[str, list[RerankedMatch], str]:
    """Full pipeline: retrieve -> rerank -> synthesize.

    Returns (answer_text, reranked_matches, model_used).
    """
    matches = retrieve(question)
    reranked = rerank(question, matches)

    if not reranked or reranked[0].rerank_score < config.RERANK_SCORE_FLOOR:
        return "N/A - No relevant information found in library.", reranked, config.LLM_MODEL

    context = build_context(reranked)
    answer, model = synthesize(context, question)
    return answer, reranked, model
