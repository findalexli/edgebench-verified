#!/usr/bin/env python3
"""Print repaired-set differences between variants (from eval_lean.py structured reports)."""
import json, sys, gzip, os
def rep(v):
    p = f'out/report_{v}.json'; t = (gzip.open(p + '.gz', 'rt', encoding='utf-8') if os.path.exists(p + '.gz') else open(p, encoding='utf-8')).read(); return json.loads(t[t.index('{'):t.rindex('}')+1])['metrics']
base = set(rep('T')['repaired'])
for v in sys.argv[1:]:
    m = rep(v); s = set(m['repaired'])
    print(f'{v}: repaired={len(s)} lost_vs_T={sorted(base - s)} gained_vs_T={sorted(s - base)}')
