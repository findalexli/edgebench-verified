# warehouse_forklift_routing (time-budget arithmetic)

## Claim

- The promised budget is 5 test cases × 30 s = 150 s per input. That equals the fixed
  `TIME_LIMIT`, and it is 2.5× the original 60 s.
- The 13 s-per-case test submission (65 s per input) is within the promise but over 60 s.
- Worst case for the whole evaluation: ⌈50/8⌉ = 7 waves × (150 s + 30 s tester) = 1,260 s,
  under `eval_timeout` 3,600 (the original gives 630 s).

## Model and link to the code

`Ebv/TimeBudgets.lean` (output `TimeBudgets.out`), warehouse section. It models
`/tmp/eval_warehouse_manager.py` (fixed copy sha256 `eff6a69b…7b95`): `TIME_LIMIT` on line 9
(60 → 150 in `repair.patch`), the solver timeout on lines 16–18, the tester timeout of 30 s on
lines 24–25 and `max_workers=min(8, …)` on line 42. `eval_timeout` 3600 is from
`tasks/warehouse_forklift_routing.json`, line 20. T = 5 and 30 s per case come from the prompt
as quoted on the case page.

## Result

**Proved** as arithmetic. All the published numbers (150, 60, 1,260 and 3,600) reproduce. The
≈30.3 ceiling involves logarithms and is covered by the existing `WarehouseBound.lean` and its
related files, not here.

## Counter-check

- `counter_orig_limit`: 5 × 30 ≤ 60 is false.
- `counter_six_waves`: 6 × 8 < 50, so a seventh wave is needed.

## Limits

- The "7 waves" bound treats `ProcessPoolExecutor` as filling waves. The pool actually hands
  inputs to workers greedily. A short argument shows that greedy dispatch with every job
  ≤ M also finishes by ⌈n/8⌉·M: in each window of length M, every worker that was busy
  finishes and takes a new input. This argument is not formalised.
- Pool start-up, process spawn and kill overheads, and CPU contention between 8 parallel
  solvers are not modelled.
