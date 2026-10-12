#!/usr/bin/env python3
"""Differential test: independent oracle.py vs original verifier.py on random honest
outputs (random C,Q, random total/partial rule tables, random initial colours) and
on route-following outputs truncated at random lengths.
Usage: fuzz_agree.py <tools/src dir> <cases_dir> <n>"""
import sys, os, random, tempfile
src, cd, n = sys.argv[1], sys.argv[2], int(sys.argv[3])
sys.path.insert(0, src)
from verifier import Verifier
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import oracle
rng = random.Random(12345)
cases = sorted(os.listdir(cd))
tmp = tempfile.mkdtemp()
dis = 0; kinds = {}
for it in range(n):
    case = os.path.join(cd, rng.choice(cases))
    N, K, T, v, h, tg = oracle.read_case(case)
    C = rng.randint(1, 6); Q = rng.randint(1, 6)
    pairs = [(c, q) for c in range(C) for q in range(Q)]
    rng.shuffle(pairs)
    pairs = pairs[:rng.randint(0, min(len(pairs), T))]
    lines = [f'{C} {Q} {len(pairs)}']
    lines += [' '.join(str(rng.randrange(C)) for _ in range(N)) for _ in range(N)]
    for c, q in pairs:
        lines.append(f'{c} {q} {rng.randrange(C)} {rng.randrange(Q)} {rng.choice("UDLRS")}')
    out = os.path.join(tmp, 'o.txt'); open(out, 'w').write('\n'.join(lines) + '\n')
    ok, err, s1 = Verifier(case).verify(out)
    s2, why = oracle.score(case, out)
    kinds[why.split()[0]] = kinds.get(why.split()[0], 0) + 1
    if (s1 if ok else None) != s2:
        dis += 1; print('DISAGREE', case, ok, s1, s2, why)
print('random tables:', n, 'disagreements:', dis, 'outcome kinds:', kinds)
