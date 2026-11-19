---
provenance: agent-generated
last-verified: never
---

# Memory store vs Pinecone for the RFI library: review for Maggie (AF-129)

This is a point-in-time result from one run of each eval on 2026-11-19. The answer keys are agent-built and nobody has checked them, so every score is provisional. Accuracy and routing calls are yours.

## The question

Ezra suggested keeping the library in a Claude Managed Agents **memory store** instead of Pinecone. A memory store is a set of read-only text files at `/mnt/memory/`, and the agent searches it with grep. That means keyword matching: no meaning-based search and no scores. We tested it side by side, and **rfi-agent was not changed.**

- **Store:** `memstore_01MqRVN7npVy4FFPnuWZmVru`, holding the same 2,297 records as the index, one file per record, one folder per stack. Built by `pipeline/build_memory_store.py`.
- **Copy agent:** `rfi-agent-memory` (`agent_01Eu17bC4gDYXD1h4eHT7Nu8`). It's live rfi-agent v3 with only the search steps swapped (`agents/rfi-agent-memory/`). It needs no vault, no Pinecone and no OpenAI.

## Results

| | Pinecone (rfi-agent v3) | Memory store |
|---|---|---|
| Triage, AF-50 set (29 questions) | 28/29 | 29/29 |
| Routing (amber + red) | 15/15 | 15/15 |
| Red safety | 8/8 | 8/8 |
| Faithfulness | 13/14 | 15/16 |
| Retrieval, right record first (first 30 AF-49 paraphrases) | 25/30 | 25/30 |
| Retrieval, right record in top 3 | 28/30 | 27/30 |
| Claude cost per question | about $0.036 | about $0.062 |

The Pinecone baselines are AF-50 and AF-49, both run 2026-11-12. Files: `evals/accuracy/results/2026-11-19-cmi2025-slice-memory-v1.json` and `evals/retrieval/results/2026-11-19-memory-v1-paraphrase-first30.json`.

## What we need from you

1. **Three retrieval misses that Pinecone got right.** Is the record the memory agent picked an acceptable answer?
   - `af49-037`, report breakouts: picked `rfi2026-cmi2025-016`
   - `af49-038`, source of physician targeting data: picked `rfi2026-cmi0826-037`
   - `af49-039`, how fast an audience goes live: picked `loopio-13130670`

   The answer key was widened by reviewing Pinecone's misses, so it may favour Pinecone.
2. **`CMI-049`, bid shading.** The memory agent called it green. Pinecone called it amber and routed it to Becky Hallam. The library has conflicting records on this question. Which call is right?
3. **`CMI-055`.** The draft claims a "patented MeSH-mapped contextual engine", and the judge found no record that says so. Is it true?
4. **The answer key.** Please check `evals/accuracy/questions.json`, starting with `CMI-057` and `CMI-049`.

## Cost and scale

Prices were checked 2026-11-19 on pinecone.io/pricing and OpenAI's pricing page.

- **Pinecone per question is close to $0:** about $0.000004 for the search and $0.000001 for the OpenAI embedding. The real cost is the plan: Standard has a $50/month minimum and Builder is $20. The index is on GCP, so it's on a paid plan; which one is not checked.
- **The memory store has no storage charge listed,** but it costs about $0.026 more Claude per question. It's cheaper overall below about 1,900 questions a month, and only if the Pinecone plan exists just for this library.
- **Upkeep Pinecone needs and the memory store doesn't:**
  - two vendors' keys in the vault, plus the allowed hosts
  - a ReadWrite key for every load
  - an OpenAI account that can run out of credit
  - two outside services to clear in a legal or security review
- **Scale:**
  - The memory store caps at 10,000 files per store, and it holds 2,297 now.
  - Keyword search reads more files as the library grows, and it gets worse at matching reworded questions.
  - Pinecone stays at minimum query cost up to roughly 40,000 records, and its search quality holds as the library grows.
  - Both get worse as duplicates and conflicts grow, so library cleanup (AF-117) matters either way.

## Still open

- **Dentsu 14 (AF-120).** These are the real retrieval test. Run both evals on both agents when the questions arrive.
- **Run-to-run variance.** Each question ran once, and AF-50 showed overclaims vary between runs.
- **The other 44 AF-49 paraphrases and 16 verbatim items.** Not run on the memory store yet, to stay inside the budget.
- **Which Pinecone plan the project is on.**

## Rerun

```
unset ANTHROPIC_API_KEY
python3 evals/accuracy/run_accuracy_eval.py --agent-id agent_01Eu17bC4gDYXD1h4eHT7Nu8 --memory-store memstore_01MqRVN7npVy4FFPnuWZmVru [--set evals/accuracy/dentsu14.json]
python3 evals/retrieval/run_memory_retrieval.py [--origin paraphrase] [--limit N]
```
