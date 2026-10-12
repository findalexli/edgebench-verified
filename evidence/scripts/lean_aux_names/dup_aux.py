#!/usr/bin/env python3
"""Count baseline aux targets that share parent AND exact type text with another aux target
(copies of the same sorried proof; a proved version may be deduplicated into one aux lemma)."""
import re, collections, sys
pat = re.compile(r'BAD (\S+) : type=(.*); unexpected=\[(.*?)\]; all=\[(.*?)\]$')
T = {}
for line in open('../lean_analysis_proofs/baseline-ListDeclAxiom.out', encoding='utf-8'):
    m = pat.search(line.rstrip('\n'))
    if m and 'sorryAx' in m.group(4): T[m.group(1)] = m.group(2)
aux = {l.split()[1] for l in open('where_aux.out') if l.startswith('AUXMOD')}
sorry_ty = {l.strip() for l in open('sorry_type_targets.txt')}
g = collections.defaultdict(list)
for n in aux:
    if re.search(r'\._proof_\d+$', n): g[(n.rsplit('.', 1)[0], T[n])].append(n)
extra = [sorted(v, key=lambda s: int(s.rsplit('_', 1)[1]))[1:] for v in g.values() if len(v) > 1]
extra = [x for e in extra for x in e]
print('duplicate-type _proof groups:', sum(1 for v in g.values() if len(v) > 1), '; extra copies:', len(extra),
      '; of which not sorry-typed:', len([x for x in extra if x not in sorry_ty]))
if '-v' in sys.argv:
    for x in sorted(extra): print('  DUP', x)
