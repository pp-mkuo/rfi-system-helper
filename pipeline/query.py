#!/usr/bin/env python3
"""Semantic search over the loopio-library-2 Pinecone index.

Usage:
  python3 query.py "your question" [topK] [--raw] [--stack NAME] [--cleaned-only]

Default ("prefer-newest"): one row per question, and where the same question
appears more than once the answer with the most recent last_updated_date wins.
Ties break toward the curated stacks ("Client Strategy- Cleaned", "RFI 2026").

Ranking is by date rather than by stack membership, so:
  * 2026 RFI answers automatically outrank older duplicates
  * nothing has to be relabeled when a 2027 batch is added
  * the ~79 questions that exist only in the old "Client Strategy" stack are
    still returned, instead of being silently dropped

  --raw           no dedupe, no preference — every match exactly as stored
  --stack NAME    hard filter to one stack_name (e.g. --stack "RFI 2026")
  --cleaned-only  shorthand for --stack "Client Strategy- Cleaned".
                  NOTE: this excludes the RFI 2026 batch. Prefer the default.

Reads keys from keys.env in this folder. Never prints key values.
"""
import json, os, sys, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
INDEX_HOST = "https://loopio-library-2-rme8ns3.svc.aped-4627-b74a.pinecone.io"
EMBED_MODEL = "text-embedding-3-small"
# us.api first: our OpenAI org enforces US data residency.
OPENAI_HOSTS = ("https://us.api.openai.com", "https://api.openai.com")
CLEANED = "Client Strategy- Cleaned"
# stacks that hold reviewed answers; used only to break date ties
CURATED = (CLEANED, "RFI 2026")
NAMESPACE = ""  # this index uses the empty namespace, not __default__


def load_keys():
    keys = {}
    with open(os.path.join(HERE, "keys.env")) as fh:
        for line in fh:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                keys[k.strip()] = v.strip().strip('"').strip("'")
    missing = [k for k in ("PINECONE_API_KEY", "OPENAI_API_KEY") if not keys.get(k)]
    if missing:
        sys.exit("Missing in keys.env: " + ", ".join(missing))
    return keys


def post(url, payload, headers):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json", **headers})
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.load(r)


def embed(text, key):
    last = None
    for host in OPENAI_HOSTS:
        try:
            out = post(host + "/v1/embeddings",
                       {"model": EMBED_MODEL, "input": text},
                       {"Authorization": "Bearer " + key})
            return out["data"][0]["embedding"]
        except Exception as e:
            last = e
    raise last


def search(vec, key, top_k, stack=None):
    payload = {"vector": vec, "topK": top_k, "includeMetadata": True, "namespace": NAMESPACE}
    if stack:
        payload["filter"] = {"stack_name": {"$eq": stack}}
    return post(INDEX_HOST + "/query", payload,
                {"Api-Key": key, "X-Pinecone-API-Version": "2025-04"}).get("matches", [])


def norm(s):
    return " ".join(str(s or "").lower().split())


def rank_key(match):
    """Sort key for choosing between duplicate questions: newest date first,
    then curated stacks, then similarity score."""
    md = match.get("metadata") or {}
    return (str(md.get("last_updated_date", "")),
            1 if md.get("stack_name") in CURATED else 0,
            match.get("score", 0))


def collapse(matches, want):
    """One row per question; newest answer wins, curated stack breaks ties."""
    best = {}
    for m in matches:
        md = m.get("metadata") or {}
        k = norm(md.get("question")) or m["id"]
        cur = best.get(k)
        if cur is None or rank_key(m) > rank_key(cur):
            best[k] = m
    rows = sorted(best.values(), key=lambda m: m.get("score", 0), reverse=True)
    return rows[:want]


def main():
    argv = sys.argv[1:]
    stack = None
    if "--stack" in argv:
        i = argv.index("--stack")
        if i + 1 >= len(argv):
            sys.exit("--stack needs a stack name")
        stack = argv[i + 1]
        del argv[i:i + 2]
    flags = {a for a in argv if a.startswith("--")}
    args = [a for a in argv if not a.startswith("--")]
    if not args:
        sys.exit('Usage: python3 query.py "your question" [topK] '
                 '[--raw] [--stack NAME] [--cleaned-only]')
    if "--cleaned-only" in flags:
        stack = CLEANED
        print("note: --cleaned-only excludes the RFI 2026 batch", file=sys.stderr)

    q = args[0]
    want = int(args[1]) if len(args) > 1 else 5
    keys = load_keys()
    vec = embed(q, keys["OPENAI_API_KEY"])

    if stack:
        rows, mode = search(vec, keys["PINECONE_API_KEY"], want, stack=stack), f"stack:{stack}"
    elif "--raw" in flags:
        rows, mode = search(vec, keys["PINECONE_API_KEY"], want), "raw"
    else:
        # over-fetch so duplicates collapsing doesn't shrink the result set
        rows = collapse(search(vec, keys["PINECONE_API_KEY"], max(want * 4, 20)), want)
        mode = "prefer-newest"

    out = {"query": q, "mode": mode, "results": [{
        "score": round(m.get("score", 0), 4),
        "stack": (m.get("metadata") or {}).get("stack_name"),
        "updated": str((m.get("metadata") or {}).get("last_updated_date", ""))[:10],
        "source": (m.get("metadata") or {}).get("source_doc"),
        "tags": (m.get("metadata") or {}).get("tags", []),
        "question": (m.get("metadata") or {}).get("question"),
        "answer": (m.get("metadata") or {}).get("answer_plain"),
    } for m in rows]}
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
