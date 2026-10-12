# Triangulation Coloring Optimization (`triangulation_coloring_optimization`)

**Outcome:** Fixed. The grader's rule for legal edge flips leaves out the README's convexity condition; the same rule generated all ten hidden inputs, which contain overlapping or folded triangles, and it also decides which submitted moves are accepted.

![A dart-shaped four-point shape where flipping its inner edge makes two triangles overlap; the original grader accepts the flip with Score = 41 and the fixed version rejects it as an invalid flip.](figures/triangulation_coloring_optimization.svg)

*The original grader accepts flips the rules forbid, and they even improve the score (644,809 to 641,611 on case 0009); the fixed version rejects them.*

## What the task asks

The input is "a **triangulation**" of N = 512 points: a mesh of triangles that covers the points without overlaps. The agent recolours points and flips edges to lower a score. The README defines the move: "if an edge is a diagonal of a **convex quadrilateral** formed by two adjacent triangles, replace it with the other diagonal. The result remains a valid triangulation."

The prompt says "The local `tester` applies flips exactly like the judge". The score is counted "on the **final** triangulation after all flips". Category: Combinatorial Optimization.

## What goes wrong

**Rule.** A flip is legal only for a diagonal of a convex quadrilateral. The shared library's `Triangulation.is_flippable` checks only that the two apexes (the far corners of the two triangles) lie on opposite sides of the shared edge. It never checks that the shared edge's endpoints lie on opposite sides of the new diagonal. It therefore accepts flips of non-convex quadrilaterals, and those flips fold the mesh.

**Effect on the inputs.** `gen.py` applies K random flips with this rule to build every case. All ten hidden inputs contain overlapping triangles, with 17 to 583 overlapping triangle pairs per case. Six of them also contain duplicate triangles and non-manifold edges (edges shared by more than two triangles). Plain generator output with no flips (K=0) has no overlaps.

**Effect on scoring.** The same rule is the official grader's move rule:

- On every hidden case, 317–379 interior edges pass the official rule but are not diagonals of a convex quadrilateral. The README forbids flipping these edges.
- No convex-quadrilateral flip is rejected. The official rule allows everything the documented rule allows, and more.
- **Example under the original grader (case 0009):** the shipped do-nothing output scores `Score = 644809` (U=803). Adding one README-forbidden non-convex flip (edge 39–52) is accepted and scores `Score = 641611` (U=801). A forbidden move improves the official score (lower is better).
- **Minimal example (N=4):** the input is a valid two-triangle mesh whose quadrilateral has a reflex (inward-pointing) corner. The original tester accepts the forbidden flip (`Score = 41`), and the resulting two triangles overlap. The problem does not depend on a bad input.

**What limits the harm.** The agent's working image ships the same `verifier.py`, `tester` and samples. The agent's local testing therefore sees exactly the grader's rule, so scores are consistent and repeatable. The harm is that the scored problem differs from the documented one.

## How much it matters

This changes scores enough to matter, for all solvers: the rule changes which flips are legal for everyone. The size of the gain for a strong solver over a full optimization was not measured.

## The fix

The fixed version changes `is_flippable` in `tools/src/triangulation.py`, in both the grader image and the agent's working image. It now also requires `a != b`, that edge ab does not already exist, and that the two shared-edge endpoints lie strictly on opposite sides of the new diagonal. Nothing else in the file changes.

The 10 hidden cases and 3 samples were then regenerated with the shipped, unmodified `gen.py` and `delaunay.py` plus the fixed rule:

- Case 0000 and the samples keep their original seeds (9000000 and 1000001–1000003).
- Cases 0001–0009 use new seeds 9000001–9000009, because the original seeds are unknown. K is inferred from each case's pattern of defects.

These are unchanged: `verifier.py`, `tester`, the grader, the READMEs, the prompt, the parser, the timeouts and the reference points of the score scale. On all 26 inputs (13 original, 13 fixed), the fixed rule equals the independent exact convexity test on every edge. It allows only flips the old rule allowed. The fixed version forbids no flip the README allows.

Full grader (`eval_cmd`, 10 hidden cases). Lower raw results are better.

| Submission | Role | Original grader, raw | Original grader, cases OK | Original grader, out of 100 | Fixed grader, raw | Fixed grader, cases OK | Fixed grader, out of 100 |
|---|---|---:|---|---:|---:|---|---:|
| shipped `solution.py` (do nothing) | correct test submission | 6,092,430 | 10/10 | 0.055 | 6,092,622 | 10/10 | 0.054 |
| `greedy.py` (greedy recolour + greedy README-legal convex flips) | independent honest test submission | 866,166 | 10/10 | 48.87 | 863,058 | 10/10 | 48.95 |
| `nonconvex_flip.py` (do nothing + one README-forbidden non-convex flip per case) | **shows the problem** | 6,093,050 | 10/10 accepted | 0.052 | inf | 0/10 (WA "Invalid flip") | 0 (invalid run) |
| `wrong_count.py` (recolours vertex 1, claims C=0) | invalid test submission | inf | 0/10 (WA) | 0 (invalid) | inf | 0/10 (WA) | 0 (invalid) |

Same inputs, rule only:

| Input | Original tester | Fixed tester |
|---|---|---|
| N=4 valid 2-triangle input with reflex quadrilateral, flip 1–2 (test submission from the review) | accepted, `Score = 41` (result overlaps) | `wrong answer: Invalid flip (1,2)` |
| each fixed hidden case + its first non-convex edge that the original rule allows (10 inputs) | 10/10 accepted | 10/10 `Invalid flip` |

The agent's local testing loop (working image):

| Submission | Original SAMPLE_TOTAL | Fixed SAMPLE_TOTAL |
|---|---:|---:|
| do nothing | 1,780,251 | 1,802,171 |
| greedy | 263,500 | 258,183 |
| nonconvex_flip | 1,780,471 (accepted) | all 3 `wrong answer: Invalid flip` |

The saved case-0009 output with the score-improving forbidden flip scores `Score: 641611` under the original verifier. It gives `INVALID: Invalid flip (39,52)` with the fixed `triangulation.py`. All 13 regenerated inputs have 0 overlapping pairs, 0 crossings, 0 folds, 0 duplicate or degenerate triangles and 0 non-manifold edges.

**Score compatibility:** fixed-version scores are **not comparable** with original scores, for three reasons:

- 9 of 10 hidden inputs are new instances.
- All inputs are now valid triangulations.
- The set of legal moves is smaller.

All four original reference points of the score scale are kept unchanged, as a fixed reference scale only. They no longer correspond to leaderboard ranks on the fixed version.

## How we checked it

- **Original grader.** The original `tools/bin/tester` and the full original `eval_cmd` ran in the original public image, pinned by digest, with `--network none`, for the original and fixed versions.
- **Independent check.** Exact integer geometry, with no floating point, ran on all 10 hidden cases and all 3 samples. It covers: an exact separating-axis overlap test for each triangle pair; proper edge crossings; vertices inside triangles; duplicate, degenerate and non-manifold triangles and edges; Euler characteristic and vertex links (two standard checks that a mesh is a proper surface); area excess against the convex hull; and collinear triples. On every interior edge, the official rule was compared with an independent exact convex-quadrilateral test.
- **Regeneration.** The shipped `gen.py` with seed 9000000 reproduces hidden case 0000 byte for byte. Seeds 1000001–1000003 reproduce all three samples byte for byte. (The O(N³) collinearity check was swapped for an exactly equivalent faster test.)
- **Repeatability.** The side-by-side run of the original and fixed graders was repeated three times; no verdict changed (`data/paired-repeatability.md`).

## Limits

- No AI model or solver was run. Score effects are shown only on test submissions we wrote.
- The original seeds for hidden cases 0001–0009 are unknown. Their K is inferred, not recovered.
- A side effect of the shipped Delaunay generator (its "super-triangle" construction) is left untouched. 12 of 13 fixed inputs miss 1–3 convex-hull triangles. Each is a valid triangulated polygon of all points, but not of the full hull. The README wording "a triangulation of those points" is slightly stronger than this. The wording is noted but not changed.
- The CodeChef TRICOL statement and checker were not consulted.
- The gain a strong solver gets from non-convex flips over a full optimization was not measured.
- The fixed images were built and tested locally for the run and then removed. They are not registry digests.

## Reproduce

- Geometry and rule analysis: `evidence/scripts/triangulation_coloring_optimization/check_geometry.py`, `flip_rule_analysis.py`, `regen_compare.py`, `run_gen.py`
- Regeneration for the fixed version and rule check: `evidence/scripts/triangulation_coloring_optimization/v2/regen_v2.py`, `v2/rule_check.py`
- Side-by-side run: `repairs/triangulation_coloring_optimization-v2/paired/run.sh` (results in `paired/results.md`)
- Patch: `repairs/triangulation_coloring_optimization-v2/repair.patch`
- Pinned identity: grader image `seededge/edgebench.judge.triangulation_coloring_optimization@sha256:beeea763…dcf671`; `triangulation.py` sha256 `32862fe5…`; `verifier.py` `1f0c714a…`; `gen.py` `67201f1e…`; `tools/bin/tester` `01b6e17b…`; hidden case 0000 `8e0c5efc…`.

Supporting records: `repairs/triangulation_coloring_optimization-v2/` (the folder holding the fixed version: source-lock.json, logs of the side-by-side run).
