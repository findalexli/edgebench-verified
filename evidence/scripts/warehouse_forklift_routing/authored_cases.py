#!/usr/bin/env python3
"""Write authored tester fixtures to inputs/authored/ with oracle predictions (prompt and CodeChef rules).
Positive family: cells ordered by (r+c, r, c); good j stored in cell j; arrivals n..3,1,2."""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import oracle_sim as O
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'inputs', 'authored'); os.makedirs(OUT, exist_ok=True)


def diag(R, C):
    cells = sorted(((r, c) for r in range(R) for c in range(C) if (r, c) != (0, 0)), key=lambda p: (p[0] + p[1], p[0], p[1]))
    n = len(cells); cell = {j + 1: cells[j] for j in range(n)}
    arr = list(range(n, 2, -1)) + [1, 2]

    def path(p):  # monotone route of strictly nearer cells to a predecessor, then direction
        r, c = p
        if c == 0:
            return ['S'] * (r - 1), 'S'
        return ['S'] * r + ['E'] * (c - 1), 'E'
    inv = {'S': 'N', 'E': 'W'}
    s = []
    for g in arr:
        mv, d = path(cell[g]); s += ['P'] + mv + ['U' + d] + [inv[m] for m in reversed(mv)]
    for g in range(1, n + 1):
        mv, d = path(cell[g]); s += mv + ['L' + d] + [inv[m] for m in reversed(mv)] + ['D']
    return arr, ''.join(s)


fixtures = {}
def add(name, cases, lines):
    inp = "%d\n" % len(cases) + ''.join("%d %d\n%s\n" % (R, C, ' '.join(map(str, a))) for R, C, a in cases)
    out = '\n'.join(lines) + '\n'
    open(os.path.join(OUT, name + '.in'), 'w').write(inp); open(os.path.join(OUT, name + '.out'), 'w').write(out)
    res = {}
    for mode in ('prompt', 'original'):
        ok, v = O.score_file(inp, out, mode)
        res[mode] = ("Score = %.1f" % float(v)) if ok else ("FAIL " + v)
        if ok: res[mode + '_exact'] = str(v)
    fixtures[name] = res

sizes = [(6, 6), (6, 20), (20, 6), (20, 20), (7, 11)]
D = {rc: diag(*rc) for rc in sizes + [(6, 6)]}
add('pos_mixed', [(R, C, D[(R, C)][0]) for R, C in sizes], [D[rc][1] for rc in sizes])
a66, s66 = D[(6, 6)]
add('pos_6x6x5', [(6, 6, a66)] * 5, [s66] * 5)
add('pos_detour', [(6, 6, a66)] * 5, ['EW' + s66] * 5)
# empty forklift walks over occupied cells after all goods are stored, then proceeds
n = 35; split = s66.index('D') ; pre = s66[:s66.index('L')]  # all placements done before first L
idx = len(pre) - (len(pre) - len(pre.rstrip('NSEW')))
walk = 'SSSSNNNN'  # (0,0)->(4,0) and back over stored goods
add('relaxed_walk_over', [(6, 6, a66)] * 5, [pre + walk + s66[len(pre):]] * 5)
neg = {'neg_oob': 'N', 'neg_P_away': 'EP', 'neg_PP': 'PP', 'neg_D_early': 'PD', 'neg_D_empty': 'D',
       'neg_carry_into_occupied': 'PUEPE', 'neg_U_occupied': 'PUEPUE', 'neg_trunc_L': 'L', 'neg_unknown': 'X'}
for k, pfx in neg.items():
    add(k, [(6, 6, a66)] * 5, [pfx] + [s66] * 4)
add('neg_missing_final_D', [(6, 6, a66)] * 5, [s66[:-1]] + [s66] * 4)
# wrong dispatch order: swap retrieval of goods 1 and 2 (both adjacent to entrance)
s_bad = s66.replace('LED', '#', 1).replace('LSD', 'LED', 1).replace('#', 'LSD', 1)
add('neg_wrong_order', [(6, 6, a66)] * 5, [s_bad] + [s66] * 4)
add('neg_empty_output', [(6, 6, a66)] * 5, [''] * 5)
json.dump(fixtures, open(os.path.join(OUT, 'predictions.json'), 'w'), indent=1)
for k, v in fixtures.items(): print(k, v)
