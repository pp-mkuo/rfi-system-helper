"""Offline check of the plain-comparison scoring. No API calls: python3 evals/accuracy/test_grading.py"""
import run_accuracy_eval as r

red = {'id': 'R', 'question': 'q', 'triage': 'red', 'route_any': ['rfi@internetbrands.com']}
amber = {'id': 'A', 'question': 'q', 'triage': 'amber', 'route_any': ['Jay Irwin', 'Doug Richards']}

g = r.grade(red, {'triage': 'Red', 'route': 'Route out: Security team — RFI@internetbrands.com', 'draft': None}, [])
assert g['triage_ok'] and g['route_ok'] and g['red_safe'] and 'faithful' not in g

g = r.grade(amber, {'triage': 'amber', 'route': 'SME: Walker Linares', 'draft': ''}, [])
assert g['triage_ok'] and not g['route_ok'] and 'red_safe' not in g

g = r.grade(red, None, [])  # agent's JSON block missing this question
assert not g['answered'] and not g['triage_ok'] and not g['route_ok'] and g['red_safe']

r.judge = lambda q, d, ret: ({'claims': [{'claim': 'x', 'supported': False, 'evidence': 'none'}], 'faithful': False, 'notes': ''}, 0)
g = r.grade(red, {'triage': 'green', 'route': None, 'draft': 'We hold SOC 2.'}, [])
assert not g['red_safe'] and g['faithful'] is False

s = r.summarize([g])
assert s['red_safety'] == {'pass': 0, 'n': 1, 'rate': 0.0} and s['unsupported_claims'] == 1 and s['confusion'] == {'red->green': 1}
print('ok')
