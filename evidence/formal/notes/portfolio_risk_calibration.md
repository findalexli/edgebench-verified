# portfolio_risk_calibration: formal note (extension)

## Claim
We published "≤ ~0.4 points; ordering preserved" for the real test period (k = 252/242). The
existing `FinanceExcessFx.lean` proves identities and monotonicity only for k = 2 (126 NAV points).
**It does not cover k = 252/242.** The case page says this ("The Lean proofs cover only the rational
exponent k = 2"). This file extends the ordering part, and only that part, to every real k > 0.

## Model and link to the code
Lean 4: `evidence/formal/lean/ebv/Ebv/PortfolioOrderRealExp.lean` (output
`PortfolioOrderRealExp.out`). It uses Real.rpow.
- Grader: `eG = (1+a-b)^k - 1`.
- Contract: `eC = (1+a)^k₁ - (1+b)^k₂`. Different exponents are allowed for the 241-interval and
  242-point inconsistency.
- The formula is `eval_script.py:925-928` as quoted in `evidence/reviews/portfolio_risk_calibration.md`.
  That file was not re-read or re-hashed here, because no local copy of the portfolio grader was
  found.

## Result
**Partly proved.**
- `same_order`: for a fixed benchmark return b, the grader and contract formulas rank any two
  strategies identically, for any k, k₁ > 0, when 1+a > 0 and 1+a-b > 0.
- `same_sign`: both formulas are positive exactly when a > b, with the same k.
- `k_real_pos` covers 252/242 and 252/241.
- **Not proved:** the magnitude claims, namely a gap of at most ~0.56–0.71 pp, at most 0.17
  excess-score points, and at most ~0.4 total points. They need certified enclosures of
  x^(126/121), for which there is no light tactic. They remain float64 sweeps (`sensitivity.out`).

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
