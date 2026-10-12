# grid_turing_robot: formal note

## Claim
The shipped do-nothing solution totals 7,744,909 over the 50 cases. Under the task's
`piecewise_min` rescale (baseline anchor 9,025,986, rank30 4,490) it scores exactly
20·1,281,077/9,021,496 = 6405385/2255374 ≈ 2.84005 out of 100, not 0. Against the same scale
anchored at the measured 7,744,909, the extra credit is ≥ 0 for every raw score, at most
6405385/2255374, and 0 at or below rank30.

## Model and link to the code
Lean 4: `evidence/formal/lean/ebv/Ebv/GridTuringBaseline.lean` (output `GridTuringBaseline.out`).
- `pmin` = `score_rescale.py` lines 155-171 (sha256 98feb630…4b19). The branches below rank30 do
  not read the baseline and are an arbitrary function `low`.
- Anchors come from `tasks/grid_turing_robot.json` (sha256 b88eff20…3948).
- `baselineCases` holds the 50 CASE scores from `native/shipped_baseline.log` (sha256 bb916f62…aa9).
  `baseline_sum` proves that they sum to 7,744,909.
- Differential check: `baseline_score` gives 2.84005 and `diff_good` gives 19.8013…; these match
  `native/grade_out.txt` (2.8401 and 19.8014, rounded).

## Result
**Proved.** `baseline_score` gives the exact value, `baseline_score_bounds` shows
2.84 < v < 2.8401, and `offset_bounds` proves the bound on the offset for every raw score.

## Counter-check
- `counter_not_zero`: the baseline does not score 0 under the configured anchor.
- `counter_fixed_zero`: it does score 0 with anchor 7,744,909.
- `counter_too_strong`: "offset ≤ 2.84" is false, because the exact maximum is 2.84005. The
  published "at most 2.84 points" is therefore a rounding.

## Limits
- Exact rationals stand in for Python floats, and rounding is not modelled.
- The 50 per-case scores are taken from the saved original-grader log. The robot simulation is not
  modelled; it is covered by the independent oracle in `evidence/scripts/grid_turing_robot/`.
- The other two notes on this task are not formalized: (a) one failed case voids the submission,
  and (c) the dependence on CPU count. (a) is a property of the harness's validity check, and (c)
  is a timing condition of the execution environment, so neither is a scoring rule.
