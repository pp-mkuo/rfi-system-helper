#!/usr/bin/env python3
"""Upsert RFI Q&A Bank v2 rows into loopio-library-2.

Usage (from ~/Desktop/pinecone-loopio, next to keys.env and qabank_records.json):
  python3 ingest_qabank.py              # dry run: counts, sample, no writes
  python3 ingest_qabank.py --commit     # embed + upsert
  python3 ingest_qabank.py --rollback   # delete every qabank- record this file lists

Embedding text = question + "\\n\\n" + answer, text-embedding-3-small, same as existing records.
Every record ID starts with "qabank-" so the batch is identifiable and reversible.
Keys are read from keys.env and never printed.
"""
import json, os, sys, time, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
INDEX_HOST = "https://loopio-library-2-rme8ns3.svc.aped-4627-b74a.pinecone.io"
EMBED_MODEL = "text-embedding-3-small"
OPENAI_HOSTS = ("https://us.api.openai.com", "https://api.openai.com")
NAMESPACE = ""
BATCH = 50


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
    with urllib.request.urlopen(req, timeout=120) as r:
        body = r.read()
        return json.loads(body) if body else {}


def embed(texts, key):
    last = None
    for host in OPENAI_HOSTS:
        try:
            out = post(host + "/v1/embeddings", {"model": EMBED_MODEL, "input": texts},
                       {"Authorization": "Bearer " + key})
            return [d["embedding"] for d in sorted(out["data"], key=lambda d: d["index"])]
        except Exception as e:
            last = e
    raise last


def pc(path, payload, key):
    return post(INDEX_HOST + path, payload, {"Api-Key": key, "X-Pinecone-API-Version": "2025-04"})


def main():
    flags = set(sys.argv[1:])
    recs = json.load(open(os.path.join(HERE, "qabank_records.json")))
    assert all(r["id"].startswith("qabank-") for r in recs), "every ID must carry the qabank- prefix"
    by_aud = {}
    for r in recs:
        by_aud[r["metadata"]["audience"]] = by_aud.get(r["metadata"]["audience"], 0) + 1
    print(f"{len(recs)} records: {by_aud}")

    if "--rollback" in flags:
        keys = load_keys()
        ids = [r["id"] for r in recs]
        for i in range(0, len(ids), 100):
            pc("/vectors/delete", {"ids": ids[i:i + 100], "namespace": NAMESPACE}, keys["PINECONE_API_KEY"])
        print(f"Deleted {len(ids)} qabank- records.")
        return

    if "--commit" not in flags:
        print("DRY RUN — nothing written. Sample:")
        for r in recs[:3]:
            print(" ", r["id"], "|", r["metadata"]["question"][:80], "|", r["metadata"]["tags"])
        print("Re-run with --commit to embed and upsert.")
        return

    keys = load_keys()
    before = pc("/describe_index_stats", {}, keys["PINECONE_API_KEY"]).get("totalVectorCount")
    done = 0
    for i in range(0, len(recs), BATCH):
        chunk = recs[i:i + BATCH]
        vecs = embed([r["text"] for r in chunk], keys["OPENAI_API_KEY"])
        pc("/vectors/upsert", {"namespace": NAMESPACE, "vectors": [
            {"id": r["id"], "values": v, "metadata": r["metadata"]} for r, v in zip(chunk, vecs)]},
           keys["PINECONE_API_KEY"])
        done += len(chunk)
        print(f"  upserted {done}/{len(recs)}")
        time.sleep(0.3)
    time.sleep(5)
    after = pc("/describe_index_stats", {}, keys["PINECONE_API_KEY"]).get("totalVectorCount")
    print(f"Index count: {before} -> {after}")


if __name__ == "__main__":
    main()
