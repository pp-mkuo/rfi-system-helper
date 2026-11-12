#!/usr/bin/env python3
"""AF-49 retrieval test: does the agent's index return the right record?

Usage:
  python3 evals/retrieval/run_retrieval_eval.py [testset.json ...] [--out FILE]
  python3 evals/retrieval/run_retrieval_eval.py --selftest

Searches go through pipeline/query.py (same embed, search and prefer-newest
collapse the agent uses). Keys come from pipeline/keys.env or the environment;
nothing here prints them. Read-only: describe_index_stats, fetch, query.

Defaults: testset.json, plus dentsu14.json once it has items.
"""
import datetime, json, os, statistics, sys, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
# Caedon's copy of loopio-library-2, the one rfi-agent's vault reaches.
os.environ.setdefault("PINECONE_INDEX_HOST",
                      "https://loopio-library-2-yxxbxim.svc.gcp-us-central1-4a9f.pinecone.io")
sys.path.insert(0, os.path.join(REPO, "pipeline"))
import query  # noqa: E402

FLOOR = 0.45      # rfi-system-helper skill: below this, "no basis"
WINDOW = 20       # query.py over-fetches 20 for a top-5 answer; rank within that
DENTSU_BAR = 13   # today's library: 13 of 14 top-1 on Maggie's Dentsu questions


def unverified(row):
    return "unverified" in str(row.get("stack") or "").lower()


def pinecone(path, key, payload=None):
    h = {"Api-Key": key, "X-Pinecone-API-Version": "2025-04"}
    url = query.INDEX_HOST + path
    if payload is None:
        with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=60) as r:
            return json.load(r)
    return query.post(url, payload, h)


def existing_ids(ids, key):
    found, ids = set(), sorted(ids)
    for i in range(0, len(ids), 50):
        qs = urllib.parse.urlencode([("ids", x) for x in ids[i:i + 50]] + [("namespace", query.NAMESPACE)])
        found |= set(pinecone("/vectors/fetch?" + qs, key).get("vectors", {}))
    return found


def run_item(item, keys):
    vec = query.embed(item["question"], keys["OPENAI_API_KEY"])
    rows = query.collapse(query.search(vec, keys["PINECONE_API_KEY"], WINDOW), WINDOW)
    return [{"id": m["id"], "score": round(m.get("score", 0), 4),
             "stack": (m.get("metadata") or {}).get("stack_name"),
             "question": " ".join(str((m.get("metadata") or {}).get("question", "")).split())[:160]}
            for m in rows]


def grade(item, rows):
    want = set(item["expected_ids"])
    rank = next((i + 1 for i, r in enumerate(rows) if r["id"] in want), None)
    right = rows[rank - 1]["score"] if rank else None
    wrong = next((r["score"] for r in rows if r["id"] not in want), None)
    # unverified Q&A Bank record above the best verified correct record
    outrank = None
    if not item["primary_id"].startswith("qabank-"):
        best_ok = next((i for i, r in enumerate(rows) if r["id"] in want and not unverified(r)), None)
        above = [r for r in rows[:best_ok if best_ok is not None else 5]
                 if unverified(r) and r["id"] not in want]
        if above:
            outrank = {"unverified": above[0], "verified_rank": best_ok + 1 if best_ok is not None else None,
                       "verified_score": rows[best_ok]["score"] if best_ok is not None else None}
    return {"rank": rank, "right_score": right, "best_wrong_score": wrong,
            "gap": round(right - wrong, 4) if right is not None and wrong is not None else None,
            "under_floor": right is None or right < FLOOR, "unverified_outranks": outrank}


def summarize(graded):
    n = len(graded)
    if not n:
        return {"n": 0}
    gaps = [g["gap"] for g in graded if g["gap"] is not None]
    return {"n": n,
            "top1": round(sum(g["rank"] == 1 for g in graded) / n, 3),
            "top3": round(sum(bool(g["rank"]) and g["rank"] <= 3 for g in graded) / n, 3),
            "top1_count": sum(g["rank"] == 1 for g in graded),
            "mrr": round(sum(1 / g["rank"] for g in graded if g["rank"]) / n, 3),
            "gap_median": round(statistics.median(gaps), 4) if gaps else None,
            "gap_mean": round(statistics.mean(gaps), 4) if gaps else None,
            "under_floor": sum(g["under_floor"] for g in graded),
            "not_in_top20": sum(g["rank"] is None for g in graded),
            "unverified_outranks": sum(bool(g["unverified_outranks"]) for g in graded)}


def by(results, field):
    keys = sorted({r[field] for r in results})
    return {k: summarize([r["grade"] for r in results if r[field] == k]) for k in keys}


def load(path):
    with open(path) as fh:
        return json.load(fh).get("items", [])


def main():
    argv = sys.argv[1:]
    out = None
    if "--out" in argv:
        out = argv[argv.index("--out") + 1]
        del argv[argv.index("--out"):argv.index("--out") + 2]
    sets = argv or [os.path.join(HERE, "testset.json"), os.path.join(HERE, "dentsu14.json")]
    items = []
    for p in sets:
        if os.path.exists(p):
            for it in load(p):
                items.append({**it, "set": os.path.splitext(os.path.basename(p))[0]})

    keys = query.load_keys()
    stats = pinecone("/describe_index_stats", keys["PINECONE_API_KEY"], {})
    have = existing_ids({i for it in items for i in it["expected_ids"]}, keys["PINECONE_API_KEY"])
    results, dropped = [], []
    for it in items:
        it = {**it, "expected_ids": [i for i in it["expected_ids"] if i in have]}
        if not it["expected_ids"]:
            dropped.append(it["id"])
            continue
        rows = run_item(it, keys)
        results.append({**it, "grade": grade(it, rows), "top5": rows[:5]})
        print(".", end="", file=sys.stderr, flush=True)
    print(file=sys.stderr)

    main_set = [r for r in results if r["set"] != "dentsu14"]
    dentsu = [r for r in results if r["set"] == "dentsu14"]
    report = {
        "date": datetime.date.today().isoformat(),
        "index_host": query.INDEX_HOST.replace("https://", ""),
        "record_count": stats.get("totalVectorCount"),
        "embed_model": query.EMBED_MODEL,
        "mode": f"prefer-newest (query.collapse), ranked within top {WINDOW}",
        "floor": FLOOR,
        "dropped_no_expected_id_in_index": dropped,
        "overall": summarize([r["grade"] for r in main_set]),
        "by_source": by(main_set, "source"),
        "by_origin": by(main_set, "origin"),
        "dentsu14": ({**summarize([r["grade"] for r in dentsu]), "bar_top1": DENTSU_BAR,
                      "meets_bar": sum(r["grade"]["rank"] == 1 for r in dentsu) >= DENTSU_BAR}
                     if dentsu else "pending: add Maggie's questions to dentsu14.json"),
        "unverified_outranks_cases": [
            {"id": r["id"], "question": r["question"], **r["grade"]["unverified_outranks"]}
            for r in results if r["grade"]["unverified_outranks"]],
        "misses": [{"id": r["id"], "source": r["source"], "question": r["question"],
                    "rank": r["grade"]["rank"], "right_score": r["grade"]["right_score"],
                    "top1": r["top5"][0]} for r in results if r["grade"]["rank"] != 1],
        "items": [{k: r[k] for k in ("id", "set", "source", "origin", "question", "grade", "top5")}
                  for r in results],
    }
    out = out or os.path.join(HERE, "results", f"{report['date']}.json")
    with open(out, "w") as fh:
        json.dump(report, fh, indent=1)
    print(json.dumps({k: report[k] for k in
                      ("date", "record_count", "overall", "by_source", "by_origin", "dentsu14")}, indent=1))
    print(f"unverified outranks verified: {len(report['unverified_outranks_cases'])}; "
          f"dropped: {len(dropped)}; full results: {os.path.relpath(out, REPO)}")


def selftest():
    it = {"expected_ids": ["a", "a2"], "primary_id": "a"}
    rows = [{"id": "q", "score": 0.79, "stack": "RFI Q&A Bank v2 (unverified)"},
            {"id": "a", "score": 0.59, "stack": "RFI 2026"},
            {"id": "b", "score": 0.50, "stack": "RFI 2026"}]
    g = grade(it, rows)
    assert g["rank"] == 2 and g["gap"] == -0.2 and not g["under_floor"], g
    assert g["unverified_outranks"]["verified_rank"] == 2, g
    miss = grade(it, rows[2:])
    assert miss["rank"] is None and miss["under_floor"] and miss["gap"] is None, miss
    s = summarize([g, miss, grade(it, rows[1:])])
    assert s["top1_count"] == 1 and s["top3"] == round(2 / 3, 3) and s["mrr"] == 0.5, s
    print("selftest ok")


if __name__ == "__main__":
    selftest() if "--selftest" in sys.argv else main()
