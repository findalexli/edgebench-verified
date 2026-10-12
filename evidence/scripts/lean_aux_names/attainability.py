#!/usr/bin/env python3
"""Ceiling arithmetic for lean_analysis_proofs aux-name scoring (exact fractions)."""
from fractions import Fraction as F
import re
T = 2901
aux = {l.split()[1]: l.split()[3].split('=')[1] for l in open('where_aux.out') if l.startswith('AUXMOD')}
sorry_ty = [l.strip() for l in open('sorry_type_targets.txt')]
parents_with_sorry_aux = {n.rsplit('.', 1)[0] for n in sorry_ty if n in aux}
siblings = [n for n in aux if n.rsplit('.', 1)[0] in parents_with_sorry_aux and n not in sorry_ty]
def_aux = [n for n, k in aux.items() if k == 'def']
print('aux targets', len(aux), 'def-parent', len(def_aux))
print('sorry-in-type targets (structurally unattainable):', len(sorry_ty), 'of which aux', sum(n in aux for n in sorry_ty))
print('parents with a sorry-typed aux:', len(parents_with_sorry_aux), '; their other aux targets (renumbering-exposed):', len(siblings))
for k, lost in [('sorry-typed only', len(sorry_ty)), ('+2 false statements', len(sorry_ty) + 2),
                ('+ renumbering-exposed siblings', len(sorry_ty) + 2 + len(siblings)),
                ('worst case: all def-parent aux + sorry-typed main + 2 false', len(def_aux) + 3 + 2)]:
    c = F(T - lost, T); print(f'{k:60s} lost={lost:4d} ceiling={T-lost}/{T} = {float(c):.4%}')
