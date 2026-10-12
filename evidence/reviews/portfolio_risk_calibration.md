# Review: portfolio_risk_calibration (annualized excess return formula)

## Claim under review

Earlier claim (verbatim): "The evaluator annualizes the period-return difference instead of
subtracting aligned annualized returns. The same 126-observation native witness yields 21% instead
of 23%; seven unaffected metrics are preserved."

Earlier disposition: withhold the exact original (`ADOPT_EXACT_ORIGINAL_WITHHOLDING`,
`evidence/selected/portfolio-original-exclusion.json`). A finite two-line metric repair was
accepted but not certified (`portfolio-native-repair-acceptance.json`).

## Pinned artifacts

- Task: `tasks/portfolio_risk_calibration.json` sha256 `0343ac03f42042ff9053cb1809d106dac9311e5fe7d9bab353eab4ad1b078cb1`
  (`eval_cmd` `python3 scoring/score.py`, which runs the manifest command, which runs `eval_script.py`).
- Judge image: `seededge/edgebench.judge.portfolio_risk_calibration@sha256:42997fb5770532b08cf9b97927d28f34466868348cc75ae13824b81c90e9458d`
  (pulled and run locally).
- `scoring/eval_script.py` `829eeee186f02fba42e4291fea94523a8a7c89cf62c7e534c77115cb8eea4f9b`
  (identical in the image and in the extracted sources). `input/task_instruction.md`
  `a903d2361d017c92fe8b2e6975fafbea485d9b031d5e6231a7989bf3216cd191`.
- Hidden test data: `etf_prices_test.csv` has 243 distinct dates, of which 242 NAV days are in the
  evaluation period (from the run log). `test_period.txt` is `2025-01-01,2025-12-31`.

## Contract

The task prompt (`agent_query` / `task_instruction.md`) defines the convention outright, so it is
not left open:

- "Excess return = strategy annualized return - benchmark annualized return."
- "Information ratio = annualized excess return / tracking error."
- "Sortino ratio = annualized excess return / downside deviation."
- Thresholds: excess ≥ 12% is full marks, and a negative excess is deducted.

The reviewer brief raised a fair point: finance has several accepted definitions (annualize the
excess series, geometric excess, difference of annualized returns). Here the task chooses one,
the arithmetic difference of the two annualized returns. The evaluator's convention is none of
the three standard ones. It annualizes the difference of *period* returns:

```python
bench_total = bench_aligned.iloc[-1] / bench_aligned.iloc[0] - 1
benchmark_annual_return = (1 + bench_total) ** (252 / len(common_idx)) - 1
agent_total = agent_aligned.iloc[-1] / agent_aligned.iloc[0] - 1
excess_total = agent_total - bench_total
excess_annual = (1 + excess_total) ** (252 / len(common_idx)) - 1      # eval_script.py:925-928
```

It does not compound daily excess (that would be path-dependent), and it is not the geometric
ratio. It is a hybrid that matches the stated definition only when the exponent is 1.

## Independent reproduction

Scripts are in `evidence/scripts/portfolio_risk_calibration/`. Docker runs used
`--network none --memory 2g`.

1. `witness.py` calls the installed `calculate_metrics_from_data` on authored constant-growth NAV
   paths (`witness.out`):
   - 126 NAV points, agent +20%, benchmark +10%: evaluator gives **0.21**, the contract formula
     gives **0.23**. Exact values: 21/100 and 23/100. The geometric version is 23/121 ≈ 0.190. Both
     score 20/20, because both are above the 12% cap.
   - 243 points, +20% / +10%: 0.10389 vs 0.10424. The excess score is 17.317 vs 17.373.
   - 252 points (exponent 1): identical (0.10 / 0.10).
2. `run_full.sh` runs the full original manifest pipeline with the image's shipped example
   `portfolio_optimizer.py` as the submission, then `posthoc.py` recomputes the result on the same
   `backtest_results.json` and the evaluator's own benchmark NAV (`run_full.out`). There are 242
   aligned points, so k = 252/242 = 1.0413. Agent period return is 15.87% and benchmark is 24.80%.
   The evaluator's excess is −9.284% and the contract's is −9.373%. Excess score is −9.284 vs
   −9.373. IR and Sortino scores are 0 vs 0. The final total is 0/100 either way, because other
   gates decide it.
3. `sensitivity.py` sweeps agent period returns from −30% to +100% with the real benchmark
   (24.80%) and the real horizon (`sensitivity.out`). The largest excess-component score
   difference is **0.17 points out of 100** (at an agent return of about 36%, just below the 12%
   cap). The gap in excess reaches 0.713 pp at an agent return of −30% (where both scores are already at the −10 floor); see `sensitivity.out`. IR and Sortino share
   the numerator, which rescales by about 1% (example: IR −1.806 vs −1.823). At most this moves
   each of those scores by about 0.1 points.

## Refutation attempts

- *Ambiguous convention?* No. The prompt states "strategy annualized return − benchmark annualized
  return" in so many words. The evaluator's formula contradicts it whenever the exponent is not 1
  and the benchmark return is not 0. In Lean, for k = 2 the gap is exactly 2·b·(a−b).
- *Arithmetic.* 1.1² − 1 = 0.21, 1.2² − 1.1² = 0.44 − 0.21 = 0.23, and (1.2/1.1)² − 1 = 23/121.
  All checked with exact fractions and in Lean.
- *Is the witness reachable?* Not on the real horizon. The hidden test period is fixed at about
  242 NAV days, so the real exponent is 1.041, not 2. The 126-observation witness exaggerates the
  gap roughly 50-fold compared with what any real submission sees. "21% instead of 23%" is
  correct arithmetic about a horizon the task never uses.
- *Rankings.* The benchmark is the same for every submission. For a fixed benchmark, both formulas
  increase strictly with the agent's period return (Lean proves this for k = 2; numerically it
  holds for k = 1.041). So both formulas rank strategies' excess returns the same way. Total-score
  order can flip only between submissions within about 0.4 points of each other (0.17 excess +
  about 0.1 IR + about 0.1 Sortino).
- *"Seven unaffected metrics are preserved."* Accurate for the seven returned fields (Sharpe,
  drawdown, turnover, total return, annual return, benchmark annual return, trading days).
  Information ratio and Sortino *do* change, because they use the excess as numerator. The
  acceptance record says this too.
- *Unclaimed side inconsistency.* The exported `annual_return` uses 241 return intervals and
  `benchmark_annual_return` uses 242 NAV points. The evaluator's own printed annual returns
  therefore do not subtract exactly to any of the excess figures (16.65 − 25.95 = −9.30, against
  −9.28 from the evaluator and −9.37 from the aligned contract formula). The earlier repair keeps
  the aligned 242-point exponent and says so.

## Formal check

`formal/lean/ebv/Ebv/FinanceExcessFx.lean` (output in `FinanceExcessFx.out`) proves `pf_orig`
(21/100), `pf_contract` (23/100), `pf_geometric` (23/121), `pf_gap_k2` (gap = 2b(a−b), by `ring`),
and `pf_orig_strictMono` and `pf_contract_strictMono`. Every one depends only on
`[propext, Classical.choice, Quot.sound]`, with no `sorry`. Scope: rational k = 2 only. The real
k = 252/242 cases are covered numerically (float64), not formally.

## Verdict

**CONFIRMED-NARROWER.** The formula contradicts the explicitly stated contract definition, and the
witness arithmetic is right. But the convention objection fails, because the contract is not
ambiguous. And the impact on the real 242-day test horizon is tiny. At most about 0.17 points of
the excess component and about 0.4 points of total score move. Excess ranking among solutions is
unchanged. For the shipped example submission the change is −9.28% to −9.37%, with no change in
the final score.

## Disposition assessment

I disagree that this finding *alone* justifies withholding the original. A spec deviation worth
less than half a point, which never changes the excess ordering, calls for "retain with a note"
or a two-line repair. If the original is withheld, that should rest on other portfolio findings
(I did not review those), not on this one.

## Recommended publishable wording

"The evaluator computes annualized excess return as ((1 + agent period return − benchmark period
return)^(252/N) − 1), while the task defines it as strategy annualized return minus benchmark
annualized return. On the task's fixed 242-day test horizon the two differ by at most 0.713
percentage points, which moves the score by at most about 0.4 of 100 points and never changes
the ordering of excess returns."

## Repair note

The earlier corrected formula, `(1+a)**(252/N) - (1+b)**(252/N)` with the same aligned N, is
correct and minimal for this finding. It changes IR and Sortino downstream, as intended. It does
not fix the 241 vs 242 horizon mismatch in exported `annual_return`, which is cosmetic for
scoring.

## Limits

- The full run used the manifest command directly, not the `score.py` wrapper.
- The shipped example optimizer scores 0 because of other gates. I did not construct a strategy
  that scores near the excess thresholds through the full pipeline. The sweep uses the
  evaluator's scoring functions on the real benchmark and horizon instead.
- IR and Sortino effects are bounded by numerator rescaling, not rerun end-to-end.
