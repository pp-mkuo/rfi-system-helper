#!/usr/bin/env python3
"""AF-129: the AF-49 retrieval test set, run through rfi-agent-memory (memory store, grep search).

AF-49 scores Pinecone by calling query.py directly. A memory store has no search API, so here
the agent itself searches /mnt/memory and returns its ranked record ids, and those are graded
the same way: top1 = first id is expected, top3 = any of the first three is.
Baseline to compare against: AF-49 results/2026-11-12.json (loopio-library-2).

    unset ANTHROPIC_API_KEY
    python3 evals/retrieval/run_memory_retrieval.py --limit 10     # trial
    python3 evals/retrieval/run_memory_retrieval.py                # all 91
"""
import argparse, datetime, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'accuracy'))
import run_accuracy_eval as R  # noqa: E402  (ant, ended, collect)

AGENT_ID = 'agent_01Eu17bC4gDYXD1h4eHT7Nu8'   # rfi-agent-memory
MEMORY_STORE = 'memstore_01MqRVN7npVy4FFPnuWZmVru'

PROTOCOL = """

This is a retrieval test. Do not triage, draft or route. For each question, search the library with the
library-search-memory skill as you normally would, and decide which library records answer it.
End with exactly one fenced ```json block, a list with one object per question:
{"id": "<question id>", "record_ids": ["<best record id>", "<next>", ...]}  (up to 5, best first; [] if none answers it)"""


def norm(i):
    return i[len('loopio-'):] if i.startswith('loopio-') else i


def grade(item, ans):
    got = [norm(str(x)) for x in ((ans or {}).get('record_ids') or [])]
    exp = set(item['expected_ids']) | set(item.get('added_on_review') or [])
    return {'id': item['id'], 'origin': item['origin'], 'source': item['source'], 'answered': ans is not None,
            'got': got, 'top1': bool(got) and got[0] in exp, 'top3': any(g in exp for g in got[:3]),
            'any5': any(g in exp for g in got[:5])}


def summary(rows):
    def s(rs):
        n = len(rs)
        return {'n': n, **{k: round(sum(r[k] for r in rs) / n, 3) for k in ('top1', 'top3', 'any5')},
                'top1_count': sum(r['top1'] for r in rs)} if n else {'n': 0}
    return {'overall': s(rows), 'by_origin': {o: s([r for r in rows if r['origin'] == o]) for o in sorted({r['origin'] for r in rows})},
            'unparsed': [r['id'] for r in rows if not r['answered']]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--limit', type=int)
    ap.add_argument('--origin', help='only items with this origin, e.g. paraphrase')
    ap.add_argument('--batch-size', type=int, default=10)
    ap.add_argument('--budget-cents', type=int, default=150)
    a = ap.parse_args()
    R.AGENT_ID, R.VAULT_ID, R.MEMORY_STORE = AGENT_ID, None, MEMORY_STORE
    items = [i for i in json.load(open(os.path.join(HERE, 'testset.json')))['items'] if not a.origin or i['origin'] == a.origin][:a.limit]
    version = R.ant('beta:agents', 'retrieve', '--agent-id', AGENT_ID)['version']
    R.PROTOCOL = PROTOCOL  # run_batch appends R.PROTOCOL to the questions
    res = {'date': datetime.date.today().isoformat(), 'agent': {'id': AGENT_ID, 'version': version},
           'memory_store': MEMORY_STORE, 'batches': [], 'grades': []}
    for n in range(0, len(items), a.batch_size):
        batch = items[n:n + a.batch_size]
        print(f'session {n // a.batch_size + 1}: {batch[0]["id"]}..{batch[-1]["id"]}', flush=True)
        b = R.run_batch(batch, version, a.budget_cents, f'AF-129 retrieval {n // a.batch_size + 1}')
        b['ids'] = [i['id'] for i in batch]
        b.pop('retrieved')  # bash output is large and not needed for id grading
        res['batches'].append(b)
        res['grades'] += [grade(i, b['parsed'].get(i['id'])) for i in batch]
        print(f'  {b["status"]} {b["stop_reason"]}  ${b["cost_cents"] / 100:.2f}', flush=True)
    res['summary'] = summary(res['grades'])
    res['cost_usd'] = sum(b['cost_cents'] for b in res['batches']) / 100
    out = os.path.join(HERE, 'results', f'{res["date"]}-memory-v{version}{"-" + a.origin if a.origin else ""}{"-first" + str(a.limit) if a.limit else ""}.json')
    json.dump(res, open(out, 'w'), indent=1, ensure_ascii=False)
    print(json.dumps({'summary': res['summary'], 'cost_usd': res['cost_usd']}, indent=1))
    print(f'wrote {out}')


if __name__ == '__main__':
    _i = {'id': 'x', 'origin': 'p', 'source': 'loopio', 'expected_ids': ['13131320']}
    _g = grade(_i, {'record_ids': ['loopio-99', 'loopio-13131320']})
    assert not _g['top1'] and _g['top3'] and not grade(_i, None)['answered']  # self-check
    main()
