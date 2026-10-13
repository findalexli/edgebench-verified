# treant_forest (score cap and score scales)

## Claim

1. No submission's per-case score exceeds 2N², and TOTAL_SCORE never exceeds Σ 2N_i².
2. With Σ 2N_i² = 92,304, the original `piecewise_max` scale gives at most exactly
   2543510/121003 ≈ 21.02 to any reachable total; the fixed `linear(3418, 92304)` maps
   3,418 → 0 and 92,304 → 100.
3. IMPACT.md inversion: for s in (0, 20), the unique raw total with original score s is
   5369 + s/20·82820, and its fixed score is 100(1951 + 4141 s)/88886. The five published
   values 18.0, 15.6, 13.3, 16.9, 13.5 become 86.05, 74.87, 64.16, 80.93, 65.09.

## Model and link to the code

`evidence/formal/lean/ebv/Ebv/TreantRescale.lean` (output `TreantRescale.out`).
`clip`, `linear`, `piecewiseMax` follow `sforge/harness/score_rescale.py` lines 60–63, 80–84 and
137–153 (sha256 `98feb630…4b19`). The tester's turn counter (`tools/bin/tester`, sha256
`6cbb3a72…8551`, lines 63, 65, 140–145, 202, 245–250) is the function `loop`. The loop body
is reduced to two arbitrary stop predicates. TOTAL_SCORE (sum over OK cases,
`eval_treants_forest.py` sha256 `ce2833ac…2048`, lines 52–58) is `total`. Differential check:
the saved Python value `rescaled_cap = 21.02022263910812` lies within 1e-13 of the exact value.

## Result

**Partly proved.** Claims 1 and 3 and the scale arithmetic in claim 2 are proved exactly,
along with the case-page table values: 5369 → 97550/44443, greedy 17960 → 3.04 / 16.36, and
rank1/cap ≈ 3.58. The number 92,304 is **not** re-derived: the 50 shipped case files (listing
sha256 `bc256294…`) are not in the repository. `.internal/repeatability-work/treant_cases` is
empty, and the judge image is not present locally. Regenerating the cases with `gen` from seeds
0–49 or 1–50 does not reproduce the listing hash. 92,304 is therefore a named input
(`capTotal`), taken from `check_arith.out.json`.

## Counter-check

`counter_orig_cap_gt_21` (the bound 21 is false) and `counter_orig_cap_ne_100`.
`counter_inv_above_20`: inv(20.5) lands on segment 2 and scores 20.513, so the formula fails
above 20. `counter_inv_at_zero`: the formula also fails for a run whose original score is 0.

## Limits

- **Caveat for IMPACT.md.** The inversion of an average of runs is exact only if every run's raw
  total lies in (5369, 88189]. IMPACT.md names only the 20–21.02 exception. A run with raw
  ≤ 5,369 also scores 0 on the original scale, but between 0 and 2.19 on the fixed one.
  Treating it as raw 5,369 overstates the fixed average by up to 2.19/k points (k = number of
  valid runs). The other exception, a run in 20–21.02, overstates by at most about 0.12/k.
  Lean shows only that the formula fails in these two cases (`counter_inv_at_zero`,
  `counter_inv_above_20`). The sizes 2.19/k and 0.12/k are computed, not proved: fixed(5369) =
  97550/44443 ≈ 2.195, and at 21.0202 the formula's raw total 92,413.8 exceeds the true 92,304 by
  109.7 turns, which is 0.123 points on the fixed scale.
- The five converted values are exact for the published one-decimal inputs. An input known to
  ±0.05 gives a fixed score known to ±0.23 (slope 100·4141/88886 ≈ 4.66 per point).
- 92,304 is an upper bound on the raw total (claim 1). That some submission reaches it on every
  case is not proved, so 21.02 is the highest score the original scale can give, not one a
  submission is shown to reach.
- The proofs use exact rationals, while the grader uses doubles.
- The tester's movement rules are abstracted away. Only the counter bound is used.
