#!/usr/bin/env python3
from fractions import Fraction as F
S = lambda f: {l.split()[0] for l in open(f) if l.strip()}
sorry_ty, contra, dup = S('sorry_type_targets.txt'), S('contradictory_targets.txt'), S('dup_extra_targets.txt')
false_main = {'Chapter11.MajorizesOn.anti_symm', 'Chapter11.PiecewiseConstantOn.div'}
observed = {'Section_4_1.Int.equivInt._proof_1'}  # lost in every honest style tried (binder names / dedup)
for name, s in [('A sorry-typed', sorry_ty), ('B P/notP hypothesis-dropped', contra), ('C duplicate copies', dup)]:
    print(f'{name}: {len(s)}')
lb = sorry_ty | contra | false_main
print('lower bound A+B+false-main:', len(lb), f'ceiling {2901-len(lb)}/2901 = {float(F(2901-len(lb),2901)):.4%}')
lb2 = lb | dup | observed
print('with C + observed equivInt._proof_1:', len(lb2), f'ceiling {2901-len(lb2)}/2901 = {float(F(2901-len(lb2),2901)):.4%}')
