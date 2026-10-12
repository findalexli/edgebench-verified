# triangulation_coloring_optimization: formal check of the flip rule

## Claim

1. The fixed `is_flippable` geometric test is exactly strict convexity of the quadrilateral u→a→v→b. Equivalently, the diagonals uv and ab cross at a point inside both segments.
2. After a flip the fixed rule accepts, the new triangles (a,b,u) and (a,b,v) are non-degenerate and lie strictly on opposite sides of ab. Their interiors are disjoint, and the closed triangles meet only in the segment ab.
3. Every flip the fixed rule allows was also allowed by the original rule. The fixed rule forbids no README-legal flip as long as no existing edge properly crosses uv, which holds in any valid triangulation.
4. The original rule accepts the published N=4 reflex input, and the two triangles after the flip overlap.

## Model and link to the code

The proofs are in `evidence/formal/lean/ebv/Ebv/TriangulationFlip.lean`, and the compiler output is in `TriangulationFlip.out`. The model covers `/home/workspace/triangulation_coloring/tools/src/triangulation.py`:

- original version: sha256 `32862fe5…c1a844`, lines 52-63;
- fixed version: sha256 `8b5b9cbb…d86bbd`, lines 52-71.

The `orient` function in the model is lines 11-19 of the source. `origGeom` and `fixedFlip` follow the source branch for branch. `isFlippable` is an executable model of the whole method: the edge map, the apex choice with `next(...)` and `has_edge`. Points have integer coordinates, so the model's ℤ arithmetic matches Python's exactly. The geometric statements are made over ℚ.

## Result

**Proved.** The theorems are `fixed_iff_convex`, `fixed_iff_cross`, `fixedFlip_iff`, `fixed_flip_sound`, `fixed_subset_orig` and `fixed_complete`. The key step is the area identity s2 − s1 = s3 − s4. It shows that the two sign tests in the code imply that all four turns go the same way.

The completeness claim needs a hypothesis that is not visible in the code: the guard `has_edge(a,b)` also rejects a convex flip when edge ab already exists. That can only happen in a mesh where ab crosses uv, which is not a valid triangulation. So "forbids no README-legal flip" holds for valid triangulations, which is what the README promises and what the v2 inputs are. On the folded original inputs this guard could in principle reject a convex flip. The saved `rule_check.jsonl` found no such edge.

## Counter-check

- On the published N=4 input (`n4_nonconvex.txt`), the executable model gives the same verdicts as the saved tester outputs: the original accepts (`Score = 41`) and the fixed version rejects (`Invalid flip (1,2)`). These are `n4_orig_accepts` and `n4_fixed_rejects`, both proved by `decide`.
- The quadrilateral is not strictly convex (`n4_not_convex`).
- The point (−4, 1) lies strictly inside both new triangles, with barycentric coordinates 5/12, 5/12, 1/6 and 52/105, 52/105, 1/105 (`n4_overlap`).
- So the original rule fails both properties (`orig_not_convexity`, `orig_unsound`), and the subset is strict (`orig_not_subset_fixed`).

## Limits

- The model covers the single flip predicate and one flip. It does not prove that the whole mesh stays a valid triangulation, but the local result implies it for a valid input.
- The model has not been run on the 512-point cases. Agreement there rests on the Python `rule_check.jsonl`.
- `verifier.py`, `tester` and `gen.py` are not modelled. They call this method, as the review states.
- Triangle orientation is not modelled, because `normalize_triangle` sorts the indices. "Positive area" is proved as nonzero |orient|.
