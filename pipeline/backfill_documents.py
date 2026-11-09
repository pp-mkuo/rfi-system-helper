#!/usr/bin/env python3
"""Rebuild the answer library as a Pinecone *document* index with integrated
text-embedding-3-small (Documents API, version 2026-07).

Why: the legacy index `loopio-library-2` has no hosted model, so every query
needs an OpenAI key and a desktop link. A document index embeds on write and
on search with the same OpenAI model, so a server-side pass-through can serve
it with the Pinecone key alone. The live `loopio-library-2` is never touched.

Sources (all in this repo), one document per record:
  data/loopio_library_export_updated.csv  Loopio export, 1,509 unique rows.
      The 80 rows tagged "2026" are a copy of the KSO RFI that records.json
      covers properly, so they are skipped.
  pipeline/records.json                    RFI 2026 batch (202), stack "RFI 2026"
  pipeline/qabank_records.json             RFI Q&A Bank v2 (586), unverified

Embedding text = question + "\\n\\n" + answer_plain (same recipe as before).
Metadata keeps what query.py relies on: question, answer_plain, stack_name,
tags, last_updated_date, source_doc; plus source, cleaned, legal_approved.

Usage:
  export PINECONE_API_KEY=...                   # never in the repo
  python3 backfill_documents.py                 # dry run: build + report, no network
  python3 backfill_documents.py --create-index  # create index (tries us, falls back to global)
  python3 backfill_documents.py --commit        # upsert; writes backfill-rollback-<index>.json
  python3 backfill_documents.py --rollback      # delete every id in the rollback file
  python3 backfill_documents.py --delete-index  # drop the whole index (asks for the name)

  --index NAME        default rfi-answer-library
  --location us|global  force a processing location for --create-index
"""
import csv, json, os, sys, time, urllib.error, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
API = "https://api.pinecone.io"
VERSION = "2026-07"
MODEL = "text-embedding-3-small"
DIM = 1536
NAMESPACE = "__default__"
EMBED_FIELD = "embed_text"
BATCH = 96  # Pinecone's cap per request when a field embeds
CLEANED = "Client Strategy- Cleaned"


def key():
    k = os.environ.get("PINECONE_API_KEY")
    if not k:
        sys.exit("Set PINECONE_API_KEY in the environment (e.g. `source ~/.config/rfi-system-helper/keys.env`).")
    return k


def call(url, body=None, method=None, retries=4):
    data = json.dumps(body).encode() if body is not None else None
    for attempt in range(retries):
        req = urllib.request.Request(url, data=data, method=method or ("POST" if data else "GET"), headers={
            "Content-Type": "application/json", "Api-Key": key(), "X-Pinecone-Api-Version": VERSION})
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                raw = r.read()
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as e:
            detail = e.read().decode()[:400]
            if e.code in (429, 500, 502, 503, 504) and attempt < retries - 1:
                time.sleep(2 ** attempt); continue
            raise RuntimeError(f"{method or 'POST'} {url} -> HTTP {e.code}: {detail}")


def clean_meta(d):
    """Pinecone metadata: bool, number, string or list of strings. Drop empties."""
    out = {}
    for k, v in d.items():
        if v is None or v == "" or v == []:
            continue
        if isinstance(v, list):
            v = [str(x) for x in v if str(x).strip()]
            if not v:
                continue
        elif not isinstance(v, (str, int, float, bool)):
            v = str(v)
        out[k] = v
    return out


def split_tags(s):
    return [t.strip() for t in str(s or "").split(";") if t.strip()]


def build():
    docs, seen = [], set()

    def add(_id, question, answer, meta):
        if _id in seen:
            return
        seen.add(_id)
        tags = meta.get("tags") or []
        meta = clean_meta({**meta,
                           "question": question, "answer_plain": answer,
                           "cleaned": meta.get("stack_name") == CLEANED,
                           "legal_approved": "Legal Approved" in tags})
        docs.append({"_id": _id, EMBED_FIELD: question + "\n\n" + answer, **meta})

    skipped_2026 = 0
    with open(os.path.join(REPO, "data", "loopio_library_export_updated.csv"), newline="") as fh:
        for row in csv.DictReader(fh):
            tags = split_tags(row["tags"])
            if "2026" in tags:          # KSO RFI copy; records.json has the real batch
                skipped_2026 += 1
                continue
            add("loopio-" + row["id"], row["question"].strip(), row["answer_plain"].strip(), {
                "stack_name": row["stack_name"], "tags": tags,
                "last_updated_date": row["last_updated_date"],
                "status": row["status"].upper(), "source": "loopio"})

    for r in json.load(open(os.path.join(HERE, "records.json"))):
        m = dict(r["metadata"])
        add(r["id"], m.pop("question"), m.pop("answer_plain"), {**m, "source": "rfi-2026"})

    for r in json.load(open(os.path.join(HERE, "qabank_records.json"))):
        m = dict(r["metadata"])
        add(r["id"], m.pop("question"), m.pop("answer_plain"), {**m, "source": m.get("source", "qabank"),
                                                                 "source_doc": "RFI Q&A Bank v2"})
    return docs, skipped_2026


def report(docs, skipped):
    by = {}
    for d in docs:
        by[d["stack_name"]] = by.get(d["stack_name"], 0) + 1
    print(f"{len(docs)} documents (skipped {skipped} CSV rows duplicated in records.json)")
    for k, v in sorted(by.items()):
        print(f"  {v:5d}  {k}")
    big = max(len(json.dumps(d)) for d in docs)
    print(f"largest document {big} bytes; longest embed text {max(len(d[EMBED_FIELD]) for d in docs)} chars")
    print("sample:", json.dumps({k: (v[:70] + "…" if isinstance(v, str) and len(v) > 70 else v)
                                 for k, v in docs[0].items()}, ensure_ascii=False))
    print("  ", json.dumps({k: (v[:70] + "…" if isinstance(v, str) and len(v) > 70 else v)
                            for k, v in docs[-1].items()}, ensure_ascii=False))


def describe(name):
    return call(f"{API}/indexes/{name}")


def wait_ready(name):
    for _ in range(90):
        d = describe(name)
        if d.get("status", {}).get("ready"):
            return d
        time.sleep(2)
    sys.exit("index not ready after 3 minutes")


def create_index(name, location):
    def body(loc):
        return {"name": name, "schema": {"fields": {EMBED_FIELD: {
            "type": "string",
            "embed": {"model": MODEL, "dimension": DIM, "metric": "cosine", "processing_location": loc}}}}}
    locations = [location] if location else ["us", "global"]
    for loc in locations:
        try:
            call(f"{API}/indexes", body(loc))
            print(f"created {name} with processing_location={loc}")
            break
        except RuntimeError as e:
            print(f"processing_location={loc} refused: {e}")
            if "401" in str(e) or "UNAUTHENTICATED" in str(e):
                sys.exit("API key rejected; check PINECONE_API_KEY (not a plan-tier problem)")
            if loc == locations[-1]:
                sys.exit("could not create index")
            print("  -> plan is Starter/Builder (us needs Standard+); falling back to global")
    d = wait_ready(name)
    emb = d["schema"]["fields"][EMBED_FIELD]["embed"]
    print(f"host={d['host']}  model={emb.get('model')} dim={emb.get('dimension')} "
          f"metric={emb.get('metric')} processing_location={emb.get('processing_location')}")


def upsert(name, docs):
    d = describe(name)
    host = "https://" + d["host"]
    rollback = os.path.join(HERE, f"backfill-rollback-{name}.json")
    json.dump({"index": name, "host": d["host"], "namespace": NAMESPACE,
               "written": time.strftime("%Y-%m-%dT%H:%M:%S"), "ids": [x["_id"] for x in docs]},
              open(rollback, "w"), indent=0)
    print(f"rollback file: {rollback}")
    done, tokens = 0, 0
    for i in range(0, len(docs), BATCH):
        chunk = docs[i:i + BATCH]
        out = call(f"{host}/namespaces/{NAMESPACE}/documents/upsert", {"documents": chunk})
        done += out.get("upserted_count", 0)
        tokens += (out.get("usage") or {}).get("embed_total_tokens", 0)
        print(f"  upserted {done}/{len(docs)}  (embed tokens so far {tokens})")
    time.sleep(10)
    stats = call(f"{host}/describe_index_stats", {})
    print(f"index reports {stats.get('totalVectorCount') or stats.get('total_vector_count') or stats} records")


def rollback(name):
    path = os.path.join(HERE, f"backfill-rollback-{name}.json")
    rb = json.load(open(path))
    host = "https://" + rb["host"]
    ids = rb["ids"]
    for i in range(0, len(ids), 500):
        call(f"{host}/namespaces/{rb['namespace']}/documents/delete", {"ids": ids[i:i + 500]})
        print(f"  deleted {min(i + 500, len(ids))}/{len(ids)}")


def main():
    argv = sys.argv[1:]
    name = argv[argv.index("--index") + 1] if "--index" in argv else "rfi-answer-library"
    location = argv[argv.index("--location") + 1] if "--location" in argv else None
    docs, skipped = build()
    report(docs, skipped)
    if "--create-index" in argv:
        create_index(name, location)
    if "--commit" in argv:
        upsert(name, docs)
    if "--rollback" in argv:
        rollback(name)
    if "--delete-index" in argv:
        if input(f"type the index name to delete ({name}): ") == name:
            call(f"{API}/indexes/{name}", method="DELETE")
            print("deleted")
    if not any(f in argv for f in ("--create-index", "--commit", "--rollback", "--delete-index")):
        print("\nDRY RUN — nothing written. Use --create-index, then --commit.")


if __name__ == "__main__":
    main()
