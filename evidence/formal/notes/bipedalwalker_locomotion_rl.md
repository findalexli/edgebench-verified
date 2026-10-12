# bipedalwalker_locomotion_rl: formal note

## Claim
For every pair of mean rewards and every outcome of the four engineering checks, the score out of
100 lies in [0, 30]. 30 is attained. With three or fewer checks passing the score is at most 27.5.
The `min(30, …)` in the code never binds, because 10 points for checks plus 20 points for reward
already make 30. The case-table values are 2.5, 10, 18 and 30.

## Model and link to the code
Lean 4: `evidence/formal/lean/ebv/Ebv/BipedalCap.lean` (output `BipedalCap.out`).
- Source: work-image `loco-rl/sebench_eval.py`, sha256 9bb2f8bf…838a (the hash cited in
  `_game-tasks-correctness.md` §10).
  - Lines 39-48 give the reward scores; lines 122-126 give `strict_score`.
  - Lines 148-204 append exactly one detail per engineering name, so `e ≤ 4`.
  - Lines 169-173 and 197-198 give the not-evaluated defaults.
- Rescale: `score_rescale.py` lines 80-84 with lower 0 and upper 100 (task JSON).
- The cap is stated in `task_prompt.md` lines 117-118 (sha256 e4023718…cf).

## Result
**Proved.** The theorems are `score100_bounds`, `min_never_binds`, `perfect_30` and
`needs_all_checks`. The differential check `table_missing`, `table_untrained` and
`table_normal_only` reproduces the case table exactly.

## Counter-check
- `counter_not_below_30`: "score < 30 always" is false.
- `counter_100_unreachable`: the upper anchor of 100 is unreachable.
- `counter_e5_uncapped`: with a hypothetical fifth check the uncapped sum would be 32.5, so only
  then would `min 30` act.

## Limits
- The model assumes the evaluator subprocess reports a mean reward, or the -200 default. The
  episode simulation and checkpoint loading are not modelled.
- `round(score, 2)` is not modelled.
- The silent partial-loading note (`strict=False`) is not formalizable as a scoring rule: it is a
  property of PyTorch state-dict loading.
- The grader image digest is not recorded. The source is the work-image copy.
