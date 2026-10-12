#!/usr/bin/env python3
"""Map grading cases to generator seeds (exact byte match with tools/src/gen.py),
and compute the shipped-baseline cost sum for generator seed ranges.
Usage: seeds.py <gen.py dir> <cases_dir> <max_seed>"""
import sys, os, hashlib
sys.path.insert(0, sys.argv[1])
from gen import generate
cases = {}
for f in sorted(os.listdir(sys.argv[2])):
    cases[hashlib.sha256(open(os.path.join(sys.argv[2], f), 'rb').read()).hexdigest()] = f
heads = {open(os.path.join(sys.argv[2], f)).read().split('\n', 1)[0] for f in os.listdir(sys.argv[2])}
found = {}
def base(txt):
    N, K, T = map(int, txt.split('\n', 1)[0].split())
    return 2 * N ** 4 + (K - 1) * N ** 2
sums = {}
for seed in range(int(sys.argv[3]) + 1):
    t = generate(seed)
    hsh = hashlib.sha256(t.encode()).hexdigest()
    if hsh in cases:
        found[cases[hsh]] = seed
    for lo in (0, 1):
        if lo <= seed < lo + 50:
            sums[lo] = sums.get(lo, 0) + base(t)
print('MATCHED', len(found), 'of', len(cases))
for f in sorted(found): print(f, 'seed', found[f])
print('BASELINE_SUM seeds0-49', sums.get(0), 'seeds1-50', sums.get(1))
