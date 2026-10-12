#!/usr/bin/env python3
"""Find baseline aux targets of one parent whose type is literally P and another's is ¬P
(after the shared ∀-prefix): the sorried hole dropped the case hypothesis, so the stated aux
proposition is refutable and any honest proof must change it."""
import re, collections
pat = re.compile(r'BAD (\S+) : type=(.*); unexpected=\[(.*?)\]; all=\[(.*?)\]$')
T = {}
for line in open('../lean_analysis_proofs/baseline-ListDeclAxiom.out', encoding='utf-8'):
    m = pat.search(line.rstrip('\n'))
    if m and 'sorryAx' in m.group(4): T[m.group(1)] = re.sub(r'\s+', ' ', m.group(2))
aux = [l.split()[1] for l in open('where_aux.out') if l.startswith('AUXMOD')]
def split(t):
    m = re.match(r'^((?:∀ [^,]*, )*)(.*)$', t)
    return m.group(1), m.group(2)
byp = collections.defaultdict(list)
for n in aux: byp[n.rsplit('.', 1)[0]].append(n)
hits = set()
for p, ns in byp.items():
    bodies = {n: split(T[n])[1] for n in ns}
    for a in ns:
        for b in ns:
            if bodies[a] == '¬' + bodies[b] or bodies[a] == '¬(' + bodies[b] + ')':
                hits.update([a, b])
print('aux targets in P / ¬P pairs:', len(hits))
for h in sorted(hits): print('  ', h, ':', T[h][:110])
