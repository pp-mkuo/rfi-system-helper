#!/usr/bin/env python3
"""Search the document index (text in, text out — Pinecone embeds the query).

Same output shape and prefer-newest dedupe as query.py, minus the OpenAI call.

  export PINECONE_API_KEY=...
  python3 query_documents.py "your question" [topK] [--raw] [--stack NAME] [--index NAME]
  python3 query_documents.py --eval eval.json     # top-1 hit rate; see EVAL FORMAT

EVAL FORMAT: a JSON list of {"question": "...", "expected": "<_id or exact library question>"}.
The Dentsu 14-question set is not checked in; ask Maggie for it.
"""
import json, os, sys, urllib.request

API = "https://api.pinecone.io"
VERSION = "2026-07"
NAMESPACE = "__default__"
FIELDS = ["question", "answer_plain", "stack_name", "tags", "last_updated_date", "source_doc", "source",
          "legal_approved", "cleaned"]
CURATED = ("Client Strategy- Cleaned", "RFI 2026")
_host = {}


def call(url, body=None):
    req = urllib.request.Request(url, data=json.dumps(body).encode() if body is not None else None, headers={
        "Content-Type": "application/json", "Api-Key": os.environ["PINECONE_API_KEY"],
        "X-Pinecone-API-Version": VERSION})
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.load(r)


def host(index):
    if index not in _host:
        _host[index] = "https://" + call(f"{API}/indexes/{index}")["host"]
    return _host[index]


def search(index, q, top_k, stack=None):
    body = {"top_k": top_k, "include_fields": FIELDS,
            "score_by": [{"type": "embed", "fields": ["embed_text"], "query": q}]}
    if stack:
        body["filter"] = {"stack_name": {"$eq": stack}}
    return call(f"{host(index)}/namespaces/{NAMESPACE}/documents/search", body).get("matches", [])


def norm(s):
    return " ".join(str(s or "").lower().split())


def rank_key(m):
    return (str(m.get("last_updated_date", "")), 1 if m.get("stack_name") in CURATED else 0, m.get("_score") or 0)


def collapse(matches, want):
    best = {}
    for m in matches:
        k = norm(m.get("question")) or m["_id"]
        if k not in best or rank_key(m) > rank_key(best[k]):
            best[k] = m
    return sorted(best.values(), key=lambda m: m.get("_score") or 0, reverse=True)[:want]


def shape(m):
    return {"id": m["_id"], "score": round(m.get("_score") or 0, 4), "stack": m.get("stack_name"),
            "updated": str(m.get("last_updated_date", ""))[:10], "source": m.get("source_doc"),
            "tags": m.get("tags", []), "legal_approved": bool(m.get("legal_approved")),
            "question": m.get("question"), "answer": m.get("answer_plain")}


def query(index, q, want=5, stack=None, raw=False):
    if stack:
        return search(index, q, want, stack), f"stack:{stack}"
    if raw:
        return search(index, q, want), "raw"
    return collapse(search(index, q, max(want * 4, 20)), want), "prefer-newest"


def evaluate(index, path):
    cases = json.load(open(path))
    hits = 0
    for c in cases:
        rows, _ = query(index, c["question"])
        top = rows[0] if rows else {}
        ok = top and (top["_id"] == c["expected"] or norm(top.get("question")) == norm(c["expected"]))
        hits += bool(ok)
        print(("HIT " if ok else "MISS"), f"{top.get('_score', 0):.3f}", c["question"][:60], "->", (top.get("question") or "")[:50])
    print(f"\ntop-1: {hits}/{len(cases)}")


def main():
    argv = sys.argv[1:]
    index = argv[argv.index("--index") + 1] if "--index" in argv else "rfi-answer-library"
    if "--eval" in argv:
        return evaluate(index, argv[argv.index("--eval") + 1])
    stack = argv[argv.index("--stack") + 1] if "--stack" in argv else None
    args = [a for i, a in enumerate(argv) if not a.startswith("--") and (i == 0 or argv[i - 1] not in ("--stack", "--index"))]
    if not args:
        sys.exit(__doc__)
    rows, mode = query(index, args[0], int(args[1]) if len(args) > 1 else 5, stack, "--raw" in argv)
    print(json.dumps({"query": args[0], "mode": mode, "results": [shape(m) for m in rows]}, indent=2))


if __name__ == "__main__":
    main()
