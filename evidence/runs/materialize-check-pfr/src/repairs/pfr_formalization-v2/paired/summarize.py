#!/usr/bin/env python3
"""Summarize the paired runs: one row per (variant, version) from report_*.json and listdecl_*.txt.

Usage: summarize.py V1_OUT_DIR V2_OUT_DIR
"""
import json
import re
import sys
from pathlib import Path

FIVE = ['torsion_free_doubling', 'torsion_dist_shrinking', 'app_ent_PFR', "PFR_projection'", 'PFR_projection']
LINE = re.compile(r'^(?:info: ListDeclAxiom\.lean:\d+:\d+: )?(OK|BAD) (\S+) : type=(.*?); (?:axioms|unexpected)=')


def report(p):
    s = p.read_text()
    j = s.find('{', max(s.find('>>>>> Start'), 0))
    return json.loads(s[j:s.rfind('}') + 1])


def listing(p):
    out = {}
    for ln in p.read_text().splitlines():
        m = LINE.match(ln)
        if m:
            out[m.group(2)] = (m.group(1), 'sorry)' in m.group(3) or 'sorry) ' in m.group(3))
    return out


print('| variant | version | score | repaired / targets | type_changed | disappeared | new BAD declarations '
      '| five targets: BAD / type shows `sorry` | added lemmas (status) | HASH checks |')
print('|---|---|---|---|---|---|---|---|---|---|')
for variant in ['starter', 'T', 'D', 'BAD']:
    for ver, d in zip(['v1', 'v2'], sys.argv[1:3]):
        d = Path(d)
        r = report(d / f'report_{ver}_{variant}.json')
        m = r['metrics']
        L = listing(d / f'listdecl_{ver}_{variant}.txt')
        five_bad = sum(L[n][0] == 'BAD' for n in FIVE)
        five_sorry = sum(L[n][1] for n in FIVE)
        added = ', '.join(f'{n} {L[n][0]}' for n in sorted(L) if n.startswith('ebv_') and '._auto_' not in n) or '–'
        hc = ', '.join(f'{k}={v}' for k, v in m['hash_checks'].items())
        print(f"| {variant} | {ver} | {r['score']} | {m['repaired_count']}/{m['baseline_total']} "
              f"| {m['type_changed_count']} | {m['disappeared_count']} | {', '.join(m['new_bad_declarations']) or '–'} "
              f"| {five_bad}/5, {five_sorry}/5 | {added} | {hc} |")
