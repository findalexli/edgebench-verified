#!/usr/bin/env python3
"""Classify baseline sorry targets of lean_analysis_proofs (static, from the baseline dump)."""
import re, sys, collections
path = sys.argv[1] if len(sys.argv) > 1 else '../lean_analysis_proofs/baseline-ListDeclAxiom.out'
pat = re.compile(r'BAD (\S+) : type=(.*); unexpected=\[(.*?)\]; all=\[(.*?)\]$')
T = {}
for line in open(path, encoding='utf-8'):
    m = pat.search(line.rstrip('\n'))
    if m and 'sorryAx' in m.group(4):
        T[m.group(1)] = m.group(2)
AUX = re.compile(r'^(.*?)\.(_proof_\d+|_simp_\d+|_sunfold|_unsafe_rec|match_\d+|_sizeOf_\d+|congr_simp|eq_\d+|eq_def|_eq_\d+|proof_\d+)(\..*)?$')
aux = {}
for n in T:
    m = AUX.match(n)
    if m: aux[n] = (m.group(1), m.group(2))
kinds = collections.Counter(re.sub(r'\d+', 'N', k) for _, k in aux.values())
print('targets', len(T)); print('aux targets', len(aux)); print('aux kinds', dict(kinds))
par_in = sum(1 for p, _ in aux.values() if p in T)
print('aux whose parent is itself a target', par_in)
sorry_ty = [n for n, t in T.items() if re.search(r'\bsorry\b', t)]
sorry_aux = [n for n in sorry_ty if n in aux]
print('targets whose baseline TYPE text contains `sorry`', len(sorry_ty), '(aux:', len(sorry_aux), ')')
for n in sorry_ty[:400]:
    print('  SORRYTYPE', n)
if '-v' in sys.argv:
    for n, (p, k) in sorted(aux.items()): print('  AUX', n, 'parent_target=' + str(p in T))
