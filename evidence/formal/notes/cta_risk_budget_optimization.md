# cta_risk_budget_optimization (fixed 40% overseas-share check)

## Claim

1. The fixed per-day check, which converts USD notionals at USDCNY before testing
   on/tn > 0.40, is exactly the contract's test on RMB-equivalent values.
2. All-CNY books are numerically unchanged by the fix.
3. Assume every overseas ticker is USD-priced and every USD ticker is overseas, and
   USDCNY ≥ 1. Then an original violation is also a fixed violation, so the fix can only lower
   credit.
4. The published witness (2 CNY lots plus 1 USD lot, price and multiplier 1, USDCNY 7) has an
   unconverted share of 1/3 and an RMB share of 7/9. The fixed check rejects it and the
   original accepts it.

## Model and link to the code

`Ebv/CtaFxCheck.lean` (output `CtaFxCheck.out`), a new file next to `FinanceExcessFx.lean`.
It models the fixed `eval_script.py` (sha256 `4e0ddc4e…110a`), lines 1015–1046: the price
lookup (missing → 0), the multiplier lookup (missing → 1), `ccy_lk`, the fx factor
(rate, or 1.0 for CNY), `n = l*m*p*fx`, the `tn`/`on` sums and the violation test on line 1046.
`nOrig` is the original line `n = l * m * p`, line 1033 before `repair.patch`. One day's
holdings are a list of positions, and the day's USDCNY value `r` stands for the `asof`
lookup or its 7.0 fallback.

## Result

**Proved:** `fixed_iff_contract`, `fixed_eq_orig_of_cny`, `orig_violation_implies_fixed`
and the four witness theorems.

## Counter-check

- `witness_accepted_by_orig` and `counter_orig_not_contract`: the original rule fails the
  contract.
- `counter_fixed_not_implies_orig`: the reverse implication is false, so the fix does change
  outcomes.

## Limits

- The `asof` lookup, the 7.0 fallback, pandas grouping by date and the mapping from
  violation days to `cb_checks` (lines 1048–1050) are not modelled.
- The "% of NAV vs % of gross notional" question is out of scope.
- Claim 3 relies on overseas ⇔ USD. The case page states this; it was not re-checked against
  `contract_specs`.
- The real-data examples (0.175 → 0.595, 32 of 1,565 days) were not re-derived.
