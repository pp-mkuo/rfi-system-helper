#!/usr/bin/env python3
"""AF-129: load the RFI answer library into a Managed Agents memory store.

One file per library record, one folder per stack:
  /client-strategy-cleaned/loopio-13131320.md
  /rfi-2026/rfi2026-kso-001.md
  /rfi-qa-bank-v2-unverified/qabank-SUP-001.md

Each file opens with id, question, stack, updated, tags and source lines, then the answer,
so grep finds questions and answers alike and every hit shows its record id.
Records are the 2,297 IDs written to the Pinecone index (backfill-rollback-rfi-answer-library.json):
1,509 Loopio export rows (data/loopio_library_export_updated.csv), 202 RFI 2026 (records.json),
586 Q&A Bank v2 (qabank_records.json).

Talks to the API only through the `ant` CLI with the OAuth profile (no key in env or files).
  python3 pipeline/build_memory_store.py                      # dry run: counts and sizes, no writes
  python3 pipeline/build_memory_store.py --commit             # create the store and upload every record
  python3 pipeline/build_memory_store.py --commit --store-id memstore_...   # resume into an existing store
"""
import csv, json, os, re, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BETA = 'agent-memory-2026-07-22'
NAME = 'rfi-answer-library'
DESCRIPTION = ('PulsePoint approved RFI answer library: one file per Q&A record, one folder per stack. '
               'Each file starts with id, question, stack, updated, tags and source lines, then the answer. '
               'Read-only reference: search it with grep, never edit it.')


def ant(*args):
    env = {k: v for k, v in os.environ.items() if k != 'ANTHROPIC_API_KEY'}  # OAuth profile, never a key
    for attempt in range(4):
        p = subprocess.run(['ant', *args, '--beta', BETA, '--format', 'json'], capture_output=True, text=True, env=env)
        if p.returncode == 0:
            return json.loads(p.stdout)
        if 'already exists' in p.stderr or 'conflict' in p.stderr.lower():
            return {'skipped': True}
        time.sleep(3 * (attempt + 1))
    raise RuntimeError(p.stderr.strip()[:300])


def slug(s):
    return re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')


def records():
    ids = json.load(open(os.path.join(ROOT, 'pipeline/backfill-rollback-rfi-answer-library.json')))['ids']
    want, out = set(ids), {}
    for r in csv.DictReader(open(os.path.join(ROOT, 'data/loopio_library_export_updated.csv'))):
        rid = 'loopio-' + r['id']
        if rid in want and rid not in out:  # ponytail: CSV repeats 2 ids; first row wins, same as the index
            out[rid] = {'question': r['question'], 'answer': r['answer_plain'], 'stack': r['stack_name'],
                        'updated': r['last_updated_date'], 'tags': r['tags'], 'source': 'loopio'}
    for f in ('records.json', 'qabank_records.json'):
        for r in json.load(open(os.path.join(ROOT, 'pipeline', f))):
            m = r['metadata']
            out[r['id']] = {'question': m['question'], 'answer': m['answer_plain'], 'stack': m['stack_name'],
                            'updated': m.get('last_updated_date', ''), 'tags': ', '.join(m.get('tags') or []),
                            'source': m.get('source_doc') or m.get('source_ref') or m.get('source', '')}
    missing = want - out.keys()
    assert not missing, f'{len(missing)} index ids have no source row, e.g. {sorted(missing)[:3]}'
    return out


def render(rid, r):
    path = f'/{slug(r["stack"])}/{rid}.md'
    body = (f'id: {rid}\nquestion: {r["question"]}\nstack: {r["stack"]}\nupdated: {r["updated"]}\n'
            f'tags: {r["tags"]}\nsource: {r["source"]}\n\n{r["answer"].strip()}\n')
    return path, body


def main():
    files = [render(rid, r) for rid, r in sorted(records().items())]
    sizes = [len(b.encode()) for _, b in files]
    folders = sorted({p.split('/')[1] for p, _ in files})
    print(f'{len(files)} files, {sum(sizes) / 1e6:.2f} MB, largest {max(sizes)} B, folders: {", ".join(folders)}')
    assert max(sizes) < 100_000 and len(files) <= 10_000  # memory store limits
    if '--commit' not in sys.argv:
        print(files[0][0]); print(files[0][1][:400]); return
    store = sys.argv[sys.argv.index('--store-id') + 1] if '--store-id' in sys.argv else \
        ant('beta:memory-stores', 'create', '--name', NAME, '--description', DESCRIPTION,
            '--metadata', json.dumps({'ticket': 'AF-129'}))['id']
    print('store', store, flush=True)

    def up(f):
        ant('beta:memory-stores:memories', 'create', '--memory-store-id', store, '--path', f[0], '--content', f[1])
    done = 0
    with ThreadPoolExecutor(6) as ex:
        for _ in ex.map(up, files):
            done += 1
            if done % 200 == 0:
                print(f'  {done}/{len(files)}', flush=True)
    print(f'uploaded {done} files to {store}')


if __name__ == '__main__':
    main()
