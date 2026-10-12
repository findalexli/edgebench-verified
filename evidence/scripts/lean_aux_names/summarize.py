#!/usr/bin/env python3
"""Summarize eval_lean.py structured reports: overall metrics + per-target status for Section_4_1."""
import json, sys, gzip, os, re
def load(p):
    t = (gzip.open(p + '.gz', 'rt', encoding='utf-8') if os.path.exists(p + '.gz') else open(p, encoding='utf-8')).read()
    a = t.index('{'); b = t.rindex('}')
    return json.loads(t[a:b+1])
AUX = re.compile(r'\.(_proof_\d+|_simp_\d+|match_\d+|eq_\d+|_sunfold|_unsafe_rec)$')
for v in sys.argv[1:]:
    r = load(f'out/report_{v}.json'); m = r['metrics']
    print(f'## variant {v}: score={r["score"]:.6f} summary: {r["summary"]}')
    print(f'   disappeared={m["disappeared"]} type_changed={m["type_changed"]}')
    print(f'   new_bad={m["new_bad_declarations"]}')
    rows = [d for d in r['details'] if d['name'].startswith('Section_4_1.') and d['weight'] > 0]
    for d in sorted(rows, key=lambda d: d['name']):
        if d['status'] == 'PASSED' or 'still bad' not in d['message']:
            tag = 'AUX ' if AUX.search(d['name']) else 'MAIN'
            print(f'   {tag} {d["status"]:6} {d["name"]}: {d["message"][:160]}')
    print(f'   (Section_4_1 targets: {len(rows)}; others listed only if PASSED or not "still bad")')
