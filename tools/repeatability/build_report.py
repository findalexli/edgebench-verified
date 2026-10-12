#!/usr/bin/env python3
"""Build data/paired-repeatability.csv and a JSON digest (for the .md) from runs 1-3."""
import csv, json, math, sys, traceback
from collections import OrderedDict
sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parent))
import extract as X

R = X.R
rows = list(csv.DictReader(open(R / 'data/paired-results.csv')))
tasks = OrderedDict()
for r in rows:
    tasks.setdefault(r['task_id'], []).append(r)

TIMING = {'exchange_core_throughput', 'ffmpeg_swscale_reimplementation', 'integer_compression_codec'}
SKIP = {'openrct2_theme_park_ai': 'prompt-only repair, nothing executable'}

def fmt(x):
    if x is None:
        return ''
    if isinstance(x, float):
        if math.isinf(x):
            return 'inf'
        return f'{x:.10g}'
    return str(x)

out_rows, digest = [], {}
for task, arms in tasks.items():
    if task in SKIP:
        digest[task] = {'skipped': SKIP[task], 'arms': [{'arm': a['arm'], 'role': a['role']} for a in arms]}
        continue
    runs = {}
    for run in (1, 2, 3):
        try:
            runs[run] = X.extract(task, run)
        except Exception as e:
            runs[run] = {'_error': f'{type(e).__name__}: {e}'.splitlines()[0][:300]}
    td = {'runs_ok': [k for k, v in runs.items() if '_error' not in v],
          'errors': {k: v['_error'] for k, v in runs.items() if '_error' in v}, 'arms': []}
    if task == 'integer_compression_codec':
        td['in_run_repeats'] = {k: v.get('_repeat') for k, v in runs.items() if '_error' not in v}
    for i, a in enumerate(arms):
        per = {}
        for run in (1, 2, 3):
            x = runs[run]
            if '_error' in x or i not in x:
                continue
            v1r, v2r, v1s, v2s = x[i]
            if task == 'lean_analysis_proofs' and run == 1 and v1r == 'not run in this harness':
                v1r = f"published (reviewer native run): {a['v1_result']}"; v1s = float(a['v1_score']) if a['v1_score'] else None
            per[run] = (v1r, v2r, v1s, v2s)
            out_rows.append([task, a['arm'], a['role'], run, v1r, v2r, fmt(v1s), fmt(v2s)])
        derived = all(p[0] == 'derived (no execution)' for p in per.values()) and per
        sigs = {r: (p[0], p[1]) for r, p in per.items()}
        cmp_runs = [r for r in per if not (task == 'lean_analysis_proofs' and r == 1 and str(per[r][0]).startswith('published'))]
        # verdict stability: v2 verdict over all runs; v1 verdict over comparable runs
        v1set = {per[r][0] for r in cmp_runs}; v2set = {per[r][1] for r in per}
        stable = (len(v1set) <= 1 and len(v2set) <= 1)
        def spread(idx):
            vals = [per[r][idx] for r in per if isinstance(per[r][idx], (int, float)) and not math.isinf(per[r][idx])]
            if len(vals) < 2:
                return None
            lo, hi = min(vals), max(vals); mean = sum(vals) / len(vals)
            rel = (hi - lo) / abs(mean) if mean else (0.0 if hi == lo else float('inf'))
            return {'min': lo, 'max': hi, 'rel': rel, 'n': len(vals)}
        td['arms'].append({'arm': a['arm'], 'role': a['role'], 'runs': sorted(per), 'derived': bool(derived),
                           'stable': stable, 'per': {r: list(map(fmt, p)) if False else [p[0], p[1], fmt(p[2]), fmt(p[3])] for r, p in per.items()},
                           'v1_spread': spread(2), 'v2_spread': spread(3), 'timing': task in TIMING})
    digest[task] = td

with open(R / 'data/paired-repeatability.csv', 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['task_id', 'arm', 'role', 'run', 'v1_result', 'v2_result', 'v1_score', 'v2_score'])
    w.writerows(out_rows)
json.dump(digest, open(X.S / 'digest.json', 'w'), indent=1)
print('rows', len(out_rows))
for t, d in digest.items():
    if 'skipped' in d:
        print(t, 'SKIPPED'); continue
    n = len(d['arms']); st = sum(a['stable'] for a in d['arms'])
    print(f"{t}: runs {d['runs_ok']} errors {list(d['errors'])} stable {st}/{n}")
    for a in d['arms']:
        if not a['stable']:
            print('   FLIP', a['arm'][:60], a['per'])
