#!/usr/bin/env python3
"""Differential fixtures: Lean model (`accepts?`) vs ORIGINAL tester bytes.
Brute-force optima on small grids plus random 1-3 character edits; tester verdict recorded.
Writes a Lean snippet that #evals the number of disagreements.
Usage: gen_diff.py <tester> <workdir> <lean_out>"""
import sys, os, random, subprocess, itertools
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from brute_force import opt
tester, wd, lean_out = sys.argv[1:4]
os.makedirs(wd, exist_ok=True)
random.seed(7)
rows = []
inst = [(2, 2, [1, 2, 3]), (2, 2, [3, 1, 2]), (2, 3, [1, 2, 3, 4, 5]), (2, 3, [3, 1, 2, 4, 5]),
        (3, 2, [5, 4, 1, 3, 2]), (1, 4, [1, 3, 2]), (4, 1, [2, 1, 3])]
for R, C, a in inst:
    S, s = opt(R, C, a)
    cands = [s]
    for _ in range(40):
        t = list(s)
        for _ in range(random.randint(1, 3)):
            op = random.random(); i = random.randrange(len(t) + 1)
            ch = random.choice('NSWEPDLUX')
            if op < 0.4 and t: t[min(i, len(t) - 1)] = ch
            elif op < 0.7: t.insert(i, ch)
            elif t: del t[min(i, len(t) - 1)]
        cands.append(''.join(t))
    cands.append(s + 'EW' if C > 1 else s + 'SN')   # valid detour
    for c in cands:
        if not c: continue
        fi = os.path.join(wd, 'in.txt'); fo = os.path.join(wd, 'out.txt')
        open(fi, 'w').write("1\n%d %d\n%s\n" % (R, C, ' '.join(map(str, a))))
        open(fo, 'w').write(c + "\n")
        pr = subprocess.run([sys.executable, '-I', tester, fi, fo], capture_output=True, text=True)
        rows.append((R, C, a, c, pr.returncode == 0))
acc = sum(r[4] for r in rows)
print("fixtures", len(rows), "tester-accepted", acc)
with open(lean_out, 'w') as o:
    o.write("def diffFixtures : List (ℕ × ℕ × List ℕ × String × Bool) := [\n")
    o.write(",\n".join('  (%d, %d, [%s], "%s", %s)' % (R, C, ', '.join(map(str, a)), c, 'true' if ok else 'false')
                       for R, C, a, c, ok in rows))
    o.write("]\n\n")
    o.write("/-- number of fixtures where the Lean model disagrees with the original tester (expect 0) -/\n")
    o.write("def diffMismatches : ℕ := (diffFixtures.filter (fun x =>\n"
            "  accepts? x.1 x.2.1 (fun i => x.2.2.1.getD i 0) x.2.2.2.1.toList != x.2.2.2.2)).length\n\n")
    o.write('#eval s!"differential fixtures={diffFixtures.length} accepted={(diffFixtures.filter (·.2.2.2.2)).length} mismatches={diffMismatches}"\n')
