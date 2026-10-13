#!/usr/bin/env python3
"""Summarize paired v1/v2 grader reports (out/report_<ver>_<var>.json[.gz]) for results.md."""
import gzip, json, re, sys
from fractions import Fraction
from pathlib import Path
OUT = Path(__file__).resolve().parent / 'out'
def load(ver, var):
    for p in (OUT / f'report_{ver}_{var}.json', OUT / f'report_{ver}_{var}.json.gz'):
        if p.exists():
            t = (gzip.open(p, 'rt', encoding='utf-8') if p.suffix == '.gz' else open(p, encoding='utf-8')).read()
            m = re.search(r'>>>>> Start Structured Result\n(.*)\n>>>>> End Structured Result', t, re.S)
            return json.loads(m.group(1) if m else t)
    return None
cases = sys.argv[1:] or ['orig', 'A', 'BAD', 'T', 'S', 'W']
rep = {}
print('| variant | version | lake build | raw score (= normalized, linear 0..1) | repaired / targets | type_changed | disappeared |')
print('|---|---|---|---|---|---|---|')
for var in cases:
    for ver in ('v1', 'v2'):
        r = load(ver, var); rep[ver, var] = r
        if r is None: print(f'| {var} | {ver} | not run | | | | |'); continue
        if 'lake_build_rc' in r:
            print(f'| {var} | {ver} | FAILED rc={r["lake_build_rc"]} | no score (eval not reached) | – | – | – |'); continue
        m = r['metrics']; n, d = m['repaired_count'], m['baseline_total']
        print(f'| {var} | {ver} | ok | {r["score"]:.6f} ({n}/{d}) | {n}/{d} | {m["type_changed_count"]} | {m["disappeared_count"]} |')
print()
for var in cases:
    a, b = rep.get(('v1', var)), rep.get(('v2', var))
    if a and b and 'metrics' in a and 'metrics' in b:
        print(f'{var}: v1 repaired = {sorted(a["metrics"]["repaired"])}')
        print(f'{var}: v2 repaired = {sorted(b["metrics"]["repaired"])}')
        print(f'{var}: v1 type_changed = {a["metrics"]["type_changed"]}; v2 type_changed = {b["metrics"]["type_changed"]}')
sets = {v: frozenset(rep[('v2', v)]['metrics']['repaired']) for v in ('T', 'S', 'W') if rep.get(('v2', v)) and 'metrics' in rep[('v2', v)]}
if sets: print('v2 repaired sets identical across T/S/W:', len(set(sets.values())) == 1)
sets1 = {v: frozenset(rep[('v1', v)]['metrics']['repaired']) for v in ('T', 'S', 'W') if rep.get(('v1', v)) and 'metrics' in rep[('v1', v)]}
if sets1: print('v1 repaired sets identical across T/S/W:', len(set(sets1.values())) == 1, {k: len(v) for k, v in sets1.items()})
