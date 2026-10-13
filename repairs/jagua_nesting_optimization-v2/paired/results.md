# jagua_nesting_optimization v2: paired evaluation

## Job

- **Superseded.** Sections 1–3 are the run of the first fixed version (v2, orientation tolerance
  1e-6°, tag `bba393b2dd53-ebv-v2`). The current fixed version is v2.1; see "Revision v2.1" below.
- **Run:** one E2B worker, ledger job `paired` (sandbox `i48r9e7wrad9nueuy5qux`), ran `run.sh` in
  643 s, exit 0, then was killed by its exact ID. Raw outputs are in `result/out/`. Repeats:
  ledger jobs `jagua_nesting_optimization-v2-paired-rep2` and `-rep3` (`evidence/runs/`).
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

## Revision v2.1 (2026-10-13): orientation tolerance 1e-3°

**Why.** v2 accepted an allowed angle only within 1e-6°. The original grader never reads
`allowed_orientations` and accepts every rotation, so this tolerance was introduced by our fix,
and it is below f32 angle resolution. A solver that keeps angles in f32 radians and prints them
in f64 degrees writes 90.00000250447816 for 90°, and v2 rejected it. v2.1 changes only that
tolerance, to 1e-3° (README, "Revision v2.1").

**Job.** `run3.sh` (staged as `run.sh` in `evidence/runs/jagua_nesting_optimization-v2.1-paired-rep1`,
`-rep2`, `-rep3`), one E2B worker per run, each `status: exit=0` in the ledger and killed by
exact ID. Three graders on the same inputs:

- **v1:** the original image `sha256:4f029bf7…` (in-image `evaluate.py` `08159f8e…`).
- **v2 (superseded):** built from `v2ctx/` with `evaluate.py` `df296c87…`.
- **v2.1 (current):** built from `v21ctx/` (= `../Dockerfile`) with `evaluate.py` `2c3c189e…`,
  the same as `files/`.

`score.sh` (`04459173…`) and the 16 scored assets are identical in all three images
(`pins_v1.txt`, `pins_v2.txt`, `pins_v2.1.txt`). v1 and v2.1 of each submission ran concurrently
with 3 CPUs each, then v2 with 3 CPUs.

### Witnesses (`validate_solution` of each image)

The ten witnesses of section 1 give the same verdicts under v2.1 as under v2. The eight new
orientation witnesses use one 10×5 rectangle in a strip of height 20:

| Witness | Rotation written | v1 | v2 | v2.1 |
| --- | --- | --- | --- | --- |
| f32_rot90_f64deg (allowed [0, 90, 180, 270]) | 90.00000250447816 | accept | reject `orientation_not_allowed_0` | accept |
| f32_rot180_f64deg (allowed [0, 180]) | 180.00000500895632 | accept | reject `orientation_not_allowed_0` | accept |
| f32_rot_minus90_f64deg | -90.00000250447816 | accept | reject `orientation_not_allowed_0` | accept |
| f32_rot270_f64deg | 270.00000068324533 | accept | accept | accept |
| near_tol_rot_90.0009 (0.9 × the v2.1 tolerance) | 90.0009 | accept | reject `orientation_not_allowed_0` | accept |
| wrong_rot_90.002 (2 × the v2.1 tolerance) | 90.002 | accept | reject `orientation_not_allowed_0` | reject `orientation_not_allowed_0` |
| wrong_rot_90.01 (10 × the v2.1 tolerance) | 90.01 | accept | reject `orientation_not_allowed_0` | reject `orientation_not_allowed_0` |
| wrong_rot_45 (allowed [0, 90, 180, 270]) | 45.0 | accept | reject `orientation_not_allowed_0` | reject `orientation_not_allowed_0` |

### Reference outputs in three forms (`ref_validity.txt`, `ref_validity3.py`)

The frozen reference lbf ran on all 16 scored instances with the scorer's seeds. Each output was
validated as written (`ref`), with every angle replaced by its f32 radians printed as f64 degrees
(`f32deg`, largest change 5.0e-6°, 1.0e-5° on `swim_cr`), and with every angle + 0.01°
(`wrong`).

| Form | v1 | v2 | v2.1 |
| --- | --- | --- | --- |
| ref | 16 / 16 valid | 16 / 16 valid | 16 / 16 valid, identical widths |
| f32deg | 16 / 16 valid | 1 / 16 valid (`swim_cr`, free rotation); 15 `orientation_not_allowed` | 16 / 16 valid, same widths as ref |
| wrong | 0 / 16 valid (9 `overlap`, 7 `out_of_strip`) | 1 / 16 valid (`swim_cr`); 15 `orientation_not_allowed` | 1 / 16 valid (`swim_cr`); 15 `orientation_not_allowed` |

The largest pairwise relative overlap of every reference layout under v2.1 is exactly 0.

### Full original scorer (TaskSpec `eval.sh`, `--network none`)

Run 1 of 3. "Cases" is OK / WA / RE. Case lines are compared with timings and the runtime
multiplier field removed (the multiplier is 1.000 on every case of every run).

| Submission | Role | v1 raw TOTAL_SCORE | v2 raw TOTAL_SCORE | v2.1 raw TOTAL_SCORE | Cases v1 | Cases v2 | Cases v2.1 | Case lines v1 = v2.1 |
| --- | --- | ---: | ---: | ---: | --- | --- | --- | --- |
| Shipped baseline (rev. v2.1) | valid | 0.000000 | 0.000000 | 0.000000 | 0 / 16 / 0 | 0 / 16 / 0 | 0 / 16 / 0 | yes |
| seed_shift (rev. v2.1) | valid | 1.644419 | 1.644419 | 1.644419 | 6 / 10 / 0 | 6 / 10 / 0 | 6 / 10 / 0 | yes |
| drop_last_item (rev. v2.1) | invalid | 0.000000 | 0.000000 | 0.000000 | 0 / 16 / 0 | 0 / 16 / 0 | 0 / 16 / 0 | yes |
| seed_shift_f32deg (honest: seed_shift with f32-derived angles) | valid | 1.644419 | 0.186857 | 1.644419 | 6 / 10 / 0 | 1 / 15 / 0, 15 `orientation_not_allowed` | 6 / 10 / 0 | yes |
| seed_shift_wrongdeg (every angle + 0.01°) | invalid | 0.000000 | 0.186857 | 0.186857 | 0 / 16 / 0: 8 `overlap`, 7 `out_of_strip`, 1 valid without improvement (case 0012, `gardeyn3`) | 1 / 15 / 0, 15 `orientation_not_allowed` | 1 / 15 / 0, 15 `orientation_not_allowed` | no (`swim_cr`) |

Notes on the table:

- **f32 arm.** `subs/seed_shift_f32deg` is `seed_shift` plus a post-processing step that rewrites
  each exported angle `r` as `((r as f32).to_radians() as f64).to_degrees()`. Under v2.1 its case
  lines equal those of `seed_shift`. v2 scores only `swim_cr` (case 0007, 0.186857), the instance
  with free rotation, and rejects the other 15 cases, including all five other cases that
  `seed_shift` scores.
- **Wrong-angle arm.** v2 and v2.1 reject all 15 instances that list allowed orientations as
  `orientation_not_allowed`. v1 rejects 15 cases through geometry and accepts one (`gardeyn3`,
  wider than the reference, score 0). On `swim_cr` any angle is allowed. There v1 rejects the rotated layout
  as `overlap_39_41` through its crossing test, while v2 and v2.1 accept it because its overlap is
  below the 1e-6 relative area tolerance. This is the leniency stated under "Score compatibility" in
  the README, and v2 and v2.1 behave the same way here. It is not caused by the orientation
  tolerance.

### Spec checks (v2.1)

- **Trigger of the revision.** f32-derived angles are accepted again: v2.1 gives the f32 arm the
  same per-case result as v1 and as `seed_shift` (1.644419), where v2 gave 0.186857.
- **Wrong angles stay rejected.** Angles 2×, 10× and 45° away from every allowed angle are
  rejected by v2.1 in the witnesses, and +0.01° is rejected on every instance that lists allowed
  orientations.
- **Unchanged controls.** Baseline, seed_shift and drop_last_item have identical case lines
  under v1, v2 and v2.1. All overlap witnesses keep their v2 verdicts.
- **Verdict:** **accepted.**

### Repeatability (v2.1 revision, 2026-10-13)

The revision run was repeated three times on separate E2B workers. All three have `status: exit=0`
in `evidence/runs/ledger.jsonl` and were killed by exact ID:

| Run | Ledger job | Sandbox | Elapsed |
| --- | --- | --- | ---: |
| 1 | `jagua_nesting_optimization-v2.1-paired-rep1` | `im9a41nijkzl5aror41py` | 944 s |
| 2 | `jagua_nesting_optimization-v2.1-paired-rep2` | `irv7xt6lb1667zpyetrnb` | 863 s |
| 3 | `jagua_nesting_optimization-v2.1-paired-rep3` | `ignhi3fmff03r13qiswi4` | 884 s |

Raw TOTAL_SCORE in each run (v1 / v2 / v2.1):

| Submission | Run 1 | Run 2 | Run 3 |
| --- | --- | --- | --- |
| Shipped baseline | 0.000000 / 0.000000 / 0.000000 | 0.000000 / 0.000000 / 0.000000 | 0.000000 / 0.000000 / 0.000000 |
| seed_shift | 1.644419 / 1.644419 / 1.644419 | 1.644419 / 1.644419 / 1.644419 | 1.644419 / 1.644419 / 1.644419 |
| drop_last_item | 0.000000 / 0.000000 / 0.000000 | 0.000000 / 0.000000 / 0.000000 | 0.000000 / 0.000000 / 0.000000 |
| seed_shift_f32deg | 1.644419 / 0.186857 / 1.644419 | 1.644419 / 0.186857 / 1.644419 | 1.644419 / 0.186857 / 1.644419 |
| seed_shift_wrongdeg | 0.000000 / 0.186857 / 0.186857 | 0.000000 / 0.186857 / 0.186857 | 0.000000 / 0.186857 / 0.186857 |

With timings removed, every case line of all 15 scorer runs (5 submissions × 3 graders) is
identical across the three runs, and so are the witness verdicts of all three graders and the
`ref_validity.txt` verdicts and widths. The runtime multiplier is 1.000 on every case.
