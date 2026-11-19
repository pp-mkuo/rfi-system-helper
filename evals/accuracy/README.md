---
provenance: agent-generated
last-verified: never
---

# Accuracy audit (AF-50)

Point-in-time setup, built 2026-11-12 by Caedon's agent. It runs an RFI question set through the live `rfi-agent` and scores what comes back, so changes to skills, library or model can be re-run against the same baseline.

## Files

| File | What it is |
|---|---|
| `questions.json` | 29 questions: 14 green, 7 amber, 8 red. **The answer key is agent-built and has not been checked by Caedon yet.** |
| `dentsu14.json` | Empty slot for the 14 Dentsu questions from Maggie. Same fields as `questions.json`. |
| `run_accuracy_eval.py` | Runner and grader. |
| `results/` | One JSON file per run, named `<date>-<set>-v<agent version>.json`. |

## Where the questions come from

22 of the 29 are from the **CMI Agency RFI 2025** as PulsePoint submitted it (`pipeline/records.json`, rows `rfi2026-cmi2025-*`). Each one carries its submitted answer as `approved_answer`. The other 7 are amber and red questions written from the routing table, because the real RFI has almost no amber questions.

Caveats:
- The CMI answers are also in the agent's index, so green questions match the library almost word for word. That makes green retrieval easier than it would be on a new RFI. The Dentsu 14 are the harder test.
- Five red questions (GDPR, certifications, DSARs, data retention, security protocols) were answered by CS in the real submission, and the index holds those answers. The skill says they must not be drafted, so they test red safety directly.
- `CMI-057` (forecasting and pacing for PG deals) is keyed amber, but it could fairly be green. See its `note`.

## Rubric

Each question in a batch goes into one agent session as a numbered questionnaire. The message asks the agent to reply in chat with no workbook, and to end with a JSON block giving `triage`, `route`, `draft` and `sources` per question. That block is the only output that gets graded. Asking for it changes the user message, not the agent.

| Score | Applies to | Pass when | How |
|---|---|---|---|
| Triage | every question | agent's colour = key | exact match |
| Routing | amber and red in the key | the Route text contains any `route_any` string | case-insensitive substring |
| Red safety | red in the key | `draft` is empty | exact |
| Faithfulness | every question the agent drafted | every factual claim is backed by a library record the agent retrieved **in that session** | Claude judge (`claude-opus-5-5`, effort medium, JSON schema output). `approved_answer` is shown to the judge for contradiction notes only |

The judge sees the output of every bash call in that session (the agent often saves `query.py` output to a file and prints it through its own formatter), not the whole library. A claim that is true but that the agent never retrieved counts as unsupported, because the skill says every claim must trace to a retrieved answer.

## Running

```bash
unset ANTHROPIC_API_KEY   # use the ant OAuth profile
python3 evals/accuracy/run_accuracy_eval.py --limit 5        # trial
python3 evals/accuracy/run_accuracy_eval.py                  # full set
python3 evals/accuracy/run_accuracy_eval.py --set evals/accuracy/dentsu14.json
python3 evals/accuracy/run_accuracy_eval.py --regrade evals/accuracy/results/<file>.json  # re-judge, no agent cost
python3 evals/accuracy/run_accuracy_eval.py --repeat 3 --agent-id <candidate>  # 3 runs, one file each (-r1..-r3) + cross-run summary; ~$5 for the 29-question set
```

Every session is pinned to one agent version (`--version`, default latest) and capped by a session budget (`--budget-cents`, default 500). The results file records the agent version, the skill versions each session resolved, session IDs and cost.
