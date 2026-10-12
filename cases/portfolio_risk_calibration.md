# Portfolio Risk Calibration (`portfolio_risk_calibration`)

**Decision:** Retain with note. The evaluator computes annual excess return as an annualized difference, not as the difference of the two annualized returns, but on the real test horizon the effect is at most about 0.4 points and the ordering of excess returns is unchanged.

## What the task asks for

The solver builds a portfolio strategy that is backtested against a benchmark. The task instruction defines the convention explicitly:

- "Excess return = strategy annualized return - benchmark annualized return."
- "Information ratio = annualized excess return / tracking error."
- "Sortino ratio = annualized excess return / downside deviation."

An excess return of 12% or more earns full marks for that component, and a negative excess is deducted. Category: Professional Knowledge Work.

## What goes wrong

**The evaluator uses a different formula from the one stated.** Finance has several accepted definitions of excess return, but the prompt chooses one: the difference of the two annualized returns. The evaluator instead subtracts the benchmark's period return from the agent's period return, then annualizes that difference with the exponent 252/N. The two agree only when the exponent is 1.

**Small example.** With 126 NAV points, an agent return of +20% and a benchmark return of +10%:

- The evaluator gives **0.21**. The contract formula gives **0.23** (exactly 21/100 and 23/100).
- Both values are above the 12% cap, so both score 20/20.

**The real horizon is much closer to 252 days.** The hidden test period is fixed at about 242 NAV days, so the exponent is 252/242 = 1.0413, not 2. The 126-point example exaggerates the gap roughly 50-fold compared with what a real submission sees.

**The shipped example under the original evaluator:**

| Quantity | Value |
| --- | --- |
| Agent period return | 15.87% |
| Benchmark period return | 24.80% |
| Excess, evaluator | −9.284% |
| Excess, contract formula | −9.373% |
| Excess score, evaluator vs contract | −9.284 vs −9.373 |
| Final total | 0/100 either way (other gates decide it) |

Information ratio and Sortino share the excess-return numerator, so they change too.

**Separate small inconsistency (cosmetic for scoring).** The exported `annual_return` uses 241 return intervals, while `benchmark_annual_return` uses 242 NAV points.

The note that ships with the task: scores from the original evaluator compute annualized excess return with the evaluator's formula, which differs from the task's stated definition. On the task's fixed 242-day test horizon the two formulas differ by at most about 0.7 percentage points for agent returns from −30% to +100% (under 0.6 points from 0% upward). The total score moves by at most about 0.4 of 100 points, and the ordering of excess returns never changes. A two-line formula fix exists if exact agreement with the contract is needed.

## Impact

- The largest difference in the excess-component score across agent returns from −30% to +100% is **0.17 points out of 100**. It occurs at an agent return of about 36%, just below the cap.
- The gap in the excess value itself is at most about 0.56 percentage points for agent returns from 0% to +100%, and up to about 0.71 points at −30%, where both excess scores are already at the −10 floor.
- Information ratio and Sortino each move by at most about 0.1 points.
- The total score can move by about 0.4 points at most, for all solvers.
- For a fixed benchmark, both formulas rank strategies' excess returns in the same order.

## Fix (v2)

No change; the note above ships with the task.

## How we know

- **Original evaluator in the pinned image.** The full original manifest pipeline ran in the judge image (`sha256:42997fb57705…`, `--network none --memory 2g`) with the image's shipped example optimizer as the submission. The contract formula was then recomputed on the same backtest output and the evaluator's own benchmark NAV.
- **Direct checks.** The installed metric function was called on constant-growth NAV paths of 126, 243 and 252 points. Agent period returns from −30% to +100% were swept against the real benchmark (24.80%) over the real horizon, using the evaluator's scoring functions.
- **Formal check (Lean 4).** `FinanceExcessFx.lean` proves the k = 2 identities and that both formulas increase strictly with the agent's return. All proofs depend only on the standard axioms and use no `sorry`. Exact arithmetic was also checked with fractions.

## Limits

- No model or solver runs. Effects are shown on authored controls and counterexamples only, and no leaderboard impact is estimated.
- The full run called the manifest command directly, not the `score.py` wrapper.
- The shipped example scores 0 because of other gates. No strategy that scores near the excess thresholds was run through the full pipeline; the sweep uses the evaluator's scoring functions instead.
- The information ratio and Sortino effects are bounded by numerator rescaling, not rerun end to end.
- The Lean proofs cover only rational k = 2. The real k = 252/242 cases were checked numerically in float64.
- Other possible issues in this task were not reviewed here.

## Reproduce

- Example on authored NAV paths: `evidence/scripts/portfolio_risk_calibration/witness.py` (output `witness.out`).
- Full original pipeline plus recomputation: `evidence/scripts/portfolio_risk_calibration/run_full.sh` and `posthoc.py` (output `run_full.out`).
- Sweep over the real horizon: `evidence/scripts/portfolio_risk_calibration/sensitivity.py` (output `sensitivity.out`).
- Lean identities: `evidence/formal/lean/ebv/Ebv/FinanceExcessFx.lean` (output `FinanceExcessFx.out`).
- Supporting records: `evidence/reviews/portfolio_risk_calibration.md`.
