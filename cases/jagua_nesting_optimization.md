# Jagua Nesting Optimization (`jagua_nesting_optimization`)

**Decision:** Repair (v2). The original validator accepts large positive-area overlaps, such as identical placements, contained items and half-slid items, so it cannot guarantee that a winning layout is feasible.

## What the task asks for

The solver packs polygon items into a strip of fixed height and minimizes the strip width. The prompt says: "Keep outputs geometrically valid; the judge independently checks all placements." `SEBENCH_TASK.md` says that "illegal output, missing items, out-of-bounds placement, **overlaps**, timeout, or program crashes all result in a score of 0". Contact at boundaries is allowed; no document allows overlap with positive area. Category: Combinatorial Optimization.

## What goes wrong

**Overlaps are missed.** The original `polygons_overlap` reports an overlap in only two situations: two edges cross properly, or a vertex of one polygon lies strictly inside the other. Any overlap with neither property is accepted. This is not a floating-point effect; it happens with exact integer coordinates.

Examples under the original evaluator (integer coordinates, rotation 0, strip height 20):

- Two identical copies at the same pose: expected reject (overlap is 100% of the item's area); observed **accept**.
- A square slid halfway along another equal-height square (overlap area 50): **accept**.
- A rectangle, a triangle and a diamond each placed fully inside a square (overlap area 50 each): **accept**. The diamond shares no edge with the square.
- Two squares shifted diagonally, where edges cross properly: reject, as expected.
- An edge-sharing pair (legal contact): accept, as expected.

Each accepted overlap above is 50–100% of an item's area, about 10^6 times the validator's tolerance (`EPS = 1e-5`).

**Forbidden rotations are not checked.** `validate_solution` never reads `allowed_orientations`, so rotations an instance forbids are accepted.

Why it matters: the score depends only on strip width, and every hidden instance has items with demand above 1. A layout with overlapping items can report less width than any feasible packing.

## Impact

Material for any submission whose layout contains such an overlap: infeasible layouts are accepted as valid and can beat every feasible one. This score effect is inferred from the code; it was not measured through the full scorer with an overlap-exploiting submission. Honest, non-overlapping layouts are unaffected.

## Fix (v2)

v2 changes only `jagua_task_scorer/evaluate.py`:

- **Overlap test.** A new `overlap_area` computes the exact intersection area of two simple polygons by vertical slab decomposition. `polygons_overlap` now rejects a pair when the intersection area exceeds 1e-6 × the smaller item's area. Boundary contact has zero area and stays legal.
- **Orientations.** A new `orientation_allowed` check rejects placements whose rotation is not in an item's `allowed_orientations` modulo 360°, when that field is present.
- **Unchanged:** the bounding-box prefilter, strip bounds, demand checks, score formula, runtime multiplier, reference, assets and work image.

Witnesses, run through each image's `validate_solution`:

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

The baseline's cases are labelled `WA` only because a zero score is labelled WA; each case reads `ref=X,cand=X,impr=0%`. The task has no rescale, so the normalized score equals the raw score. All 16 frozen reference layouts are valid under both versions, with identical widths, and their largest pairwise relative overlap under v2 is exactly 0.

**Score compatibility:** valid layouts with no overlap above the tolerance and only allowed rotations validate and score identically in v1 and v2. Scores differ in three situations:

- A layout contains a positive-area overlap that v1 missed. It becomes `WA` with score 0 in v2.
- A layout uses a forbidden rotation.
- A layout contains a sub-tolerance proper crossing that v1 rejected. v2 accepts it, limited to 1e-6 of an item's area.

## How we know

- **Original evaluator in the pinned image.** The witnesses ran through the unchanged `validate_solution` in the judge image (`sha256:4f029bf7…`) with `--network none --memory 1g --cpus 1`.
- **Independent area oracles.** Shapely 2.2.0 and exact closed-form areas (the witnesses are integer rectangles, triangles and diamonds). The v2 overlap-area routine was also checked against an exact rational Sutherland–Hodgman clip on random integer polygons: 0 mismatches in 7526 comparisons, with a maximum absolute error of 3.4e-13.
- **Paired evaluation.** The witnesses, the frozen reference outputs on all 16 scored instances, and the full original scorer gave the tables above. The paired evaluation was repeated three times with no verdict change ([`paired-repeatability.md`](../paired-repeatability.md)).

## Limits

- No model or solver runs. Effects are shown only on authored controls and counterexamples.
- No overlap-exploiting submission was run through the full scorer. The trigger is shown on `validate_solution`, the scorer's only feasibility check, so score inflation is inferred, not measured.
- The witnesses are hand-made instances, not hidden assets.
- The area oracle covers concave-against-convex polygon pairs. Concave-against-concave pairs are covered only by the witnesses and the reference layouts.
- v2 uses floating point, as the original does. It is exact only up to rounding, which is far below the tolerance.
- No adversarial or near-tolerance layouts beyond the witnesses were built, and no stronger honest solver was run.

## Reproduce

- Paired evaluation: `repairs/jagua_nesting_optimization-v2/paired/run.sh` (results in `paired/results.md`).
- Area oracle and reference-overlap checks: `evidence/scripts/jagua_nesting_optimization/v2/oracle_area_check.py`, `v2/max_overlap.py`.
- Patch: `repairs/jagua_nesting_optimization-v2/repair.patch`.
- Supporting records: `repairs/jagua_nesting_optimization-v2/` (source-lock.json, paired logs).
