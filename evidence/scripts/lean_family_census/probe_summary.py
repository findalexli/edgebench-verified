#!/usr/bin/env python3
"""Summarize AuxProbe output: which aux targets carry a sorry hole in their own value (fragile: an honest
fill re-elaborates them, so numbering/dedup/binders may change), which belong to a def/instance parent
with any direct hole (exposed to renumbering), and which reach sorry only transitively (stable).
Usage: probe_summary.py <aux_probe.out> [weights.json]"""
import re, sys, collections, json
rows = {}
for l in open(sys.argv[1], encoding='utf-8'):
    m = re.match(r'AUXPROBE (\S+) module=(\S+) kind=(\S+) parent_kind=(\S+) own_value_sorry=(\S+) parent_value_sorry=(\S+) type_sorry=(\S+)', l)
    if m: rows[m.group(1)] = dict(module=m.group(2), kind=m.group(3), pk=m.group(4), own=m.group(5) == 'true', pown=m.group(6) == 'true', ty=m.group(7) == 'true')
par = lambda n: n.rsplit('.', 1)[0] if not re.search(r'\.(eq_\d+|eq_def|congr_simp)$', n) else n.rsplit('.', 1)[0]
holey = collections.defaultdict(bool)
for n, r in rows.items():
    p = n.rsplit('.', 1)[0]
    if r['own'] or (r['pown'] and r['pk'] != 'theorem'): holey[p] = True
c = collections.Counter()
for n, r in rows.items():
    p = n.rsplit('.', 1)[0]
    cls = ('own-hole' if r['own'] else 'sibling/parent-hole' if holey[p] and r['pk'] != 'theorem' else
           'transitive-of-theorem-parent' if r['pk'] == 'theorem' else 'transitive-only')
    r['cls'] = cls; c[(cls, r['pk'])] += 1
print('aux probed', len(rows))
for k, v in sorted(c.items()): print(f'  {k[0]:32s} parent_kind={k[1]:10s} {v}')
fr = [n for n, r in rows.items() if r['cls'] in ('own-hole', 'sibling/parent-hole')]
print('fragile (own hole or same-parent hole, non-theorem parent):', len(fr))
print('type contains sorryAx:', sum(r['ty'] for r in rows.values()))
if '-v' in sys.argv:
    for n in sorted(fr): print('  FRAGILE', n, rows[n]['module'])
