#!/usr/bin/env python3
"""Ingest the 2026 RFI answer batch into the Pinecone index `loopio-library-2`.

Reads records.json (built from the source RFI files), embeds each record with
OpenAI text-embedding-3-small via us.api.openai.com, and upserts into the index's
default namespace ("" — not "__default__").

Embedding recipe is not a guess: embedding  question + "\\n\\n" + answer_plain
reproduces an existing stored vector at cosine 1.0000, so new records are
directly comparable to the 1,509 already in the index.

Usage:
    python3 ingest_rfi_2026.py                # dry run: embed + report, no writes
    python3 ingest_rfi_2026.py --commit       # embed + upsert
    python3 ingest_rfi_2026.py --rollback     # delete every ID in records.json
"""
import json
import math
import os
import sys
import time
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
HOST = 'https://loopio-library-2-rme8ns3.svc.aped-4627-b74a.pinecone.io'
NAMESPACE = ''          # this index uses the empty namespace
EMBED_MODEL = 'text-embedding-3-small'
EMBED_URL = 'https://us.api.openai.com/v1/embeddings'   # US data residency
EMBED_BATCH = 64
UPSERT_BATCH = 50


def load_keys():
    keys = {}
    with open(os.path.join(HERE, 'keys.env')) as f:
        for line in f:
            line = line.strip()
            if line.startswith('#') or '=' not in line:
                continue
            k, v = line.split('=', 1)
            keys[k.strip()] = v.strip().strip('"').strip("'")
    missing = [k for k in ('PINECONE_API_KEY', 'OPENAI_API_KEY') if not keys.get(k)]
    if missing:
        sys.exit(f'keys.env is missing: {", ".join(missing)}')
    return keys


def call(url, body, headers, method='POST', retries=4):
    for attempt in range(retries):
        req = urllib.request.Request(
            url, data=json.dumps(body).encode() if body is not None else None,
            headers={'Content-Type': 'application/json', **headers}, method=method)
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            detail = e.read().decode()[:300]
            if e.code in (429, 500, 502, 503, 504) and attempt < retries - 1:
                time.sleep(2 ** attempt)
                continue
            sys.exit(f'{url} -> HTTP {e.code}: {detail}')
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
                continue
            sys.exit(f'{url} -> {e!r}')


def embed(texts, oa_key):
    out = []
    for i in range(0, len(texts), EMBED_BATCH):
        chunk = texts[i:i + EMBED_BATCH]
        body = call(EMBED_URL, {'model': EMBED_MODEL, 'input': chunk},
                    {'Authorization': f'Bearer {oa_key}'})
        out += [d['embedding'] for d in body['data']]
        print(f'  embedded {min(i + EMBED_BATCH, len(texts))}/{len(texts)}')
    return out


def main():
    commit = '--commit' in sys.argv
    rollback = '--rollback' in sys.argv
    keys = load_keys()
    records = json.load(open(os.path.join(HERE, 'records.json')))
    ids = [r['id'] for r in records]

    if rollback:
        print(f'deleting {len(ids)} records from namespace {NAMESPACE!r}...')
        for i in range(0, len(ids), 100):
            call(f'{HOST}/vectors/delete',
                 {'namespace': NAMESPACE, 'ids': ids[i:i + 100]},
                 {'Api-Key': keys['PINECONE_API_KEY']})
            print(f'  deleted {min(i + 100, len(ids))}/{len(ids)}')
        print('rollback complete')
        return

    print(f'{len(records)} records; embedding with {EMBED_MODEL}...')
    vecs = embed([r['embed_text'] for r in records], keys['OPENAI_API_KEY'])

    bad = [r['id'] for r, v in zip(records, vecs) if len(v) != 1536]
    if bad:
        sys.exit(f'unexpected embedding dimension for: {bad[:5]}')
    norms = [math.sqrt(sum(x * x for x in v)) for v in vecs]
    print(f'all {len(vecs)} vectors are 1536-dim; '
          f'norm range {min(norms):.3f}-{max(norms):.3f}')

    if not commit:
        print('\nDRY RUN — nothing written. Re-run with --commit to upsert.')
        return

    payload = [{'id': r['id'], 'values': v, 'metadata': r['metadata']}
               for r, v in zip(records, vecs)]
    print(f'\nupserting into namespace {NAMESPACE!r}...')
    total = 0
    for i in range(0, len(payload), UPSERT_BATCH):
        chunk = payload[i:i + UPSERT_BATCH]
        body = call(f'{HOST}/vectors/upsert',
                    {'namespace': NAMESPACE, 'vectors': chunk},
                    {'Api-Key': keys['PINECONE_API_KEY']})
        total += body.get('upsertedCount', 0)
        print(f'  upserted {total}/{len(payload)}')
    print(f'done: {total} records upserted')


if __name__ == '__main__':
    main()
