# ffmpeg_swscale_reimplementation: formal note

## Claim

The original grader credits a timed call's speed whether or not it succeeds. The fixed grader
gives a failing or unverified call the least possible weight and changes nothing for submissions
whose timed calls all verify.

## Model and link to the code

`lean/ebv/Ebv/FfmpegTimedCredit.lean`, over ℝ:

- original `compute_reward.py` sha256 `2f457ffd…`: l.515-557 per-workload speedup and l.671-677
  geometric mean with the 1e-15 floor;
- fixed sha256 `6d4e1095…`: l.526-549 return code and last output, l.569-597 zeroing;
- `score_rescale.py` sha256 `98feb630…`, l.110-114 `log_anchor`, anchor 14.155 → 43.

The PSNR comparison is an opaque `outOk`.

## Result: proved

- `fixed_failing_never_helps`: under the fixed grader, a submission with a failing or unverified
  timed call never scores more than the same submission with that call replaced by any outcome at
  all. `fixed_unverified_floor`: the failing call's factor is exactly 1e-15.
- `fixed_eq_orig_of_verified`: if every timed call verifies, both graders compute the same speedup
  list, so the raw value and the score are the same.
- `geo_le_one_iff`: raw ≤ 1 exactly when the product of floored speedups is ≤ 1.
  `logAnchor_le_one`: raw ≤ 1 gives score 0. `score_pos_of_gt_one`: raw > 1 gives score > 0.
- Recorded data: Variant 1's ten recorded speedups (rgba→rgb24 4K at 16,468.9989×) give a
  product > 1, so the original score is positive (recorded 5.39). With that call zeroed the
  product is ≤ 1, so the fixed score is 0. The fixed raw values 0.000464, 0.000463 and 0.000451 all score 0.

## Counter-check

`orig_ignores_failure`: the original pays a call that returns −3 exactly as if it had succeeded.
`v1_orig_score_pos`: the original gives that call positive credit. `not_always_zero`: the claim
"any failing call makes the score 0" is too strong and is false. Nine verified workloads at 100×
plus one failure give a product of 1000 and a positive score.

## Limits

- Real arithmetic, not IEEE doubles. `round(geo, 6)` is omitted. PSNR, timing and the libraries are abstract.
- Only the **last** timed call's output is checked. Return codes are checked on all 110 calls.
- The code uses 40 dB for scaling and **60 dB for same-size conversions** (l.578-579, the
  `check_correctness` thresholds), so same-size workloads such as rgba→rgb24 4K are held to 60 dB.
  The case page and the README state both thresholds.
