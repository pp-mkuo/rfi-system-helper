#!/usr/bin/env python3
"""Propose candidate records for the pending Dentsu questions (AF-49).

Usage:
  python3 evals/retrieval/propose_dentsu_candidates.py [--top 5] [--out FILE]

For each item in dentsu14.json "pending_items" (and each negative check), runs the
same search path as run_retrieval_eval.py and writes a review sheet: the top
records with score, stack, date, stored question and answer. A reviewer ticks the
records that answer the question; those ids become primary_id / expected_ids.
Read-only. Keys come from pipeline/keys.env or the environment.
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import run_retrieval_eval as rre  # sets PINECONE_INDEX_HOST to Caedon's copy  # noqa: E402

query = rre.query


def main():
    argv = sys.argv[1:]
    top = int(argv[argv.index("--top") + 1]) if "--top" in argv else 5
    out = argv[argv.index("--out") + 1] if "--out" in argv else os.path.join(HERE, "dentsu14_candidates.md")
    doc = json.load(open(os.path.join(HERE, "dentsu14.json")))
    keys = query.load_keys()
    lines = ["# Dentsu set: candidate records to confirm", "",
             "Tick every record that answers the question. The best one is primary_id; all ticked ids go in expected_ids.",
             f"Index: {query.INDEX_HOST}", ""]
    todo = [(i["rfi_ref"], i["question"], False) for i in doc.get("pending_items", [])]
    todo += [(n["rfi_ref"], n["question"], True) for n in doc.get("negative_checks", [])]
    for ref, q, negative in todo:
        vec = query.embed(q, keys["OPENAI_API_KEY"])
        rows = query.collapse(query.search(vec, keys["PINECONE_API_KEY"], rre.WINDOW), rre.WINDOW)[:top]
        lines += [f"## {ref}" + ("  (negative check: expect top score < 0.45)" if negative else ""), "", f"> {q}", ""]
        for r in rows:
            md = r.get("metadata") or {}
            ans = " ".join(str(md.get("answer_plain", "")).split())
            lines += [f"- [ ] `{r['id']}` · {r.get('score', 0):.3f} · {md.get('stack_name')} · "
                      f"{str(md.get('last_updated_date', ''))[:10]}",
                      f"  - Q: {' '.join(str(md.get('question', '')).split())}",
                      f"  - A: {ans[:600]}{'…' if len(ans) > 600 else ''}"]
        lines.append("")
    with open(out, "w") as fh:
        fh.write("\n".join(lines))
    print("wrote", out)


if __name__ == "__main__":
    main()
