"""Turn analyze.py's JSON into RESULTS.md: one row per task, recorded vs v1 regrade vs v2 regrade.

Usage: python3 table.py ANALYSIS.json RESULTS.md
The run score is the normalized score when the task has a rescale, otherwise the raw selected score
(marked "raw"). A v1 regrade that disagrees with the recorded score on a round is counted as a mismatch.
"""
import json, math, sys

d = json.load(open(sys.argv[1]))


def fmt(b):
    s, n = b.get('best_score'), b.get('norm')
    if s is None or (isinstance(s, float) and math.isinf(s)) or b.get('best_valid') is False:
        return 'no valid score'
    if n is not None:
        return f"{n:.2f} ({b['best_round']})"
    return f"{s:.6g} raw ({b['best_round']})"


rows = ['| Task | Policy | Graded / recorded rounds | Recorded | v1 regrade | v2 regrade | v1 ≠ recorded | v2 ≠ v1 |',
        '|---|---|---:|---|---|---|---:|---:|']
for t, r in d.items():
    mism = diff = 0
    for p in r['per']:
        v1, v2 = p['v1'], p['v2']
        if v1 and p['orig_score'] is not None and v1['scores'][0] != p['orig_score']:
            mism += 1
        base = (v1['scores'][0], v1['valid'][0]) if v1 else (p['orig_score'], p['orig_valid'])  # V2_ONLY: recorded
        if v2 and (v2['scores'][0], v2['valid'][0]) != base:
            diff += 1
    sel = r['sel_mean']
    rows.append(f"| {t} | {r['policy']} | {r['n_graded']} / {r['n_history']} | {fmt(r['orig_recorded'])} | "
                f"{fmt(sel['v1'])} | {fmt(sel['v2'])} | {mism} | {diff} |")
open(sys.argv[2], 'w').write('\n'.join(rows) + '\n')
print('\n'.join(rows))
