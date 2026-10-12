# Portfolio Risk Calibration (`portfolio_risk_calibration`)

**Outcome:** Kept, with a note. The grader computes yearly excess return by converting the difference of the two returns to a yearly figure, instead of taking the difference of the two yearly returns as the instructions state, but on the real test period the effect is at most about 0.4 points and the order of excess returns is unchanged.

## What the task asks

The solver builds a portfolio strategy. The grader backtests it, that is, runs it on past market data, and compares it with a benchmark index. The task instructions define the convention explicitly:

- "Excess return = strategy annualized return - benchmark annualized return."
- "Information ratio = annualized excess return / tracking error."
- "Sortino ratio = annualized excess return / downside deviation."

An excess return of 12% or more earns full marks for that part of the score, and a negative excess is deducted. Category: Professional Knowledge Work.

## What goes wrong

**The grader uses a different formula from the one stated.** Finance has several accepted definitions of excess return, but the instructions choose one: the difference of the two annualized (yearly) returns. The grader instead subtracts the benchmark's return over the period from the strategy's return over the period. It then converts that difference to a yearly figure with the exponent 252/N, where N is the number of daily NAV (net asset value) points and 252 is the number of trading days in a year. The two agree only when the exponent is 1.

**Small example.** With 126 NAV points, a strategy return of +20% and a benchmark return of +10%:

- The grader gives **0.21**. The formula in the instructions gives **0.23** (exactly 21/100 and 23/100).
- Both values are above the 12% cap, so both score 20/20.

**The real test period is much closer to 252 days.** The hidden test period is fixed at about 242 NAV days, so the exponent is 252/242 = 1.0413, not 2. The 126-point example makes the gap roughly 50 times larger than what a real submission sees.

**The supplied example under the original grader:**

| Quantity | Value |
| --- | --- |
| Strategy return over the period | 15.87% |
| Benchmark return over the period | 24.80% |
| Excess, grader | −9.284% |
| Excess, formula in the instructions | −9.373% |
| Excess score, grader vs instructions | −9.284 vs −9.373 |
| Final total | 0/100 either way (other pass/fail checks decide it) |

The information ratio and the Sortino ratio both divide the excess return by a risk measure, so they change too.

**A separate small inconsistency (no effect on scoring).** The exported `annual_return` uses 241 return intervals, while `benchmark_annual_return` uses 242 NAV points.

The note that ships with the task: scores from the original grader compute annualized excess return with the grader's formula, which differs from the task's stated definition. On the task's fixed 242-day test period the two formulas differ by at most about 0.7 percentage points for strategy returns from −30% to +100% (under 0.6 points from 0% upward). The total score moves by at most about 0.4 of 100 points, and the order of excess returns never changes. A two-line formula fix exists if exact agreement with the instructions is needed.

## How much it matters

- The largest difference in the excess-return part of the score, across strategy returns from −30% to +100%, is **0.17 points out of 100**. It occurs at a strategy return of about 36%, just below the cap.
- The gap in the excess value itself is at most about 0.56 percentage points for strategy returns from 0% to +100%. It is up to about 0.71 points at −30%, where both excess scores are already at the floor of −10.
- The information ratio and Sortino ratio each move by at most about 0.1 points.
- The total score can move by about 0.4 points at most, for all solvers.
- For a fixed benchmark, both formulas rank strategies' excess returns in the same order.

There is no code change. The note above ships with the task.

## How we checked it

- **Original grader in the original image, pinned by digest.** The full original scoring pipeline (from the task's manifest) ran in the grader image (`--network none --memory 2g`), with the image's supplied example optimizer as the submission. The formula in the instructions was then recomputed on the same backtest output and the grader's own benchmark NAV.
- **Direct checks.** The installed metric function was called on NAV paths with constant growth, of 126, 243 and 252 points. Strategy returns over the period from −30% to +100% were swept against the real benchmark (24.80%) over the real test period, using the grader's scoring functions.
- **Formal check (Lean 4, a proof checker).** `FinanceExcessFx.lean` proves the identities for exponent k = 2, and that both formulas increase strictly with the strategy's return. All proofs depend only on the standard axioms and use no `sorry` (an unproved placeholder). Exact arithmetic was also checked with fractions.

## Limits

- No AI model or solver was run. Effects are shown only on test submissions and counterexamples we wrote, and no effect on the leaderboard is estimated.
- The full run called the manifest command directly, not the `score.py` wrapper.
- The supplied example scores 0 because of other pass/fail checks. No strategy that scores near the excess-return thresholds was run through the full pipeline; the sweep uses the grader's scoring functions instead.
- The effects on the information ratio and Sortino ratio are bounded by how the shared excess-return term scales, not rerun end to end.
- The Lean proofs cover only the rational exponent k = 2. The real k = 252/242 cases were checked numerically in float64.
- Other possible issues in this task were not reviewed here.

## Reproduce

- Original grader image: `sha256:42997fb57705…`.
- Example on NAV paths we wrote: `evidence/scripts/portfolio_risk_calibration/witness.py` (output `witness.out`).
- Full original pipeline plus recomputation: `evidence/scripts/portfolio_risk_calibration/run_full.sh` and `posthoc.py` (output `run_full.out`).
- Sweep over the real test period: `evidence/scripts/portfolio_risk_calibration/sensitivity.py` (output `sensitivity.out`).
- Lean identities: `evidence/formal/lean/ebv/Ebv/FinanceExcessFx.lean` (output `FinanceExcessFx.out`).
- Supporting records: `evidence/reviews/portfolio_risk_calibration.md`.
