# Loopio RFI Auto-Responder — Specification Document

## 1. Overview

A RAG-powered tool integrated into the PulsePoint BI Fabric platform that automatically answers RFI/RFP questions using PulsePoint's internal Loopio knowledge library. The tool is registered as an ADK (Agent Development Kit) tool in the Fabric backend, allowing the AI agent to call it when users ask RFI/RFP questions through the chat interface.

**Deployment model:**
- **Backend (ADK tool):** `pulsepointinc/bi-services` → `bi-fabric/adk_runtime/tools/loopio_rfp.py`
- **Frontend (UI):** `pulsepointinc/loopio-rfp` → React/Vite app on Fabric (App Engine)

---

## 2. Architecture

```
User asks RFI question in Fabric chat UI
              │
              ▼
┌─────────────────────────────────────────────────┐
│  Fabric Frontend (loopio-rfp)                   │
│  React/Vite SPA on App Engine                   │
│  Calls: POST /api/fabric/adk-runtime/v1/turn    │
└──────────────────────┬──────────────────────────┘
                       │ IAP auth (cookie)
                       ▼
┌─────────────────────────────────────────────────┐
│  Fabric Backend (bi-services/bi-fabric)         │
│  Flask + ADK Runtime (turn_engine.py)           │
│                                                 │
│  Model receives user question                   │
│  Model decides to call: loopio_rfp_search       │
│       │                                         │
│       ▼                                         │
│  ┌──────────────────────────────────────┐       │
│  │  loopio_rfp.py (ADK Tool)           │       │
│  │                                      │       │
│  │  1. Embed query      (OpenAI)        │       │
│  │     text-embedding-3-small, 1536d    │       │
│  │                                      │       │
│  │  2. Vector search    (Pinecone)      │       │
│  │     loopio-library-2, top_k=20      │       │
│  │     filter: Client Strategy-Cleaned  │       │
│  │                                      │       │
│  │  3. Rerank           (Pinecone)      │       │
│  │     bge-reranker-v2-m3, top_n=5     │       │
│  │                                      │       │
│  │  4. Return entries to model          │       │
│  └──────────────────────────────────────┘       │
│                                                 │
│  Model synthesizes answer from entries          │
│  Returns response to frontend                   │
└─────────────────────────────────────────────────┘
```

**Key difference from standalone approach:** The LLM synthesis step is handled by the ADK runtime's model (Gemini or Claude via Vertex), not by a separate API call in the tool. The tool only does retrieval + reranking and returns structured entries. The model sees the entries and writes the answer itself. The synthesis instructions are embedded in the tool's `description` field.

### Pipeline Steps

| Step | Service | Model / Index | Input | Output |
|------|---------|---------------|-------|--------|
| **Embed** | OpenAI API | `text-embedding-3-small` (1536d) | Question text | 1536-dim vector |
| **Retrieve** | Pinecone | `loopio-library-2` (serverless, us-east-1, cosine) | Query vector, top_k=20, metadata filter | Up to 20 candidate matches with metadata |
| **Rerank** | Pinecone Inference | `bge-reranker-v2-m3` | Query + 20 candidate docs | Top 5 reranked results with scores |
| **Synthesize** | ADK Runtime model | Gemini / Claude via Vertex | Tool output (entries) + tool description rules | Professional RFI answer |

---

## 3. Data Layer

### 3.1 Source: Loopio Library Export

- **Origin:** Loopio REST API (`/data/v2/libraryEntries`) via OAuth2 client credentials
- **Export format:** CSV with these fields:
  - `id`, `question`, `answer_plain`, `answer_html`, `stack_name`, `category_name`, `subcategory_name`, `tags`, `status`, `last_updated_date`, `owner_name`, `creator_name`, `attachment_count`, scores, usage counts
- **Relevant stack:** `Client Strategy- Cleaned` (primary filter for RFI retrieval)

### 3.2 Pinecone Vector Store

| Property | Value |
|----------|-------|
| Index name | `loopio-library-2` |
| Cloud | AWS |
| Region | us-east-1 |
| Metric | cosine |
| Dimensions | 1536 |
| Spec | serverless |

**Stored metadata per vector:**
- `stack_name` (string)
- `question` (string)
- `answer_plain` (string)
- `tags` (list of strings)
- `last_updated_date` (string)

### 3.3 Ingestion Pipeline

1. Read Loopio CSV export
2. For each entry, concatenate `question + "\n\n" + answer_plain` as embedding text
3. Embed in batches of 96 using OpenAI `text-embedding-3-small`
4. Upsert to Pinecone with metadata
5. Ingestion is a standalone script (`pinecone_ingest.py`), run manually when the library is updated

---

## 4. ADK Tool Contract

### 4.1 Tool Specification

| Field | Value |
|-------|-------|
| `tool_id` | `fabric.loopio.rfp_search` |
| `genai_name` | `loopio_rfp_search` |
| `display_name` | `Loopio RFP Library Search` |

### 4.2 Input Schema

```json
{
  "type": "OBJECT",
  "properties": {
    "query": {
      "type": "STRING",
      "description": "The RFI/RFP question to search. Max 2000 chars."
    },
    "top_n": {
      "type": "INTEGER",
      "description": "Max entries to return (default 5, range 1-10)."
    }
  },
  "required": ["query"]
}
```

### 4.3 Output Shape

**Success:**
```json
{
  "query": "Does your platform support HIPAA-compliant data handling?",
  "count": 5,
  "entries": [
    {
      "rerank_score": 0.8923,
      "vector_score": 0.7841,
      "question": "Is PulsePoint HIPAA compliant?",
      "answer": "PulsePoint's platform is built with compliance...",
      "stack_name": "Client Strategy- Cleaned",
      "tags": ["compliance", "HIPAA"],
      "last_updated": "2026-03-15",
      "entry_id": "12345"
    }
  ]
}
```

**No results:**
```json
{
  "query": "...",
  "count": 0,
  "entries": [],
  "message": "No relevant entries found after reranking."
}
```

**Error:**
```json
{
  "error": true,
  "errorCode": "loopio_tool_disabled",
  "errorDesc": "Loopio RFP search is not configured: set PINECONE_API_KEY and OPENAI_API_KEY."
}
```

### 4.4 Error Codes

| Code | Meaning | Retry? |
|------|---------|--------|
| `loopio_tool_disabled` | Env vars not set | No |
| `loopio_query_invalid` | Bad query input | Fix args, retry |
| `loopio_top_n_invalid` | Bad top_n input | Fix args, retry |
| `loopio_retrieve_error` | Pinecone retrieval failed | Retry once |
| `loopio_rerank_error` | Reranking failed | Retry once |

---

## 5. LLM Synthesis (via Tool Description)

The tool's `description` field contains the synthesis instructions that the ADK runtime model follows when processing the tool's output:

- Synthesize a single, complete answer from the returned entries
- Older entries may have stronger foundational detail — use them as the base
- Newer entries may contain updated capabilities or stats — layer these in
- If older and newer entries conflict, prefer the newer one
- Only use information from the returned entries — do not make up facts
- If no entries are returned (count=0), tell the user clearly

The ADK runtime model (Gemini or Claude via Vertex) handles the final synthesis, governed by the app's `systemInstruction` configured in the Fabric admin UI.

---

## 6. Operational Thresholds

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| `RETRIEVE_K` | 20 | Cast a wide net for reranking |
| `RERANK_TOP_N` | 5 | Narrow to most relevant context |
| Rerank score floor | 0.01 | Below this, return empty |
| Rerank 429 retry | 5 attempts, 15s * attempt backoff | Handle rate limit bursts |
| Max query length | 2000 chars | Prevent oversized embeddings |
| Embedding batch size | 96 | Ingestion batching |

---

## 7. Environment Variables (bi-fabric)

These must be added to the `bi-fabric` App Engine service environment:

| Variable | Required | Description |
|----------|----------|-------------|
| `PINECONE_API_KEY` | Yes | Pinecone API key for `loopio-library-2` |
| `OPENAI_API_KEY` | Yes | OpenAI API key for embeddings |

**Already configured in bi-fabric (no changes needed):**
- `BI_FABRIC_SVC_JSON` — GCP service account for IAP
- `FABRIC_IAP_CLIENT_ID` — IAP OAuth client ID

---

## 8. Integration Steps

### 8.1 Backend (bi-services/bi-fabric)

1. **Add tool module:** Copy `loopio_rfp.py` to `bi-fabric/adk_runtime/tools/`
2. **Register in catalog:** Edit `bi-fabric/adk_runtime/tools/__init__.py`:
   ```python
   from adk_runtime.tools import loopio_rfp
   # In TOOL_SPECS list:
   *loopio_rfp.SPECS,
   ```
3. **Add dependencies:** Add to `bi-fabric/requirements.txt`:
   ```
   pinecone>=5.0.0
   openai>=1.40.0
   ```
4. **Add env vars:** Add `PINECONE_API_KEY` and `OPENAI_API_KEY` to bi-fabric's App Engine config
5. **Entitle the tool:** In Fabric admin UI, add `fabric.loopio.rfp_search` to the loopio-rfp app's `entitledToolIds`

### 8.2 Frontend (loopio-rfp)

1. Build a chat interface using the `AdkChatBox` component pattern (already in the Fabric template)
2. Configure the app's ADK runtime in Fabric admin:
   - `enabled: true`
   - `systemInstruction`: PulsePoint pre-sales assistant prompt
   - `entitledToolIds`: `["fabric.loopio.rfp_search"]`
3. The chat UI calls `POST /api/fabric/adk-runtime/v1/turn` — the ADK runtime handles tool invocation and response synthesis automatically

### 8.3 App Registration

1. Register `loopio-rfp` in Fabric admin (or via scaffold API)
2. Configure ADK runtime settings for the app
3. Assign users who should have access

---

## 9. File Structure

### Backend (PR to bi-services)
```
bi-fabric/
  adk_runtime/
    tools/
      loopio_rfp.py          # NEW — ADK tool (embed + retrieve + rerank)
      __init__.py             # EDIT — add loopio_rfp to TOOL_SPECS
  requirements.txt            # EDIT — add pinecone, openai
```

### Frontend (loopio-rfp repo)
```
loopio-rfp/
  src/
    App.tsx                   # Router setup
    pages/
      Index.tsx               # Chat UI for RFI questions
    components/
      ...                     # Chat components
  SPEC.md                     # This document
  package.json
  .env
```

### Standalone scripts (this folder, for manual use)
```
Loopio -> Claude 2/
  pinecone_ingest.py          # One-time ingestion of Loopio CSV into Pinecone
  loopio_export.py            # Export from Loopio API to CSV
  batch_rfi.py                # Batch XLSX processing (standalone, not on Fabric)
```

---

## 10. Existing n8n Workflow Reference

The current production workflow on `n8n-labs.pulsepoint.com:5678` implements the same pipeline:

1. **Webhook** — POST trigger
2. **Pinecone Vector Store** — top_k=20, filter `stack_name = "Client Strategy- Cleaned"`, OpenAI embeddings (1536d)
3. **Pinecone Rerank** — `bge-reranker-v2-m3`, top_n=5
4. **Synthesize with GPT-4o** — System prompt + formatted context
5. **Respond to Webhook** — Returns answer + sources

The ADK tool replaces steps 1-3 (retrieval + reranking). Step 4 (synthesis) is handled by the ADK runtime model instead of a direct GPT-4o call.

---

## 11. Dependencies (new additions to bi-fabric)

| Package | Version | Purpose |
|---------|---------|---------|
| `pinecone` | >=5.0 | Vector store retrieval + hosted reranking |
| `openai` | >=1.40 | Embedding generation (`text-embedding-3-small`) |

All other dependencies (Flask, google-genai, etc.) are already in bi-fabric's requirements.

---

## 12. Next Steps

- [ ] Get access to `pulsepointinc/bi-services` repo (PR permissions)
- [ ] Add `PINECONE_API_KEY` and `OPENAI_API_KEY` to bi-fabric's App Engine env
- [ ] Submit PR: `loopio_rfp.py` + `__init__.py` edit + `requirements.txt` additions
- [ ] Register `loopio-rfp` app in Fabric admin with ADK runtime enabled
- [ ] Configure `systemInstruction` for the app (pre-sales assistant prompt)
- [ ] Entitle `fabric.loopio.rfp_search` tool to the app
- [ ] Build chat UI in the `loopio-rfp` frontend repo
- [ ] Test end-to-end: user question → ADK turn → tool call → synthesis → response
- [ ] Validate against Dentsu RFI questions for answer quality parity with n8n
