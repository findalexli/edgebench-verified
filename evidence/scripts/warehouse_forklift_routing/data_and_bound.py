#!/usr/bin/env python3
"""Validate the 50 judge inputs, look for generator-seed reuse, and compute the exact
lower bound on the raw TOTAL_SCORE implied by the potential argument in the review:
  per-case S >= 2RC(R+C-1) - 6(R+C-2) - 2  =>  per-case score >= 20 - 6(R+C-2)/(R+C-1).
Usage: data_and_bound.py <cases_dir> <gen.py> [max_seed]
"""
import sys, os, glob, math, random
from fractions import Fraction

cases_dir, gen_path = sys.argv[1], sys.argv[2]
max_seed = int(sys.argv[3]) if len(sys.argv) > 3 else 100000
files = sorted(f for f in glob.glob(os.path.join(cases_dir, '*')) if os.path.isfile(f))
print("files", len(files))
bound_total = Fraction(0); diag_total = Fraction(0)
keys = {}; dims = []
bad = 0
for f in files:
    tok = open(f).read().split()
    T = int(tok[0]); i = 1; ok = True; per = []
    sig = []
    for _ in range(T):
        R, C = int(tok[i]), int(tok[i + 1]); i += 2
        n = R * C - 1
        a = [int(x) for x in tok[i:i + n]]; i += n
        ok &= (6 <= R <= 20 and 6 <= C <= 20 and sorted(a) == list(range(1, n + 1)) and a[-1] != 1)
        per.append(20 - Fraction(6 * (R + C - 2), R + C - 1))
        dims.append((R, C)); sig.append((R, C, tuple(a[:5])))
    ok &= (T == 5 and i == len(tok))
    bad += not ok
    bound_total += sum(per) / T
    keys[tuple(sig)] = os.path.basename(f)
print("invalid files", bad, "| subcases", len(dims), "| distinct (R,C)", len(set(dims)))
print("R mean %.2f C mean %.2f" % (sum(r for r, _ in dims) / len(dims), sum(c for _, c in dims) / len(dims)))
print("lower bound on TOTAL_SCORE (sum of 50 file averages): %s = %.4f" % (bound_total, float(bound_total)))
print("per-file mean lower bound %.4f" % (float(bound_total) / len(files)))

# generator replay, same algorithm as tools/bin/gen (Python random), compared by signature
src = open(gen_path).read()
ns = {}
exec(compile(src.replace('if __name__ == "__main__":', 'if False:'), 'gen', 'exec'), ns)
hits = []
for s in range(0, max_seed + 1):
    txt = ns['generate'](s).split('\n')
    sig = []
    for t in range(5):
        R, C = map(int, txt[1 + 2 * t].split())
        a = tuple(int(x) for x in txt[2 + 2 * t].split()[:5])
        sig.append((R, C, a))
    if tuple(sig) in keys:
        hits.append((s, keys[tuple(sig)]))
print("generator seeds 0..%d reproducing a judge file: %d %s" % (max_seed, len(hits), hits[:60]))
