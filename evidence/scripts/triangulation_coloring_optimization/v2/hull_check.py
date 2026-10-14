#!/usr/bin/env python3
"""Exact convex-hull coverage and overlap check for TRICOL inputs (v2.2, issue #57).

Usage: python3 -I hull_check.py case1.txt [case2.txt ...]

"A triangulation of those points" (task README) is a set of triangles with vertices among the
points, pairwise disjoint interiors, whose union is the convex hull of the points. Everything here
is exact: Python integers for orientations and in-circle tests, fractions.Fraction for areas.

Per file it reports the full check_geometry.audit() record plus:
- hull_area / triangle_area_sum as exact Fractions (strings) and their difference;
- boundary edges against hull edges, as sets;
- M against 2N-2-h;
- interior edges that are not locally Delaunay (exact in-circle test);
- covers_hull: triangles inside the hull (their vertices are input points), 0 overlapping
  interior pairs (exact separating-axis test) and triangle area sum == hull area. Closed sets
  with disjoint interiors whose areas add up to the hull's area cover it, so these three facts
  prove coverage with no gaps and no overlaps. The boundary/hull edge equality and the
  2N-2-h count are recorded as independent consequences, not used in the proof.
"""
import json
import os
import sys
from collections import defaultdict
from fractions import Fraction

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from check_geometry import audit, hull, orient, read_case  # noqa: E402


def in_circle(a, b, c, d):
    """> 0 iff d is strictly inside the circumcircle of the counter-clockwise triangle abc."""
    rows = [(p[0] - d[0], p[1] - d[1]) for p in (a, b, c)]
    (ax, ay), (bx, by), (cx, cy) = rows
    return ((ax * ax + ay * ay) * (bx * cy - cx * by)
            - (bx * bx + by * by) * (ax * cy - cx * ay)
            + (cx * cx + cy * cy) * (ax * by - bx * ay))


def check(path):
    r = audit(path)
    n, m, pts, tris = read_case(path)
    H = hull(pts)
    h = len(H)
    idx = {p: i for i, p in enumerate(pts)}
    hull_edges = {tuple(sorted((idx[H[i]], idx[H[(i + 1) % h]]))) for i in range(h)}
    hull_area = sum(Fraction(H[i][0] * H[(i + 1) % h][1] - H[(i + 1) % h][0] * H[i][1], 2) for i in range(h))
    tri_area = sum(Fraction(abs(orient(*(pts[v] for v in t))), 2) for t in tris)
    e2t = defaultdict(list)
    for t in tris:
        a, b, c = sorted(t)
        for e in ((a, b), (b, c), (a, c)):
            e2t[e].append(t)
    boundary = {e for e, ts in e2t.items() if len(ts) == 1}
    not_delaunay = 0
    for (u, v), ts in e2t.items():
        if len(ts) != 2:
            continue
        a = next(x for x in ts[0] if x not in (u, v))
        b = next(x for x in ts[1] if x not in (u, v))
        x, y = (u, v) if orient(pts[u], pts[v], pts[a]) > 0 else (v, u)
        if in_circle(pts[x], pts[y], pts[a], pts[b]) > 0:
            not_delaunay += 1
    r.update({
        "hull_area": str(hull_area),
        "triangle_area_sum": str(tri_area),
        "area_gap": str(hull_area - tri_area),
        "hull_edges": len(hull_edges),
        "boundary_edges_equal_hull_edges": boundary == hull_edges,
        "hull_edges_missing_from_mesh": len(hull_edges - set(e2t)),
        "boundary_edges_not_on_hull": len(boundary - hull_edges),
        "M_minus_2N_2_h": m - (2 * n - 2 - h),
        "missing_triangles": (2 * n - 2 - h) - m,
        "edges_not_locally_delaunay": not_delaunay,
    })
    r["covers_hull"] = (r["overlapping_triangle_pairs"] == 0 and r["degenerate_triangles"] == 0
                        and tri_area == hull_area)
    r["valid_hull_triangulation"] = (
        r["covers_hull"] and r["boundary_edges_equal_hull_edges"] and r["M_minus_2N_2_h"] == 0
        and r["duplicate_triangles"] == 0 and r["nonmanifold_edges"] == 0
        and r["crossing_edge_pairs"] == 0 and r["vertex_strictly_inside_triangle"] == 0
        and r["vertices_unused"] == 0 and r["collinear_point_triples"] == 0)
    return r


if __name__ == "__main__":
    for f in sys.argv[1:]:
        print(json.dumps(check(f)), flush=True)
