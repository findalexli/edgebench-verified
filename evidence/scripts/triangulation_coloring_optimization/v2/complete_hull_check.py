#!/usr/bin/env python3
"""Check the v2.2 generator change (delaunay.complete_hull) before any pre-flip (issue #57).

Usage: python3 -I complete_hull_check.py <dir with original delaunay.py> <dir with v2.2 delaunay.py,
       fixed triangulation.py, gen.py> <tmpdir>

For every seed in regen_v2.PARAMS it draws the same points as gen.generate, then compares the
shipped Bowyer-Watson output (original delaunay.py) with the v2.2 output (K=0, before any flip):
triangles added, triangles of the original output kept, and hull_check on the K=0 v2.2 mesh
(exact coverage, overlaps and locally-Delaunay edges). Exact integer arithmetic throughout.
"""
import importlib.util
import json
import os
import random
import sys

here = os.path.dirname(os.path.abspath(__file__))
orig_dir, v22_dir, tmp = sys.argv[1:4]
sys.path[:0] = [v22_dir, os.path.dirname(here), here]
import triangulation  # noqa: E402  (fixed rule, from v22_dir)
import gen  # noqa: E402
import delaunay as d22  # noqa: E402
from check_geometry import collinear_triples  # noqa: E402
from hull_check import check  # noqa: E402

assert os.path.dirname(os.path.abspath(d22.__file__)) == os.path.abspath(v22_dir)
spec = importlib.util.spec_from_file_location("delaunay_orig", os.path.join(orig_dir, "delaunay.py"))
d_orig = importlib.util.module_from_spec(spec)
spec.loader.exec_module(d_orig)
gen.has_collinear_triple = lambda pts: collinear_triples(pts) > 0

src = open(os.path.join(here, "regen_v2.py")).read()
ns = {}  # the PARAMS table of regen_v2.py, verbatim
exec(src[src.index("PARAMS = ["):src.index("only = ")], ns)
os.makedirs(tmp, exist_ok=True)
for name, seed, k, x, y in ns["PARAMS"]:
    rng = random.Random(seed)
    pts = gen.random_points(rng, 512)
    raw = sorted(d_orig.delaunay_triangles(pts))
    full = d22.delaunay_triangles(pts)
    kept = len(set(raw) & set(full))
    path = os.path.join(tmp, name.replace("/", "_"))
    with open(path, "w") as f:
        f.write(gen.format_input(512, x, y, 256, 1024, "R" * 512, pts, full))
    r = check(path)
    print(json.dumps({
        "file": name, "seed": seed, "raw_triangles": len(raw), "v22_triangles": len(full),
        "added": len(full) - len(raw), "raw_triangles_kept": kept,
        "raw_triangles_changed_by_lawson": len(raw) - kept,
        "k0_covers_hull": r["covers_hull"], "k0_valid_hull_triangulation": r["valid_hull_triangulation"],
        "k0_area_gap": r["area_gap"], "k0_overlapping_triangle_pairs": r["overlapping_triangle_pairs"],
        "k0_edges_not_locally_delaunay": r["edges_not_locally_delaunay"],
    }), flush=True)
