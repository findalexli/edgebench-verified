# jagua_nesting_optimization v2: paired evaluation

## Job

- **Run:** one E2B worker (sandbox `i48r9e7wrad9nueuy5qux`) ran `run.sh` in 643 s, exit 0, then
  was killed by its exact ID. Raw outputs are in `result/out/`.
- **v1:** `seededge/edgebench.judge.jagua_nesting_optimization@sha256:4f029bf7…`. In-image
  `evaluate.py` is `08159f8e…`.
- **v2:** built in the worker from `v2ctx/Dockerfile` (image `sha256:37fcf19e…`). In-image
  `evaluate.py` is `df296c87…`, the same as `files/`.
- **Unchanged in both images:** `score.sh` (`04459173…`) and the 16 scored assets
  (`pins_v1.txt`, `pins_v2.txt`).

## 1. Witnesses (`validate_solution` of each image; `witnesses_v1.txt`, `witnesses_v2.txt`)

The first eight are the reviewer's witnesses; the two orientation witnesses were added here.

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

## 2. Reference outputs on all 16 scored instances (`ref_validity.txt`)

- **Setup:** the frozen reference lbf ran with the scorer's own seeds and config. Each output
  was validated by v1 and by v2.
- **Validity:** all 16 are valid under both, with identical widths. Rotations include
  -180/-90/90 and the continuous `swim_cr` angles.
- **Overlap margin:** the largest pairwise relative overlap under v2 is exactly 0 on every
  instance.
- **Validation time:** v2 takes ≤ 0.23 s per layout. v1 takes up to 60 s (gardeyn4) and 18 s
  (gardeyn5).

## 3. Full original scorer (TaskSpec `eval.sh`, `--network none`)

v1 and v2 of the same submission ran concurrently with 3 CPUs each.

| Submission | Role | Image | valid | Raw TOTAL_SCORE | Cases OK / WA / RE | Case lines identical v1 = v2 (timings ignored) | Wall |
| --- | --- | --- | --- | ---: | --- | --- | ---: |
| Shipped baseline (candidate = reference) | valid control | v1 | true | 0.000000 | 0 / 16 / 0 | yes | 200 s |
| Shipped baseline | valid control | v2 | true | 0.000000 | 0 / 16 / 0 | yes | 38 s |
| seed_shift (honest: same LBF, different PRNG stream) | valid control | v1 | true | 1.644419 | 6 / 10 / 0 | yes | 117 s |
| seed_shift | valid control | v2 | true | 1.644419 | 6 / 10 / 0 | yes | 37 s |
| drop_last_item (one item missing) | invalid control | v1 | true | 0.000000 | 0 / 16 / 0, all `demand_mismatch` | yes | 191 s |
| drop_last_item | invalid control | v2 | true | 0.000000 | 0 / 16 / 0, all `demand_mismatch` | yes | 37 s |

Notes on the table:

- **Baseline.** Each case reads `ref=X,cand=X,impr=0%`, so both layouts were validated. The
  status is `WA` only because a zero score is labelled WA.
- **Scale.** The task has no `rescale`, so the normalized score is the raw score (`score_sum`
  parser).
- **`valid` column.** This is the harness's grading validity: the scorer completed and printed
  `TOTAL_SCORE`. Rejected layouts score 0 per case.

## Spec checks

- **Trigger.** All six positive-area overlap witnesses that v1 accepts, and the forbidden
  rotation, are rejected by v2. Legal edge contact and the tolerance-scale case stay
  accepted.
- **Valid controls.** On the official instances, the shipped baseline and an honest
  alternative solver get identical per-case results and identical totals (0 and 1.644419).
  Every reference layout validates under v2 with zero overlap.
- **Invalid control.** The missing-item layout is rejected on every case by both versions.
- **Verdict:** **accepted.**

## Not run

- No submission that exploits the overlap through the full scorer was run (good-faith scope).
  The trigger is shown on `validate_solution`, which is the scorer's only feasibility check.
- No stronger honest solver was run.
