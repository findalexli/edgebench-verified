#!/usr/bin/env python3
"""Compare flip predicates edge-by-edge: original is_flippable (v1), fixed is_flippable (v2),
and an independent convex-quadrilateral test (exact ints) on each input file.
Usage: python3 -I rule_check.py <v1 src dir> <v2 src dir> files..."""
import importlib.util, sys, json
def load(d):
    sp = importlib.util.spec_from_file_location("t" + str(abs(hash(d))), d + "/triangulation.py")
    m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m); return m
T1, T2 = load(sys.argv[1]), load(sys.argv[2])
def orient(p, q, r): return (q[0]-p[0])*(r[1]-p[1]) - (q[1]-p[1])*(r[0]-p[0])
for f in sys.argv[3:]:
    t = open(f).read().split(); n, m = int(t[0]), int(t[1]); i = 7
    pts = [(int(t[i+2*k]), int(t[i+2*k+1])) for k in range(n)]; i += 2*n
    tris = [tuple(int(t[i+3*k+j]) - 1 for j in range(3)) for k in range(m)]
    a1, a2 = T1.Triangulation(pts, tris), T2.Triangulation(pts, tris)
    c = dict(edges=0, v1=0, v2=0, convex=0, v2_ne_convex=0, v2_not_subset_v1=0)
    for (u, v), ts in a1.edge_to_tris.items():
        c["edges"] += 1
        f1, f2 = a1.is_flippable(u, v), a2.is_flippable(u, v)
        cv = False
        if len(ts) == 2:
            a = next(x for x in ts[0] if x not in (u, v)); b = next(x for x in ts[1] if x not in (u, v))
            cv = a != b and orient(pts[u], pts[v], pts[a]) * orient(pts[u], pts[v], pts[b]) < 0 \
                 and orient(pts[a], pts[b], pts[u]) * orient(pts[a], pts[b], pts[v]) < 0 \
                 and (min(a, b), max(a, b)) not in a1.edge_to_tris
        c["v1"] += f1; c["v2"] += f2; c["convex"] += cv
        c["v2_ne_convex"] += f2 != cv; c["v2_not_subset_v1"] += f2 and not f1
    print(json.dumps({"file": f.split("/")[-2] + "/" + f.split("/")[-1], **c}))
