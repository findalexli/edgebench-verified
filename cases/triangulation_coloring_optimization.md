# Triangulation Coloring Optimization (`triangulation_coloring_optimization`)

**Decision:** Repair (v2). The flip-legality rule leaves out the README's convexity condition; the same rule generated all ten hidden cases, which overlap or fold, and it scores submissions.

## What the task asks for

The README defines the move: "if an edge is a diagonal of a **convex quadrilateral** formed by two adjacent triangles, replace it with the other diagonal. The result remains a valid triangulation." The input is "a **triangulation**" of N = 512 points. The prompt says "The local `tester` applies flips exactly like the judge", and the score is counted "on the **final** triangulation after all flips". Category: Combinatorial Optimization.

## What goes wrong

**Rule.** A flip is legal only for a diagonal of a convex quadrilateral. The shared library's `Triangulation.is_flippable` checks only that the two apexes lie on opposite sides of the shared edge. It never checks that the shared edge's endpoints lie on opposite sides of the new diagonal. It therefore accepts flips of non-convex quadrilaterals, and those flips fold the mesh.

**Effect on the inputs.** `gen.py` applies K random flips with this predicate to build every case. All ten hidden inputs contain overlapping triangles, with 17 to 583 overlapping triangle pairs per case. Six of them also contain duplicate triangles and non-manifold edges. Pure generator output with no flips (K=0) has no overlaps.

**Effect on scoring.** The same predicate is the official scorer's move rule:

- On every hidden case, 317–379 interior edges pass the official predicate but are not diagonals of a convex quadrilateral. The README forbids flipping these edges.
- No convex-quadrilateral flip is rejected. The official rule is a strict superset of the documented rule.
- **Example under the original evaluator (case 0009):** the shipped do-nothing output scores `Score = 644809` (U=803). Adding one README-forbidden non-convex flip (edge 39–52) is accepted and scores `Score = 641611` (U=801). A forbidden move improves the official score.
- **Minimal example (N=4):** the input is a valid two-triangle mesh with a reflex quadrilateral. The original tester accepts the forbidden flip (`Score = 41`), and the resulting two triangles overlap. The defect does not depend on a bad input.

**Limiting factor.** The work image ships the same `verifier.py`, `tester` and samples. The solver's local loop therefore sees exactly the judge's rule, so scores are consistent and reproducible. The harm is that the scored problem differs from the documented one.

## Impact

Material, for all solvers: the rule changes which flips are legal for everyone. The size of the gain for a strong solver over a full optimization was not measured.

## Fix (v2)

v2 changes `is_flippable` in `tools/src/triangulation.py`, in both the judge and the work image. It now also requires `a != b`, that edge ab does not already exist, and that the two shared-edge endpoints lie strictly on opposite sides of the new diagonal. Nothing else in the file changes.

The 10 hidden cases and 3 samples were then regenerated with the shipped, unmodified `gen.py` and `delaunay.py` plus the fixed predicate:

- Case 0000 and the samples keep their original seeds (9000000 and 1000001–1000003).
- Cases 0001–0009 use new seeds 9000001–9000009, because the original seeds are unknown. K is inferred from each case's defect profile.

`verifier.py`, `tester`, the evaluator, the READMEs, the prompt, the parser, the timeouts and the rescale anchors are unchanged. On all 26 inputs (13 original, 13 v2), the fixed predicate equals the independent exact convex test on every edge, and it is a subset of the old predicate. v2 forbids no README-legal flip.

Full judge (`eval_cmd`, 10 hidden cases):

| submission | role | v1 raw | v1 cases OK | v1 normalized | v2 raw | v2 cases OK | v2 normalized |
|---|---|---:|---|---:|---:|---|---:|
| shipped `solution.py` (do nothing) | valid control | 6,092,430 | 10/10 | 0.055 | 6,092,622 | 10/10 | 0.054 |
| `greedy.py` (greedy recolour + greedy README-legal convex flips) | independent honest control | 866,166 | 10/10 | 48.87 | 863,058 | 10/10 | 48.95 |
| `nonconvex_flip.py` (do nothing + one README-forbidden non-convex flip per case) | **trigger** | 6,093,050 | 10/10 accepted | 0.052 | inf | 0/10 (WA "Invalid flip") | 0 (invalid run) |
| `wrong_count.py` (recolours vertex 1, claims C=0) | invalid control | inf | 0/10 (WA) | 0 (invalid) | inf | 0/10 (WA) | 0 (invalid) |

Same inputs, rule only:

| input | v1 tester | v2 tester |
|---|---|---|
| N=4 valid 2-triangle input with reflex quadrilateral, flip 1–2 (review control) | accepted, `Score = 41` (result overlaps) | `wrong answer: Invalid flip (1,2)` |
| each v2 hidden case + its first non-convex flippable-under-v1 edge (10 inputs) | 10/10 accepted | 10/10 `Invalid flip` |

Solver-visible loop (work image):

| submission | v1 SAMPLE_TOTAL | v2 SAMPLE_TOTAL |
|---|---:|---:|
| do nothing | 1,780,251 | 1,802,171 |
| greedy | 263,500 | 258,183 |
| nonconvex_flip | 1,780,471 (accepted) | all 3 `wrong answer: Invalid flip` |

The saved case-0009 output with the score-improving forbidden flip scores `Score: 641611` under the original verifier and `INVALID: Invalid flip (39,52)` with the v2 `triangulation.py`. All 13 regenerated inputs have 0 overlapping pairs, 0 crossings, 0 folds, 0 duplicate or degenerate triangles and 0 non-manifold edges.

**Score compatibility:** v2 scores are **not comparable** with v1 scores, for three reasons:

- 9 of 10 hidden inputs are new instances.
- All inputs are now valid triangulations.
- The legal move set is smaller.

All four original rescale anchors are kept unchanged as a fixed reference scale only. They no longer correspond to leaderboard ranks on v2.

## How we know

- **Original evaluator in the pinned image.** The original `tools/bin/tester` and the full original `eval_cmd` ran in the judge image (`sha256:beeea763…dcf671`) with `--network none`, for v1 and v2.
- **Independent oracle.** Exact integer geometry, with no floats, on all 10 hidden cases and all 3 samples: an exact separating-axis overlap test for each triangle pair, proper edge crossings, vertices inside triangles, duplicate, degenerate and non-manifold triangles and edges, Euler characteristic and vertex links, area excess against the convex hull, and collinear triples. On every interior edge, the official predicate was compared with an independent exact convex-quadrilateral test.
- **Regeneration.** The shipped `gen.py` with seed 9000000 reproduces hidden case 0000 byte for byte, and seeds 1000001–1000003 reproduce all three samples byte for byte. (The O(N³) collinearity check was swapped for an exactly equivalent faster test.)
- **Repeatability.** The paired evaluation was run three times; no verdict changed (`paired-repeatability.md`).

## Limits

- No model or solver was run. Score effects are shown only on authored controls.
- The original seeds for hidden cases 0001–0009 are unknown. Their K is inferred, not recovered.
- The shipped Delaunay super-triangle artifact is untouched. 12 of 13 v2 inputs miss 1–3 convex-hull triangles: each is a valid triangulated polygon of all points, not of the full hull. The README wording "a triangulation of those points" is slightly stronger than this. The wording is noted but not changed.
- The CodeChef TRICOL statement and checker were not consulted.
- The gain a strong solver gets from non-convex flips over a full optimization was not measured.
- The v2 images were built and tested locally to the run and then removed. They are not registry digests.

## Reproduce

- Geometry and rule analysis: `evidence/scripts/triangulation_coloring_optimization/check_geometry.py`, `flip_rule_analysis.py`, `regen_compare.py`, `run_gen.py`
- v2 regeneration and rule check: `evidence/scripts/triangulation_coloring_optimization/v2/regen_v2.py`, `v2/rule_check.py`
- Paired evaluation: `repairs/triangulation_coloring_optimization-v2/paired/run.sh` (results in `paired/results.md`)
- Patch: `repairs/triangulation_coloring_optimization-v2/repair.patch`
- Pinned identity: judge image `seededge/edgebench.judge.triangulation_coloring_optimization@sha256:beeea763…dcf671`; `triangulation.py` sha256 `32862fe5…`; `verifier.py` `1f0c714a…`; `gen.py` `67201f1e…`; `tools/bin/tester` `01b6e17b…`; hidden case 0000 `8e0c5efc…`.

Supporting records: `repairs/triangulation_coloring_optimization-v2/` (source-lock.json, paired logs).
