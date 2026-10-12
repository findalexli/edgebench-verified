# Portfolio Risk Calibration (`portfolio_risk_calibration`)

Status: reviewed by the coordinator, 2026-10-12

- **Domain:** Professional Knowledge Work
- **Decision:** Retain with note. The evaluator computes annual excess return as an annualized difference, not as the difference of the two annualized returns. On the real test horizon the effect is at most about 0.4 points, and the ordering of excess returns is unchanged.

## What the task promises

The task instruction defines the convention explicitly:

- "Excess return = strategy annualized return - benchmark annualized return."
- "Information ratio = annualized excess return / tracking error."
- "Sortino ratio = annualized excess return / downside deviation."

An excess return of 12% or more earns full marks for that component, and a negative excess is deducted.

## What we checked and how

- We read the evaluator's excess-return computation in `scoring/eval_script.py`.
- We called the installed metric function on authored constant-growth NAV paths of 126, 243 and 252 points.
- We ran the full original manifest pipeline in the pinned judge image (`--network none --memory 2g`), using the image's shipped example optimizer as the submission. We then recomputed the contract formula post hoc on the same backtest output and the evaluator's own benchmark NAV.
- We swept agent period returns from −30% to +100% against the real benchmark (24.80%) over the real horizon.
- We checked exact arithmetic with fractions and in Lean 4 (`FinanceExcessFx.lean`). Lean proves the k = 2 identities and that both formulas increase strictly with the agent's return. All proofs depend only on the standard axioms and use no `sorry`. The coordinator compiled the Lean file.
- Original identity:
  - judge image `seededge/edgebench.judge.portfolio_risk_calibration@sha256:42997fb5770532b08cf9b97927d28f34466868348cc75ae13824b81c90e9458d`
  - `scoring/eval_script.py` sha256 `829eeee186f02fba42e4291fea94523a8a7c89cf62c7e534c77115cb8eea4f9b`
  - `input/task_instruction.md` sha256 `a903d2361d017c92fe8b2e6975fafbea485d9b031d5e6231a7989bf3216cd191`
  - task JSON sha256 `0343ac03f42042ff9053cb1809d106dac9311e5fe7d9bab353eab4ad1b078cb1`

## What we found

**Confirmed, narrower (immaterial).**

**The convention is not ambiguous.** Finance has several accepted definitions of excess return, but the prompt chooses one: the difference of the two annualized returns.

**The evaluator uses a different formula.** It subtracts the benchmark's period return from the agent's period return, then annualizes that difference with the exponent 252/N. The result matches the contract only when the exponent is 1.

**Witness example.** With 126 NAV points, an agent return of +20% and a benchmark return of +10%:

- The evaluator gives **0.21**. The contract formula gives **0.23** (exactly 21/100 and 23/100).
- Both values are above the 12% cap, so both score 20/20.

**The real horizon is much closer to 252 days.** The hidden test period is fixed at about 242 NAV days, so the exponent is 252/242 = 1.0413, not 2. The 126-point witness exaggerates the gap roughly 50-fold compared with what a real submission sees.

**Effect on the shipped example under the original evaluator.**

| Quantity | Value |
| --- | --- |
| Agent period return | 15.87% |
| Benchmark period return | 24.80% |
| Excess, evaluator | −9.284% |
| Excess, contract formula | −9.373% |
| Excess score, evaluator vs contract | −9.284 vs −9.373 |
| Final total | 0/100 either way (other gates decide it) |

**Maximum score effect.**

- The largest difference in the excess-component score across the sweep is **0.17 points out of 100**. It occurs at an agent return of about 36%, just below the cap.
- The gap in the excess value itself is at most about 0.56 percentage points.
- Information ratio and Sortino share this numerator, so each moves by at most about 0.1 points.
- The total score can move by about 0.4 points at most.
- For a fixed benchmark, both formulas rank strategies' excess returns in the same order.

**Why the task is retained.** An earlier audit withheld the original task because of this formula. Re-checking showed that the deviation is real but worth less than half a point on the real horizon and never changes the excess ordering. This finding alone does not justify withholding the task.

**Earlier claim of unaffected metrics.** The earlier claim said "seven unaffected metrics are preserved". That is accurate for the seven returned fields, but information ratio and Sortino do change.

**Separate small inconsistency (cosmetic for scoring).** The exported `annual_return` uses 241 return intervals, while `benchmark_annual_return` uses 242 NAV points.

## Note for users

No repair. Scores from the original evaluator compute annualized excess return with the evaluator's formula, which differs from the task's stated definition. On the task's fixed 242-day test horizon the two formulas differ by under 0.6 percentage points. The total score moves by at most about 0.4 of 100 points, and the ordering of excess returns never changes. A two-line formula fix exists if exact agreement with the contract is needed.

## Limits and what was not run

- No model or solver was re-run. The effects shown are on authored controls and counterexamples only, and no leaderboard impact is estimated.
- The full run called the manifest command directly, not the `score.py` wrapper.
- The shipped example scores 0 because of other gates. We built no strategy that scores near the excess thresholds through the full pipeline. The sweep uses the evaluator's scoring functions on the real benchmark and horizon instead.
- The information ratio and Sortino effects are bounded by numerator rescaling, not rerun end to end.
- The Lean proofs cover only rational k = 2. The real k = 252/242 cases were checked numerically in float64.
- Other portfolio findings, if any, were not reviewed here.

## Reproduce

- Witness on authored NAV paths: `evidence/scripts/portfolio_risk_calibration/witness.py` (output `witness.out`)
- Full original pipeline plus post-hoc recomputation: `evidence/scripts/portfolio_risk_calibration/run_full.sh` and `posthoc.py` (output `run_full.out`)
- Sweep over the real horizon: `evidence/scripts/portfolio_risk_calibration/sensitivity.py` (output `sensitivity.out`)
- Lean identities: `evidence/formal/lean/ebv/Ebv/FinanceExcessFx.lean` (output `FinanceExcessFx.out`)

Supporting records: `evidence/reviews/portfolio_risk_calibration.md`.

