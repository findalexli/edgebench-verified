# portfolio_risk_calibration: formal note (extension)

> **Note (2026-10-13): the task is now fixed, and this file covers the fix.** The fixed version
> (`repairs/portfolio_risk_calibration-v2/`) computes `excess_annual` as the contract formula with one
> exponent, `eC k k b a = (1+a)^k - (1+b)^k` with k = 252/len(common_idx). So `eC_strictMono` (the
> fixed excess rises strictly with the strategy return), `same_order` (the fix never reorders
> strategies against the original for a fixed benchmark) and `same_sign` (the fix keeps the sign, so
> the 0% deduction line is unchanged) are statements about the fixed formula. Summary row: covers
> "note" (score compatibility), proved: the theorems show that old and new scores are compatible, not
> that the fix is correct, since nothing formal links the model to the patched code. Still not proved: the size of the change (at most 0.39 up, 0.10 down, from a
> 50-digit decimal sweep, `repairs/portfolio_risk_calibration-v2/paired/bound.out`), its direction
> (fixed above original for a > b), and the link from the model to the fixed code beyond the
> source-line note. No new Lean was written.

## Claim
We published "≤ ~0.4 points; ordering preserved" for the real test period (k = 252/242). The
existing `FinanceExcessFx.lean` proves identities and monotonicity only for k = 2 (126 NAV points).
**It does not cover k = 252/242.** This file extends the ordering and sign parts, and only those, to
every real k > 0. The case page cites both files.

## Model and link to the code
Lean 4: `evidence/formal/lean/ebv/Ebv/PortfolioOrderRealExp.lean` (output
`PortfolioOrderRealExp.out`). It uses Real.rpow.
- Grader: `eG = (1+a-b)^k - 1`.
- Contract: `eC = (1+a)^k₁ - (1+b)^k₂`. Different exponents are allowed for the 241-interval and
  242-point inconsistency.
- The formula is `eval_script.py:925-928` as quoted in `evidence/reviews/portfolio_risk_calibration.md`.
  The file in the local grader image (`/home/workspace/scoring/eval_script.py`) has sha256
  829eeee1…a4f9b, the value in the review, and lines 921-928 match the model: `eG` is
  `excess_annual`, with k = 252/len(common_idx).

## Result
**Proved for order and sign (score compatibility); the size of the change is not proved.**
- `same_order`: for a fixed benchmark return b, the grader and contract formulas rank any two
  strategies identically, for any k, k₁ > 0, when 1+a > 0 and 1+a-b > 0.
- `same_sign`: both formulas are positive exactly when a > b, with the same k.
- `k_real_pos` checks the instances 252/242 and 252/241 (the latter is the exported `annual_return`'s exponent, which no score uses). The fixed grader's exponents, 252/242 and 252/243, are covered because the theorems hold for every k > 0.
- **Not proved:** the magnitude claims, namely a gap of at most ~0.56–0.71 pp, at most 0.18
  excess-score points, and at most 0.39 total points (a joint bound with the grader's 4-decimal rounding). They need certified enclosures of
  x^(126/121), for which there is no light tactic. They remain sweeps (float64 `sensitivity.out`; 50-digit decimal `repairs/portfolio_risk_calibration-v2/paired/bound.out`).

## Counter-check
`counter_order_across_benchmarks` (k = 2) shows that ordering can flip when the benchmark return
differs: 21/100 < 0.221025 for the grader, but 23/100 > 0.221025 for the contract. So the result
depends on the fixed test period.

## Limits
- The magnitude is not proved.
- The information ratio and Sortino ratio are not modelled.
- The score thresholds are not modelled. Ordering of excess values implies only a weak ordering of
  the capped excess score.
- The domain hypotheses exclude losses greater than 100% and 1+a-b ≤ 0. In that region Python's
  `**` would return a complex number.
