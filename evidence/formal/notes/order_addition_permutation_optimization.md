# order_addition_permutation_optimization

## Claim

Under the task's selection rule `pass_rate_first` (EdgeBench's `sforge/harness/selection.py` at `6e4e5f4`, l.51-80: a later submission replaces the best only with a strictly higher pass rate; scores are compared only when both rates are 1.0), (C1) the original grader's run best is always the **first** valid submission; (C2) the fixed grader's run best is the **highest-scoring** valid submission (earliest among equal scores), reported as a real score at pass rate 1.0. Also: (C4) `score_first` ("best so far by score") is the same under both versions, and (C5) on runs where every scored submission is valid it agrees with fixed `pass_rate_first`.

## Model and link to the code

`evidence/formal/tla/order_addition_permutation_optimization/OrderSelection.tla`. A run is a sequence of up to N = 4 submissions. Each submission is reduced to the set of non-fingerprint tests it passes (`test_final_result.py` l.74-144) and its TOTAL_SCORE (1..3). Both graders and both selection policies run side by side on the same sequence. The header maps every definition to source lines and sha256 (test file v1 `4f1d5fad…`, v2 `37e7bae6…`; EdgeBench's `grading.py` `ba15c46d…` and `selection.py` `abb55b7b…`). The model follows EdgeBench's grading: `extract_score` takes the first `TOTAL_SCORE`, so a submission failing T1 scores 0 even if T5 also prints a score. `diff_check.py` checks C1, C2, C4 and C5 against the **real** `select_best` on all 112,944 runs of length 1-3 over the same alphabet. It also replays the four recorded paired histories from `paired/graded.json`. Every check agrees.

## Result

**Model-checked** (bounded): TLC explored 5,421,361 states with no violation (`tlc-claims.out`). (Re-checked 2026-10-12 against EdgeBench's original harness; the first version of the model cited a locally modified `selection.py` and dropped T1-fail/T5-pass submissions as grading errors. Every claim and counter-check outcome is unchanged.) The published finding and fix are confirmed.

## Counter-check

- `k1`: the original grader picks the best valid score. Violated: identity (score 1) then search (score 2) keeps identity.
- `k2`: fixed `pass_rate_first` equals `score_first`. Violated: `score_first` also ranks scored submissions that break the contract.
- `k3`: `best_score` is never a pass rate. Violated in both versions (see Limits).

## Limits

- Bounded to 4 submissions and 3 score values. The selection rule does not depend on magnitudes, and the exhaustive Python check over real code covers length ≤ 3.
- The model assumes the helper and `.so` bytes are unchanged, so the fingerprint test outcome is fixed.
- **Side finding (both versions):** when no submitted entry has a score, `pass_rate_first` reports the pass rate as `best_score` (l.65). A run whose only submission is badcost gets best_score 0.6 (v1) or **0.8 (v2)**. With the linear 0-100 rescale, that is above a valid identity run (3.3e-09). The repair README's compatibility note now describes this fallback change ("One further change comes from the harness rather than the task"), and so does the case page's Limits.
