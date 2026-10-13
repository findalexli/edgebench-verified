#!/usr/bin/env python3
"""Write data/paired-repeatability.md from digest.json (made by build_report.py) plus notes.json."""
import json, math, sys
S = str(__import__('pathlib').Path(__file__).resolve().parent)
import os
W = os.environ.get('EBV_REPEAT_WORK', str(__import__('pathlib').Path(__file__).resolve().parents[2] / '.internal' / 'repeatability-work'))
D = json.load(open(f'{W}/digest.json'))
EXTRA = D.pop('_extra', [])
NOTES = json.load(open(f'{S}/notes.json'))  # {"intro": [...], "task": {task: text}, "limits": [...], "jobs": [...]}

def pct(x):
    if x is None:
        return '–'
    if math.isinf(x):
        return 'inf'
    return f'{100 * x:.2f}%'

L = ['# Side-by-side tests: are they repeatable?', '', '**How to read this file.** Each fixed task was tested side by side: the same test submissions were graded by the original grader (**v1**) and the fixed grader (**v2**). One test submission graded by both is an **arm**. A *trigger* shows the problem, a *valid control* is correct work that must keep its score, and an *invalid control* is wrong work that must stay rejected. The CSV columns use the same names.', '']
L += NOTES['intro'] + ['']

n_arms = n_exec = n_stable = n_3 = n_setup = n_setup3 = 0
flips = []
tab = ['| task | arms | arms with 3 runs | verdict stable in every run? | max relative score spread (v1 / v2) | notes |', '| --- | ---: | ---: | --- | --- | --- |']
for t, d in D.items():
    if 'skipped' in d:
        tab.append(f"| {t} | {len(d['arms'])} | 0 | not run | – | {d['skipped']} |"); continue
    nc = [a for a in d['arms'] if a.get('not_counted')]
    arms = [a for a in d['arms'] if not a['derived'] and not a.get('not_counted')]
    der = len(d['arms']) - len(arms) - len(nc)
    n_arms += len(d['arms']); n_exec += len(arms)
    st = sum(a['stable'] for a in arms); n_stable += st
    full = sum(1 for a in arms if len(a['runs']) == 3); n_3 += full
    n_setup += sum(a['role'] == 'setup' for a in arms)
    n_setup3 += sum(a['role'] == 'setup' and len(a['runs']) == 3 for a in arms)
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
    if nc:
        note = (note + ' ' if note else '') + f"{len(nc)} arm(s) not counted: {nc[0]['not_counted']}."
        n_arms -= len(nc)
    tab.append(f"| {t} | {len(d['arms'])} | {full} | {ok} | {pct(mx('v1_spread'))} / {pct(mx('v2_spread'))} | {note} |")

L += ['## Totals', '']
L += [f'- Executed arms compared: **{n_exec}** (of {n_arms} rows in `data/paired-results.csv` for the tasks that were run; '
      f'openrct2, derived rows and rows marked not counted in the table below are excluded).',
      f'- Of these, {n_setup} are setup runs that prepare an input (role `setup`), so graded comparisons: '
      f'**{n_exec - n_setup}**, of which **{n_3 - n_setup3}** have all 3 runs.',
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
L += ['## Supplementary jobs', '', NOTES.get('extra_intro', ''), '',
      '| task | job | what it adds | runs with results | labels compared | labels whose outcome changed | score spread (labels that moved, max relative) |',
      '| --- | --- | --- | --- | ---: | --- | --- |']
for e in EXTRA:
    ch = ', '.join(f"`{c['label']}`" for c in e['changed']) or 'none'
    sp = f"{len(e['spread'])} label(s), max {pct(max(s['rel'] for s in e['spread']))}" if e['spread'] else '–'
    err = f" (missing: {', '.join(str(r) for r in e['errors'])})" if e['errors'] else ''
    L.append(f"| {e['task']} | `{e['job']}` | {e['what']} | {', '.join(map(str, e['runs_ok']))}{err} | {e['labels']} | {ch} | {sp} |")
L += ['']
for e in EXTRA:
    for c in e['changed']:
        L += [f"**{e['job']}, `{c['label']}`:** " + '; '.join(f"run {r}: {v[0]}" + (f" ({v[1]})" if v[1] not in ('None', '') else '') for r, v in sorted(c['per'].items(), key=lambda x: int(x[0])))
              + '. ' + ' '.join(NOTES.get('extra_change', {}).get(f"{e['job']}|{c['label']}", [])), '']
L += ['## Jobs', ''] + NOTES['jobs'] + ['']
L += ['## Limits', ''] + NOTES['limits'] + ['']
open(__import__('pathlib').Path(__file__).resolve().parents[2] / 'data/paired-repeatability.md', 'w').write('\n'.join(L))
print(f'exec {n_exec} stable {n_stable} full {n_3} flips {len(flips)}')
