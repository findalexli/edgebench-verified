#!/usr/bin/env python3
"""Run the shipped tools/src/gen.py generate() at N=512 and audit the result.

Usage: python3 -I run_gen.py <tools/src dir> <outdir> seed:k [seed:k ...]
The O(N^3) has_collinear_triple is replaced by an exactly equivalent
O(N^2 log N) gcd-direction test (same boolean result) so N=512 runs quickly;
everything else is the shipped code. Also records k=0 (pure Delaunay output).
"""
import sys, os, json
src, out = sys.argv[1], sys.argv[2]
sys.path.insert(0, src)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen
from check_geometry import collinear_triples, audit
gen.has_collinear_triple = lambda pts: collinear_triples(pts) > 0
os.makedirs(out, exist_ok=True)
for spec in sys.argv[3:]:
    seed, k = map(int, spec.split(":"))
    txt = gen.generate(seed, 512, k, 40, 40)
    f = os.path.join(out, f"gen_s{seed}_k{k}.txt")
    open(f, "w").write(txt)
    r = audit(f, do_collinear=False)
    r.pop("folded_examples_1idx"); r.pop("overlap_examples_1idx")
    print(json.dumps({"seed": seed, "k": k, **{x: r[x] for x in (
        "M", "expected_M_planar", "boundary_edges", "hull_vertices", "duplicate_triangles",
        "nonmanifold_edges", "folded_interior_edges", "overlapping_triangle_pairs",
        "crossing_edge_pairs", "area_excess_twice")}}), flush=True)
