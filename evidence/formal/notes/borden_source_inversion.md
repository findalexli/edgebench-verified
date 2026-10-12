# borden_source_inversion (fixed score scale)

## Claim

The fixed scale linear(0, 109) equals 100·raw/109 on [0, 109]. Applied to the published raw
values 48.4, 38.5, 8.0, 15.1 and 38.2, it gives 4840/109 ≈ 44.40, 3850/109 ≈ 35.32,
800/109 ≈ 7.34, 1510/109 ≈ 13.85 and 3820/109 ≈ 35.05. These round to IMPACT.md's
44.4, 35.3, 7.3, 13.9 and 35.0.

## Model and link to the code

`Ebv/BordenScale.lean` (output `BordenScale.out`). `rescale` models
`sforge/harness/score_rescale.py`: lines 43–45 (no spec gives None), 72–73 (a None spec
gives None) and 80–84 (`linear`). The original task JSON has no `rescale`, so its spec is
`none`. The fixed spec, `task.json.in` lines 32–36, is (0, 109). The published values and the
formula come from `tools/estimate_impact.py` (`borden_v2`).

## Result

**Proved.** The five values, their two-decimal intervals, the end points (0 → 0 and
109 → 100) and the strict monotonicity of the unclipped map are all proved.

## Counter-check

`counter_orig_undefined`: the original rescale returns `none` for every raw value.
`counter_not_identity`: 48.4 is not mapped to 48.4. `counter_default_clip_ties`: a default
clip(raw, 0, 100) reading would tie 100 with 109, while the fixed scale separates them.

## Limits

- The proof covers the change of scale only. The larger part of the fix, documenting the
  convention so that honest fits rise from about 7 to about 31, cannot be formalised from
  published numbers.
- That 109 is the maximum raw score is not proved. 109 is the true source's score according
  to the case page.
- The proofs use exact rationals, while the grader uses doubles.
