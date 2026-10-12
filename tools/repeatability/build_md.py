#!/usr/bin/env python3
"""Write paired-repeatability.md from digest.json (made by build_report.py) plus notes.json."""
import json, math, sys
S = str(__import__('pathlib').Path(__file__).resolve().parent)
import os
W = os.environ.get('EBV_REPEAT_WORK', str(__import__('pathlib').Path(__file__).resolve().parents[2] / '.internal' / 'repeatability-work'))
D = json.load(open(f'{W}/digest.json'))
NOTES = json.load(open(f'{S}/notes.json'))  # {"intro": [...], "task": {task: text}, "limits": [...], "jobs": [...]}

def pct(x):
    if x is None:
        return '–'
    if math.isinf(x):
        return 'inf'
    return f'{100 * x:.2f}%'

L = ['# Paired evaluation: repeatability study', '']
L += NOTES['intro'] + ['']

n_arms = n_exec = n_stable = n_3 = 0
flips = []
tab = ['| task | arms | arms with 3 runs | verdict stable in every run? | max relative score spread (v1 / v2) | notes |', '| --- | ---: | ---: | --- | --- | --- |']
for t, d in D.items():
    if 'skipped' in d:
        tab.append(f"| {t} | {len(d['arms'])} | 0 | not run | – | {d['skipped']} |"); continue
    arms = [a for a in d['arms'] if not a['derived']]
    der = len(d['arms']) - len(arms)
    n_arms += len(d['arms']); n_exec += len(arms)
    st = sum(a['stable'] for a in arms); n_stable += st
    full = sum(1 for a in arms if len(a['runs']) == 3); n_3 += full
    def mx(key):
        v = [a[key]['rel'] for a in arms if a[key]]
        return max(v) if v else None
    for a in arms:
        if not a['stable']:
            flips.append((t, a))
    ok = 'yes' if st == len(arms) else f'**no ({len(arms) - st} arm(s) changed)**'
    if full < len(arms):
        ok += f' (only {full}/{len(arms)} arms have 3 runs)'
    note = NOTES['task'].get(t, '')
    if der:
        note = (note + ' ' if note else '') + f'{der} derived arm(s) not executed.'
    tab.append(f"| {t} | {len(d['arms'])} | {full} | {ok} | {pct(mx('v1_spread'))} / {pct(mx('v2_spread'))} | {note} |")

L += ['## Totals', '']
L += [f'- Executed arms compared: **{n_exec}** (of {n_arms} rows in `paired-results.csv` for the tasks that were run; '
      f'openrct2 and derived rows are excluded).',
      f'- Arms with all 3 runs: **{n_3}** of {n_exec}.',
      f'- **Verdicts changed across runs: {n_exec - n_stable} of {n_exec} arms.**', '']
L += NOTES.get('totals_extra', []) + ['']
L += ['## Per task', '', 'Relative spread = (max − min) / |mean| over the runs of one arm and one version; the column shows '
      'the largest value over the task\'s arms. Timing-based scores (exchange, ffmpeg, integer codec) are marked in the arm table below.', '']
L += tab + ['']

L += ['## Arms whose verdict changed', '']
if not flips:
    L += ['None. In every executed arm the v1 verdict and the v2 verdict were identical in all available runs.', '']
for t, a in flips:
    L += [f"### {t}: {a['arm']} ({a['role']})", '', '| run | v1 result | v2 result | v1 score | v2 score |', '| --- | --- | --- | --- | --- |']
    for r in sorted(a['per'], key=int):
        p = a['per'][r]
        L.append(f"| {r} | {p[0]} | {p[1]} | {p[2]} | {p[3]} |")
    L += [''] + NOTES.get('flip', {}).get(f"{t}|{a['arm']}", []) + ['']

L += ['## Score spread per arm (arms with any numeric spread)', '', '| task | arm | role | timing-based | v1 min–max (rel) | v2 min–max (rel) |', '| --- | --- | --- | --- | --- | --- |']
for t, d in D.items():
    if 'skipped' in d:
        continue
    for a in d['arms']:
        sp = [a[k] for k in ('v1_spread', 'v2_spread')]
        if not any(s and s['max'] != s['min'] for s in sp) and not a['timing']:
            continue
        f = lambda s: '–' if not s else f"{s['min']:.6g}–{s['max']:.6g} ({pct(s['rel'])})"
        L.append(f"| {t} | {a['arm']} | {a['role']} | {'yes' if a['timing'] else 'no'} | {f(sp[0])} | {f(sp[1])} |")
L += ['']
L += ['## Jobs', ''] + NOTES['jobs'] + ['']
L += ['## Limits', ''] + NOTES['limits'] + ['']
open(__import__('pathlib').Path(__file__).resolve().parents[2] / 'paired-repeatability.md', 'w').write('\n'.join(L))
print(f'exec {n_exec} stable {n_stable} full {n_3} flips {len(flips)}')
