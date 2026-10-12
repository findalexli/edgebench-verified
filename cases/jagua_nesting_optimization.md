# Jagua Nesting Optimization (`jagua_nesting_optimization`)

Status: reviewed by the coordinator, 2026-10-12

- **Domain:** Combinatorial Optimization
- **Decision:** Repair v2. The validator accepts large positive-area overlaps, such as identical placements, contained items and half-slid items. Because the score depends only on strip width, the original check cannot guarantee that a winning layout is feasible.

## What the task promises

The prompt says: "Keep outputs geometrically valid; the judge independently checks all placements." `SEBENCH_TASK.md` says that "illegal output, missing items, out-of-bounds placement, **overlaps**, timeout, or program crashes all result in a score of 0". The scorer's own docstring says it validates "independently in Python so that a submission cannot win by printing impossible strip widths". Contact at boundaries is allowed. No document allows overlap with positive area.

## What we checked and how

- We read `polygons_overlap` in the original `evaluate.py` to identify the mechanism.
- We ran eight hand-made witness layouts through the unchanged original `validate_solution` in the pinned judge image (`--network none --memory 1g --cpus 1`). The witnesses have integer coordinates, rotation 0 and strip height 20.
- Two independent area oracles: Shapely 2.2.0 and exact closed-form areas. The witnesses are integer rectangles, triangles and diamonds, so their closed-form areas are exact.
- The v2 overlap-area routine was checked against an exact rational Sutherland–Hodgman clip on random integer polygons.
- Paired v1/v2 evaluation in one E2B worker. It covered the witnesses, the frozen reference outputs on all 16 scored instances, and the full original scorer (`--network none`).
- Original identity:
  - judge image `seededge/edgebench.judge.jagua_nesting_optimization@sha256:4f029bf7…`
  - `evaluate.py` sha256 `08159f8e…`
  - `score.sh` `04459173…`

## What we found

**Confirmed, and broader than the earlier claim.** The original validator reports an overlap in only two situations: two edges cross properly, or a vertex of one polygon lies strictly inside the other. Any overlap with neither property is accepted.

This is not a floating-point tolerance effect. It happens with exact integer coordinates. Under the original evaluator:

- Two identical copies at the same pose were accepted. Expected: reject, because the overlap is 100% of the item's area.
- A square slid halfway along another equal-height square was accepted (overlap area 50).
- A rectangle, a triangle and a diamond each placed fully inside a square were accepted (overlap area 50 each). The diamond shares no edge with the square.
- Two squares shifted diagonally, where edges cross properly, were rejected. This shows ordinary overlaps are caught.
- An edge-sharing pair (legal contact) was accepted, as it should be.

Each accepted overlap is at least 25% of an item's area, about 10^6 times the validator's tolerance.

A side finding is that `validate_solution` never reads `allowed_orientations`, so rotations an instance forbids are not rejected.

**Maximum effect:** material. Infeasible layouts are accepted as valid. The score depends only on strip width, and every hidden instance has items with demand above 1. Layouts with overlapping items can therefore report less width than any feasible packing. This score effect is an inference from the code. It was not measured through the full scorer, which was deliberately not run with an overlap-exploiting submission.

An earlier audit note said that "five equal-width cases showed no score improvement". Re-checking showed these were diagnostic runs with equal reference and candidate width (5). They were not designed to test the defect, so they say nothing about score impact. That wording should be dropped.

## Repair

v2 changes only `jagua_task_scorer/evaluate.py`:

- **Overlap test.** A new `overlap_area` computes the exact intersection area of two simple polygons by vertical slab decomposition. `polygons_overlap` now rejects a pair when the intersection area exceeds 1e-6 × the smaller item's area. Boundary contact has zero area and stays legal.
- **Orientations.** A new `orientation_allowed` check rejects placements whose rotation is not in an item's `allowed_orientations` modulo 360°, when that field is present.
- **Unchanged:** the bounding-box prefilter, strip bounds, demand checks, score formula, runtime multiplier, reference, assets and work image.

An earlier repair candidate was reviewed and not reused. It had zero tolerance and did not enforce orientations.

Witnesses, run through each image's `validate_solution` (descriptions only; witness files are kept as internal records):

| Witness | Overlap area (exact) | v1 | v2 |
| --- | ---: | --- | --- |
| valid_adjacent_squares (shared edge) | 0 | accept | accept |
| coincident_squares | 100 (100%) | **accept** | reject `overlap_0_1` |
| half_slid_squares | 50 | **accept** | reject |
| rect_inside_square | 50 | **accept** | reject |
| triangle_inside_square | 50 | **accept** | reject |
| diamond_inside_square | 50 | **accept** | reject |
| diag_shift_squares (proper crossings) | 25 | reject | reject |
| tiny_overlap_1e-6 (relative overlap 1e-7) | 1e-5 | accept | accept (below the 1e-6 relative tolerance) |
| forbidden_rotation_90 (allowed [0]) | – | **accept** | reject `orientation_not_allowed_0` |
| allowed_rotation_minus180 (allowed [0, 180]) | – | accept | accept |

Full original scorer (TaskSpec `eval.sh`, `--network none`):

| Submission | Role | Image | valid | Raw TOTAL_SCORE | Cases OK / WA / RE | Case lines identical v1 = v2 (timings ignored) | Wall |
| --- | --- | --- | --- | ---: | --- | --- | ---: |
| Shipped baseline (candidate = reference) | valid control | v1 | true | 0.000000 | 0 / 16 / 0 | yes | 200 s |
| Shipped baseline | valid control | v2 | true | 0.000000 | 0 / 16 / 0 | yes | 38 s |
| seed_shift (honest: same LBF, different PRNG stream) | valid control | v1 | true | 1.644419 | 6 / 10 / 0 | yes | 117 s |
| seed_shift | valid control | v2 | true | 1.644419 | 6 / 10 / 0 | yes | 37 s |
| drop_last_item (one item missing) | invalid control | v1 | true | 0.000000 | 0 / 16 / 0, all `demand_mismatch` | yes | 191 s |
| drop_last_item | invalid control | v2 | true | 0.000000 | 0 / 16 / 0, all `demand_mismatch` | yes | 37 s |

The baseline's cases are labelled `WA` only because a zero score is labelled WA. Each case reads `ref=X,cand=X,impr=0%`. The task has no rescale, so the normalized score equals the raw score.

Further checks:

- All 16 frozen reference layouts are valid under both versions, with identical widths. Their largest pairwise relative overlap under v2 is exactly 0.
- The oracle comparison found 0 mismatches in 7526 comparisons, with a maximum absolute error of 3.4e-13.

**Score compatibility:** valid layouts with no overlap above the tolerance and only allowed rotations validate and score identically in v1 and v2. Scores differ in three situations:

- A layout contains a positive-area overlap that v1 missed. That case becomes `WA` with score 0 in v2.
- A layout uses a forbidden rotation.
- A layout contains a sub-tolerance proper crossing that v1 rejected. v2 accepts it, limited to 1e-6 of an item's area.

## Limits and what was not run

- No model or solver re-runs. Effects are shown only on authored controls and counterexamples.
- No submission that exploits the overlap was run through the full scorer. The trigger is shown on `validate_solution`, the scorer's only feasibility check. Score inflation is therefore inferred, not measured.
- The witnesses are hand-made instances, not hidden assets.
- The area oracle covers concave-against-convex polygon pairs. Concave-against-concave pairs are covered only by the witnesses and the reference layouts.
- v2 uses floating point, as the original does. It is exact only up to rounding, which is far below the tolerance.
- No adversarial or near-tolerance layouts beyond the witnesses were built, and no stronger honest solver was run.
- Scorer isolation is outside this release's scope (EdgeBench design choice).

## Reproduce

- Paired evaluation: `repairs/jagua_nesting_optimization-v2/paired/run.sh` (results in `paired/results.md`)
- Area oracle and reference-overlap checks: `evidence/scripts/jagua_nesting_optimization/v2/oracle_area_check.py`, `v2/max_overlap.py`
- Patch: `repairs/jagua_nesting_optimization-v2/repair.patch`

Supporting records: `repairs/jagua_nesting_optimization-v2/` (source-lock.json, paired logs).

