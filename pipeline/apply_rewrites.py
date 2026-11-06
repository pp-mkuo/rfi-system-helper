#!/usr/bin/env python3
"""Apply approved Q&A bank rewrites to loopio-library-2.

Usage (from ~/Desktop/pinecone-loopio, next to keys.env and qabank_rewrites_approved.json):
  python3 apply_rewrites.py            # dry run
  python3 apply_rewrites.py --commit   # re-embed + upsert rewrites under the same IDs, delete merged rows

Same embedding recipe as ingest_qabank.py (question + "\\n\\n" + answer, text-embedding-3-small).
Also updates qabank_records.json so --rollback in ingest_qabank.py stays accurate.
"""
import json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ingest_qabank as I

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    plan = json.load(open(os.path.join(HERE, "qabank_rewrites_approved.json")))
    up, dele = plan["upsert"], plan["delete"]
    assert all(r["id"].startswith("qabank-") for r in up) and all(d.startswith("qabank-") for d in dele)
    print(f"{len(up)} rewrites to upsert, {len(dele)} records to delete: {', '.join(dele)}")
    if "--commit" not in sys.argv:
        for r in up[:3]:
            print(" ", r["id"], "|", r["metadata"]["question"][:80])
        print("DRY RUN — nothing written. Re-run with --commit.")
        return
    keys = I.load_keys()
    pk = keys["PINECONE_API_KEY"]
    before = I.pc("/describe_index_stats", {}, pk).get("totalVectorCount")
    vecs = I.embed([r["text"] for r in up], keys["OPENAI_API_KEY"])
    I.pc("/vectors/upsert", {"namespace": I.NAMESPACE, "vectors": [
        {"id": r["id"], "values": v, "metadata": r["metadata"]} for r, v in zip(up, vecs)]}, pk)
    I.pc("/vectors/delete", {"namespace": I.NAMESPACE, "ids": dele}, pk)
    # keep the local record file in step
    path = os.path.join(HERE, "qabank_records.json")
    recs = {r["id"]: r for r in json.load(open(path))}
    for r in up:
        recs[r["id"]] = r
    for d in dele:
        recs.pop(d, None)
    json.dump(list(recs.values()), open(path, "w"), indent=1)
    time.sleep(5)
    after = I.pc("/describe_index_stats", {}, pk).get("totalVectorCount")
    print(f"Upserted {len(up)}, deleted {len(dele)}. Index count: {before} -> {after}")


if __name__ == "__main__":
    main()
