# Paired v1/v2 results — triangulation_coloring_optimization-v2

One E2B job (`run.sh`; job dir `evidence/runs/triangulation-v2-paired`, worker
killed by exact ID, exit 0, ~41 s). v1 = original judge/work images pulled by digest; v2 = images
built in the worker from `../Dockerfile` and `../Dockerfile.work`. Original `eval_cmd`,
`--network none --memory 4g`. Raw logs in `result/out/`. Parsed with the maintained
`score_sum` parser rules and rescaled with `score_rescale.py` and the (unchanged) anchors
(`normalize.py` → `normalize.out.jsonl`). In-image sha256 checks (`result/out/hashes_*.txt`):
v2 differs from v1 exactly in `triangulation.py`, the 10 cases and the 3 sample inputs.

## Full judge (`eval_cmd`, 10 hidden cases)

| submission | role | v1 raw | v1 cases OK | v1 normalized | v2 raw | v2 cases OK | v2 normalized |
|---|---|---:|---|---:|---:|---|---:|
| shipped `solution.py` (do nothing) | valid control | 6,092,430 | 10/10 | 0.055 | 6,092,622 | 10/10 | 0.054 |
| `greedy.py` (greedy recolour + greedy README-legal convex flips) | independent honest control | 866,166 | 10/10 | 48.87 | 863,058 | 10/10 | 48.95 |
| `nonconvex_flip.py` (do nothing + one README-forbidden non-convex flip per case) | **trigger** | 6,093,050 | 10/10 accepted | 0.052 | inf | 0/10 (WA "Invalid flip") | 0 (invalid run) |
| `wrong_count.py` (recolours vertex 1, claims C=0) | invalid control | inf | 0/10 (WA) | 0 (invalid) | inf | 0/10 (WA) | 0 (invalid) |

Docker exit 0 for all eight runs (the evaluator always exits 0; `TOTAL_SCORE inf` makes the
maintained parser invalidate the run). Valid controls: normalized scores change by ≤0.08 points;
raw changes are fully explained by the new instances for cases 0001–0009 (same anchors).
The earlier review also showed a v1 forbidden flip that *improves* the score
(case 0009, edge 39–52: 644,809 → 641,611); re-scoring that saved output
(`scripts/triangulation_coloring_optimization/case0009_one_nonconvex_flip.out`) on the original
case 0009 locally: original verifier `Score: 641611`; verifier with v2 `triangulation.py`
`INVALID: Invalid flip (39,52)`.

## Same inputs, rule only (tester in each judge image; `rule_v1.log`, `rule_v2.log`)

| input | v1 tester | v2 tester |
|---|---|---|
| N=4 valid 2-triangle input with reflex quadrilateral, flip 1–2 (review control) | accepted, `Score = 41` (result overlaps) | `wrong answer: Invalid flip (1,2)` |
| each v2 hidden case + its first non-convex flippable-under-v1 edge (10 inputs) | 10/10 accepted | 10/10 `Invalid flip` |

## Solver-visible loop (work image `eval_sample_data.sh` + `tools/bin/tester`)

| submission | v1 SAMPLE_TOTAL | v2 SAMPLE_TOTAL |
|---|---:|---:|
| do nothing | 1,780,251 | 1,802,171 |
| greedy | 263,500 | 258,183 |
| nonconvex_flip | 1,780,471 (accepted) | all 3 `wrong answer: Invalid flip` |

So the local tester the prompt says "applies flips exactly like the judge" now enforces the
same README rule as the v2 judge.

## Input validity (review's exact-integer checker, `geometry_v2.jsonl`)

All 13 regenerated files: 0 overlapping triangle pairs, 0 crossing edge pairs, 0 folded edges,
0 duplicate/degenerate triangles, 0 non-manifold edges, 0 vertices strictly inside a triangle,
V−E+F = 1, 0 bad vertex links, 0 unused vertices, 0 collinear triples (checked during
generation). Residual: 12/13 miss 1–3 convex-hull triangles (shipped Delaunay artifact; see README).
Originals for comparison: 17–583 overlapping pairs per file (review).

## Flip predicate equivalence (`rule_check.jsonl`, 26 files)

On every original and v2 input: v2 predicate == independent exact convex-quadrilateral test on
every edge (0 mismatches), and v2 ⊆ v1 (0 edges allowed by v2 but not v1). v1 allows
1,250–1,503 edges per file; v2 allows 861–1,171.

## Verdict

Trigger: v1 wrong (accepts forbidden flip), v2 right (rejects). Valid controls: accepted in both,
normalized score unchanged within 0.08. Invalid control: rejected in both. **Accepted.**
