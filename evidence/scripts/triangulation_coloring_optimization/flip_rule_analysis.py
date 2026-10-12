#!/usr/bin/env python3
"""Compare the shipped verifier's flip predicate with the README's
"diagonal of a convex quadrilateral" rule, exactly, on each input.

Usage: python3 -I flip_rule_analysis.py <tools/src> <outdir> case.txt [...]
For each case prints counts of interior edges that are
  verifier_flippable  (shipped Triangulation.is_flippable)
  convex_flippable    (strictly convex quad: a,b split by line uv AND u,v split by line ab)
  verifier_only       (accepted by verifier, quad NOT convex -> flip creates overlap)
Writes <outdir>/<case>_one_nonconvex_flip.out : a valid output (no recolor,
one verifier-only flip) for running through the official tester.
"""
import sys, os, json
sys.path.insert(0, sys.argv[1])
from triangulation import Triangulation, ccw
from verifier import Verifier

out = sys.argv[2]; os.makedirs(out, exist_ok=True)
for f in sys.argv[3:]:
    t = open(f).read().split()
    n, m = int(t[0]), int(t[1]); s = t[6]
    i = 7; pts = []
    for _ in range(n):
        pts.append((int(t[i]), int(t[i+1]))); i += 2
    tris = []
    for _ in range(m):
        tris.append(tuple(int(t[i+k]) - 1 for k in range(3))); i += 3
    T = Triangulation(pts, tris)
    vf = cf = vo = 0; example = None
    for (u, v), ts in T.edge_to_tris.items():
        if not T.is_flippable(u, v):
            # convex-but-rejected would be a different divergence; count it
            if len(ts) == 2:
                a = next(x for x in ts[0] if x not in (u, v)); b = next(x for x in ts[1] if x not in (u, v))
                if a != b and ccw(u, v, a, pts) * ccw(u, v, b, pts) < 0 and ccw(a, b, u, pts) * ccw(a, b, v, pts) < 0:
                    print("CONVEX BUT REJECTED", u, v)
            continue
        vf += 1
        a = next(x for x in ts[0] if x not in (u, v)); b = next(x for x in ts[1] if x not in (u, v))
        if ccw(a, b, u, pts) * ccw(a, b, v, pts) < 0:
            cf += 1
        else:
            vo += 1
            if example is None:
                example = (u, v, a, b)
    U0 = T.count_ugly(s)
    rec = {"case": os.path.basename(f), "M": m, "U_initial": U0, "trivial_G": U0*U0,
           "verifier_flippable": vf, "convex_flippable": cf, "verifier_only_nonconvex": vo}
    if example:
        u, v, a, b = example
        rec["example_nonconvex_flip_1idx"] = {"edge": [u+1, v+1], "opposite": [a+1, b+1],
            "pts": {"u": pts[u], "v": pts[v], "a": pts[a], "b": pts[b]},
            "orient_ab_u": ccw(a, b, u, pts), "orient_ab_v": ccw(a, b, v, pts)}
        o = os.path.join(out, os.path.basename(f).replace(".txt", "_one_nonconvex_flip.out"))
        open(o, "w").write(f"0 1\n{s}\n{u+1} {v+1}\n")
        ok, err, score = Verifier(f).verify(o)
        rec["shipped_verifier_on_that_output"] = [ok, err, score]
    print(json.dumps(rec), flush=True)
