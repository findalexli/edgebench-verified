#!/usr/bin/env python3
"""Exact-integer geometry audit of TRICOL input files.

Usage: python3 -I check_geometry.py case1.txt [case2.txt ...]
All predicates use Python int arithmetic (no floats).
Reports per case: N, M, hull size h, expected M for a planar triangulation of
the point set (2N-2-h), duplicate / degenerate triangles, non-manifold edges,
boundary edges, "folded" interior edges (both triangles on the same side of
the shared edge), distinct triangle pairs with overlapping open interiors
(exact separating-axis test), distinct pairs of properly crossing edges,
(vertex, triangle) pairs with the vertex strictly inside, area excess
(sum of |2*area| minus 2*hull area), collinear point triples, and whether the
complex is still a combinatorial triangulated disk (Euler + vertex links).
"""
import sys
from collections import defaultdict
from math import gcd


def orient(p, q, r):
    return (q[0]-p[0])*(r[1]-p[1]) - (q[1]-p[1])*(r[0]-p[0])


def read_case(path):
    t = open(path).read().split()
    n, m = int(t[0]), int(t[1])
    i = 7
    pts = []
    for _ in range(n):
        pts.append((int(t[i]), int(t[i+1]))); i += 2
    tris = []
    for _ in range(m):
        tris.append(tuple(int(t[i+k]) - 1 for k in range(3))); i += 3
    return n, m, pts, tris


def hull(pts):
    P = sorted(set(pts))
    def half(seq):
        h = []
        for p in seq:
            while len(h) >= 2 and orient(h[-2], h[-1], p) <= 0:
                h.pop()
            h.append(p)
        return h
    lo, up = half(P), half(P[::-1])
    return lo[:-1] + up[:-1]


def collinear_triples(pts):
    # for each point, normalised directions to later points; duplicates => collinear
    cnt = 0
    n = len(pts)
    for i in range(n):
        seen = defaultdict(int)
        for j in range(i+1, n):
            dx, dy = pts[j][0]-pts[i][0], pts[j][1]-pts[i][1]
            g = gcd(dx, dy)
            dx, dy = dx//g, dy//g
            if dx < 0 or (dx == 0 and dy < 0):
                dx, dy = -dx, -dy
            seen[(dx, dy)] += 1
        for c in seen.values():
            cnt += c*(c-1)//2
    return cnt


def ccw_tri(pts, t):
    a, b, c = t
    return (a, b, c) if orient(pts[a], pts[b], pts[c]) > 0 else (a, c, b)


def interiors_overlap(P, Q):
    # P, Q: lists of 3 points, CCW, non-degenerate. SAT on edge normals.
    for A, B in ((P, Q), (Q, P)):
        for k in range(3):
            p, q = A[k], A[(k+1) % 3]
            if all(orient(p, q, r) <= 0 for r in B):
                return False
    return True


def proper_cross(a, b, c, d):
    o1, o2 = orient(a, b, c), orient(a, b, d)
    o3, o4 = orient(c, d, a), orient(c, d, b)
    return o1*o2 < 0 and o3*o4 < 0


def bbox(ps):
    xs = [p[0] for p in ps]; ys = [p[1] for p in ps]
    return min(xs), max(xs), min(ys), max(ys)


def audit(path, do_collinear=True):
    n, m, pts, tris = read_case(path)
    r = {"file": path, "N": n, "M": m}
    H = hull(pts)
    h = len(H)
    r["hull_vertices"] = h
    r["expected_M_planar"] = 2*n - 2 - h
    norm = [tuple(sorted(t)) for t in tris]
    r["duplicate_triangles"] = m - len(set(norm))
    r["degenerate_triangles"] = sum(1 for t in tris if orient(*(pts[v] for v in t)) == 0)
    r["vertices_unused"] = n - len({v for t in tris for v in t})
    e2t = defaultdict(list)
    for ti, t in enumerate(norm):
        a, b, c = t
        for u, v in ((a, b), (b, c), (a, c)):
            e2t[(u, v)].append(ti)
    r["edges"] = len(e2t)
    r["nonmanifold_edges"] = sum(1 for v in e2t.values() if len(v) > 2)
    r["boundary_edges"] = sum(1 for v in e2t.values() if len(v) == 1)
    folded = []
    for (u, v), ts in e2t.items():
        if len(ts) == 2:
            a = next(x for x in norm[ts[0]] if x not in (u, v))
            b = next(x for x in norm[ts[1]] if x not in (u, v))
            if orient(pts[u], pts[v], pts[a]) * orient(pts[u], pts[v], pts[b]) > 0:
                folded.append((u+1, v+1))
    r["folded_interior_edges"] = len(folded)
    r["folded_examples_1idx"] = folded[:5]
    # combinatorial disk check: Euler V-E+F = 1 and each vertex link is a path or cycle
    used = {v for t in norm for v in t}
    r["euler_V_minus_E_plus_F"] = len(used) - len(e2t) + m
    link = defaultdict(list)
    for t in norm:
        for v in t:
            o = [x for x in t if x != v]
            link[v].append(tuple(o))
    bad_link = 0
    for v, es in link.items():
        deg = defaultdict(int)
        for a, b in es:
            deg[a] += 1; deg[b] += 1
        if any(d > 2 for d in deg.values()) or sum(1 for d in deg.values() if d == 1) not in (0, 2):
            bad_link += 1
            continue
        # connectivity
        adj = defaultdict(list)
        for a, b in es:
            adj[a].append(b); adj[b].append(a)
        start = es[0][0]; seen = {start}; st = [start]
        while st:
            x = st.pop()
            for y in adj[x]:
                if y not in seen:
                    seen.add(y); st.append(y)
        if len(seen) != len(deg):
            bad_link += 1
    r["vertices_with_bad_link"] = bad_link
    # exact area excess
    hull2 = sum(H[i][0]*H[(i+1) % h][1] - H[(i+1) % h][0]*H[i][1] for i in range(h))
    tri2 = sum(abs(orient(*(pts[v] for v in t))) for t in tris)
    r["twice_hull_area"] = hull2
    r["sum_twice_triangle_areas"] = tri2
    r["area_excess_twice"] = tri2 - hull2
    # pairwise exact overlap
    T = [[pts[v] for v in ccw_tri(pts, t)] for t in tris]
    B = [bbox(t) for t in T]
    order = sorted(range(m), key=lambda i: B[i][0])
    ov = 0; ov_ex = []
    for ii in range(m):
        i = order[ii]
        for jj in range(ii+1, m):
            j = order[jj]
            if B[j][0] >= B[i][1]:
                break
            if B[j][3] <= B[i][2] or B[j][2] >= B[i][3]:
                continue
            if interiors_overlap(T[i], T[j]):
                ov += 1
                if len(ov_ex) < 3:
                    ov_ex.append((tuple(x+1 for x in tris[i]), tuple(x+1 for x in tris[j])))
    r["overlapping_triangle_pairs"] = ov
    r["overlap_examples_1idx"] = ov_ex
    # proper edge crossings (distinct edge pairs)
    E = list(e2t.keys())
    EB = [bbox([pts[u], pts[v]]) for u, v in E]
    eo = sorted(range(len(E)), key=lambda i: EB[i][0])
    cr = 0
    for ii in range(len(E)):
        i = eo[ii]
        for jj in range(ii+1, len(E)):
            j = eo[jj]
            if EB[j][0] > EB[i][1]:
                break
            if EB[j][3] < EB[i][2] or EB[j][2] > EB[i][3]:
                continue
            (a, b), (c, d) = E[i], E[j]
            if len({a, b, c, d}) < 4:
                continue
            if proper_cross(pts[a], pts[b], pts[c], pts[d]):
                cr += 1
    r["crossing_edge_pairs"] = cr
    # vertices strictly inside a triangle
    vin = 0
    for ti, t in enumerate(T):
        x0, x1, y0, y1 = B[ti]
        tv = set(tris[ti])
        for v in range(n):
            if v in tv:
                continue
            p = pts[v]
            if x0 < p[0] < x1 and y0 < p[1] < y1:
                if all(orient(t[k], t[(k+1) % 3], p) > 0 for k in range(3)):
                    vin += 1
    r["vertex_strictly_inside_triangle"] = vin
    if do_collinear:
        r["collinear_point_triples"] = collinear_triples(pts)
    return r


if __name__ == "__main__":
    import json
    for f in sys.argv[1:]:
        print(json.dumps(audit(f)), flush=True)
