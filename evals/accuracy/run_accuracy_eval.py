#!/usr/bin/env python3
"""AF-50 accuracy audit: run an RFI question set through the live rfi-agent and score it.

Scores four things per question (rubric in evals/accuracy/README.md):
  triage    agent's green/amber/red == answer key          (plain comparison)
  routing   amber/red route names an expected owner         (plain comparison)
  red_safe  red questions come back with no draft           (plain comparison)
  faithful  every claim in a draft is backed by a library
            record the agent retrieved in that session      (Claude judge)

Talks to the API only through the `ant` CLI with the OAuth profile:
    unset ANTHROPIC_API_KEY
    python3 evals/accuracy/run_accuracy_eval.py --limit 5          # trial
    python3 evals/accuracy/run_accuracy_eval.py                    # full set
    python3 evals/accuracy/run_accuracy_eval.py --set evals/accuracy/dentsu14.json
    python3 evals/accuracy/run_accuracy_eval.py --regrade results/<file>.json   # judge only, no agent runs

Each session is pinned to one agent version, recorded in the results with the
skill versions the session resolved, so runs against later agent versions stay comparable.
"""
import argparse
import datetime
import json
import os
import re
import subprocess
import sys
import time

AGENT_ID = 'agent_018cUnLHJKgSVrFqY346wgTs'
ENV_ID = 'env_01GkLzSQxse6zmM8FxeDE7Ag'        # same as agents/rfi-agent/agent.md metadata
VAULT_ID = 'vlt_011Cgv3jMN4CJVKKKx48ts6F'
JUDGE_MODEL = 'claude-opus-5-5'
JUDGE_PRICE = (4.00, 20.00)   # $/MTok in/out, Opus 5.5 list price (2026-11)
HERE = os.path.dirname(os.path.abspath(__file__))

PROTOCOL = """

Work these as you normally would, but reply in chat only: no workbook file.
After your answer, end with exactly one fenced ```json block, a list with one object per question:
{"id": "<question id>", "triage": "green|amber|red", "route": "<Route cell text, or null>", "draft": "<draft answer text, or null>", "sources": ["<library question(s) the draft used>"]}"""


def ant(*args, parse=True):
    env = {k: v for k, v in os.environ.items() if k != 'ANTHROPIC_API_KEY'}  # OAuth profile, never a key
    for attempt in range(3):
        p = subprocess.run(['ant', *args, '--format', 'jsonl' if parse == 'lines' else 'json'],
                           capture_output=True, text=True, env=env)
        if p.returncode == 0:
            break
        time.sleep(5 * (attempt + 1))
    else:
        sys.exit(f'ant {args[0]} failed: {p.stderr.strip()[:500]}')
    if parse == 'lines':
        return [json.loads(l) for l in p.stdout.splitlines() if l.strip()]
    return json.loads(p.stdout)


def run_batch(batch, version, budget_cents, title):
    text = 'Here are questions from a client RFI questionnaire.\n\n' + '\n\n'.join(
        f'{q["id"]}. {q["question"]}' for q in batch) + PROTOCOL
    s = ant('beta:sessions', 'create',
            '--agent', json.dumps({'type': 'agent', 'id': AGENT_ID, 'version': version}),
            '--environment-id', ENV_ID, '--vault-id', VAULT_ID, '--title', title,
            '--metadata', json.dumps({'ticket': 'AF-50'}),
            '--budget', json.dumps({'type': 'limit', 'max_list_cost': {'amount': str(budget_cents), 'currency': 'USD'}}),
            '--initial-event', json.dumps({'type': 'user.message', 'content': [{'type': 'text', 'text': text}]}))
    deadline = time.time() + 20 * 60
    while not ended(s['id']) and time.time() < deadline:
        time.sleep(10)
    b = collect(s['id'])
    b['skills'] = [{k: sk[k] for k in ('skill_id', 'version')} for sk in s['agent']['skills']]
    return b


def ended(sid):
    events = ant('beta:sessions:events', 'list', '--session-id', sid, '--max-items', '-1', parse='lines')
    return any(e['type'] in ('session.status_idle', 'session.status_terminated') for e in events)


def collect(sid):
    events = ant('beta:sessions:events', 'list', '--session-id', sid, '--max-items', '-1', parse='lines')
    end = [e for e in events if e['type'] in ('session.status_idle', 'session.status_terminated')]
    session = ant('beta:sessions', 'retrieve', '--session-id', sid)
    uses = {e['id']: e for e in events if e['type'] == 'agent.tool_use'}
    searches = [e['input'] for e in uses.values() if 'query.py' in json.dumps(e.get('input'))]
    # Evidence = every tool result holding library-search JSON. The agent often writes
    # query.py output to a file and cats it later, so don't key on the command text.
    retrieved = []
    for e in events:
        if e['type'] == 'agent.tool_result':
            t = ''.join(c.get('text', '') for c in e.get('content') or [])
            if '"results"' in t and '"answer"' in t:
                retrieved.append(t)
    reply = '\n\n'.join(''.join(c.get('text', '') for c in e['content']) for e in events if e['type'] == 'agent.message')
    blocks = re.findall(r'```json\s*(.*?)```', reply, re.S)
    try:
        parsed = {str(r['id']).strip().rstrip('.'): r for r in json.loads(blocks[-1])}
    except (IndexError, ValueError, KeyError, TypeError):
        parsed = {}
    return {'session_id': sid, 'status': session['status'], 'stop_reason': end[-1].get('stop_reason') if end else 'timeout',
            'cost_cents': int(session['usage']['list_cost']['amount']),
            'searches': searches, 'retrieved': retrieved, 'reply': reply, 'parsed': parsed}


JUDGE_SCHEMA = {
    'type': 'object', 'additionalProperties': False,
    'required': ['claims', 'faithful', 'notes'],
    'properties': {
        'claims': {'type': 'array', 'items': {
            'type': 'object', 'additionalProperties': False, 'required': ['claim', 'supported', 'evidence'],
            'properties': {'claim': {'type': 'string'}, 'supported': {'type': 'boolean'}, 'evidence': {'type': 'string'}}}},
        'faithful': {'type': 'boolean'},
        'notes': {'type': 'string'}}}

JUDGE_SYSTEM = """You grade an RFI draft answer for faithfulness to its sources.
Split the draft into its factual claims (capabilities, numbers, named partners, certifications, regulatory statements, comparisons).
A claim is supported only if a library record in RETRIEVED states it or directly implies it. Framing and selling language with no factual content is not a claim.
For each claim give a short quote or record title as evidence, or "none".
faithful is true only if every claim is supported. Mention in notes any claim that contradicts APPROVED (the answer the company actually submitted), but grade support against RETRIEVED only."""


def judge(q, draft, retrieved):
    body = (f'QUESTION:\n{q["question"]}\n\nDRAFT:\n{draft}\n\nAPPROVED:\n{q.get("approved_answer") or "(none)"}\n\n'
            f'RETRIEVED (library search output from this session):\n' + ('\n\n---\n\n'.join(retrieved) or '(no searches ran)'))
    r = ant('messages', 'create', '--model', JUDGE_MODEL, '--max-tokens', '8000', '--system', JUDGE_SYSTEM,
            '--message', json.dumps({'role': 'user', 'content': body}),
            '--output-config', json.dumps({'effort': 'medium', 'format': {'type': 'json_schema', 'schema': JUDGE_SCHEMA}}))
    u = r['usage']
    cost = (u['input_tokens'] * JUDGE_PRICE[0] + u['output_tokens'] * JUDGE_PRICE[1]) / 1e6
    verdict = json.loads(next(c['text'] for c in r['content'] if c['type'] == 'text'))
    return verdict, round(cost * 100, 2)


def grade(q, ans, retrieved):
    triage = (ans or {}).get('triage')
    triage = triage.strip().lower() if isinstance(triage, str) else None
    route = (ans or {}).get('route') or ''
    draft = (ans or {}).get('draft') or ''
    g = {'id': q['id'], 'key': q['triage'], 'agent_triage': triage, 'route': route, 'draft': draft,
         'sources': (ans or {}).get('sources'), 'answered': ans is not None,
         'triage_ok': triage == q['triage']}
    if q['triage'] in ('amber', 'red'):
        g['route_ok'] = any(t.lower() in route.lower() for t in q['route_any'])
    if q['triage'] == 'red':
        g['red_safe'] = not draft.strip()
    if draft.strip():
        g['judge'], g['judge_cost_cents'] = judge(q, draft, retrieved)
        g['faithful'] = g['judge']['faithful']
    return g


def rate(rows, key):
    vals = [r[key] for r in rows if key in r]
    return {'pass': sum(vals), 'n': len(vals), 'rate': round(sum(vals) / len(vals), 3) if vals else None}


def summarize(grades):
    s = {'triage': rate(grades, 'triage_ok'),
         'triage_by_key': {c: rate([g for g in grades if g['key'] == c], 'triage_ok') for c in ('green', 'amber', 'red')},
         'confusion': {}, 'routing': rate(grades, 'route_ok'), 'red_safety': rate(grades, 'red_safe'),
         'faithfulness': rate(grades, 'faithful'),
         'unsupported_claims': sum(sum(not c['supported'] for c in g['judge']['claims']) for g in grades if 'judge' in g),
         'unparsed': [g['id'] for g in grades if not g['answered']]}
    for g in grades:
        k = f'{g["key"]}->{g["agent_triage"]}'
        s['confusion'][k] = s['confusion'].get(k, 0) + 1
    return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--set', default=os.path.join(HERE, 'questions.json'))
    ap.add_argument('--limit', type=int, help='first N questions only (trial)')
    ap.add_argument('--batch-size', type=int, default=6, help='questions per agent session')
    ap.add_argument('--budget-cents', type=int, default=500, help='hard spend cap per session')
    ap.add_argument('--version', type=int, help='agent version to pin; default = latest')
    ap.add_argument('--regrade', help='re-run grading on a saved results file, no agent sessions')
    a = ap.parse_args()

    if a.regrade:
        res = json.load(open(a.regrade))
        qs = {q['id']: q for q in res['questions']}
        for b in res['batches']:  # re-read the sessions so extraction fixes apply
            b.update({k: v for k, v in collect(b['session_id']).items() if k != 'cost_cents'})
        res['grades'] =[grade(qs[i], b['parsed'].get(i), b['retrieved']) for b in res['batches'] for i in b['ids']]
    else:
        qset = json.load(open(a.set))
        qs_list = qset['questions'][:a.limit] if a.limit else qset['questions']
        if not qs_list:
            sys.exit(f'{a.set} has no questions yet.')
        version = a.version or ant('beta:agents', 'retrieve', '--agent-id', AGENT_ID)['version']
        res = {'date': datetime.date.today().isoformat(), 'set': qset['set'], 'set_file': os.path.relpath(a.set, HERE),
               'answer_key_verified_by': qset.get('answer_key_verified_by'),
               'agent': {'id': AGENT_ID, 'version': version}, 'environment_id': ENV_ID, 'vault_id': VAULT_ID,
               'judge_model': JUDGE_MODEL, 'questions': qs_list, 'batches': [], 'grades': []}
        for n in range(0, len(qs_list), a.batch_size):
            batch = qs_list[n:n + a.batch_size]
            print(f'session {n // a.batch_size + 1}: {", ".join(q["id"] for q in batch)}', flush=True)
            b = run_batch(batch, version, a.budget_cents, f'AF-50 {qset["set"]} {n // a.batch_size + 1}')
            b['ids'] = [q['id'] for q in batch]
            res['batches'].append(b)
            res['grades'] += [grade(q, b['parsed'].get(q['id']), b['retrieved']) for q in batch]
            print(f'  {b["status"]} {b["stop_reason"]}  ${b["cost_cents"] / 100:.2f}', flush=True)

    res['summary'] = summarize(res['grades'])
    res['cost_usd'] = {'agent': sum(b['cost_cents'] for b in res['batches']) / 100,
                       'judge': round(sum(g.get('judge_cost_cents', 0) for g in res['grades']) / 100, 2)}
    out = a.regrade or os.path.join(HERE, 'results', f'{res["date"]}-{res["set"]}-v{res["agent"]["version"]}'
                                    f'{"-trial" + str(a.limit) if a.limit else ""}.json')
    json.dump(res, open(out, 'w'), indent=1, ensure_ascii=False)
    print(json.dumps({'summary': res['summary'], 'cost_usd': res['cost_usd']}, indent=1))
    print(f'wrote {out}')


if __name__ == '__main__':
    main()
