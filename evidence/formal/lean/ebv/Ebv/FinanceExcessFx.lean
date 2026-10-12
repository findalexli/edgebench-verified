import Mathlib

/-! Exact-arithmetic checks for two finance-task reviews.

cta_risk_budget_optimization: evaluator overseas share = o/(o+d) with o in USD units,
d in CNY units (no FX); contract share = (x*o)/(x*o+d) with x = USDCNY.

portfolio_risk_calibration: evaluator excess = (1+a-b)^k - 1, contract excess =
(1+a)^k - (1+b)^k ("strategy annualized return - benchmark annualized return").
Only the k = 2 (126-observation) witness exponent is modelled here. -/

namespace Ebv.Finance

/-- CTA witness: 1 USD-unit overseas vs 2 CNY-unit domestic, USDCNY = 7. -/
theorem cta_native_share : (1 : ℚ) / (1 + 2) = 1 / 3 := by norm_num
theorem cta_cny_share : (7 * 1 : ℚ) / (7 * 1 + 2) = 7 / 9 := by norm_num
theorem cta_native_passes : (1 : ℚ) / 3 ≤ 2 / 5 := by norm_num
theorem cta_cny_fails : (2 : ℚ) / 5 < 7 / 9 := by norm_num

/-- With USDCNY = 7, any book whose native-unit share passes the 40% test has a true CNY
share of at most 14/17 (about 82.4%). -/
theorem cta_max_hidden_share (o d : ℚ) (ho : 0 < o) (hd : 0 < d)
    (h : o / (o + d) ≤ 2 / 5) : (7 * o) / (7 * o + d) ≤ 14 / 17 := by
  rw [div_le_div_iff₀ (by positivity) (by positivity)] at h
  rw [div_le_div_iff₀ (by positivity) (by norm_num)]
  nlinarith

/-- Portfolio witness, k = 2: original 21/100, contract 23/100, geometric 23/121. -/
theorem pf_orig : (1 + (1 : ℚ) / 5 - 1 / 10) ^ 2 - 1 = 21 / 100 := by norm_num
theorem pf_contract : (1 + (1 : ℚ) / 5) ^ 2 - (1 + 1 / 10) ^ 2 = 23 / 100 := by norm_num
theorem pf_geometric : ((1 + (1 : ℚ) / 5) / (1 + 1 / 10)) ^ 2 - 1 = 23 / 121 := by norm_num

/-- k = 2 gap: contract - original = 2*b*(a-b); zero iff a = b or b = 0. -/
theorem pf_gap_k2 (a b : ℚ) :
    ((1 + a) ^ 2 - (1 + b) ^ 2) - ((1 + a - b) ^ 2 - 1) = 2 * b * (a - b) := by ring

/-- For a fixed benchmark b, both k = 2 formulas are strictly increasing in a on the
region 1 + a - b > 0, so they rank strategies' excess identically there. -/
theorem pf_orig_strictMono (b a₁ a₂ : ℚ) (h0 : 0 < 1 + a₁ - b) (h : a₁ < a₂) :
    (1 + a₁ - b) ^ 2 - 1 < (1 + a₂ - b) ^ 2 - 1 := by nlinarith
theorem pf_contract_strictMono (b a₁ a₂ : ℚ) (h0 : 0 < 1 + a₁) (h : a₁ < a₂) :
    (1 + a₁) ^ 2 - (1 + b) ^ 2 < (1 + a₂) ^ 2 - (1 + b) ^ 2 := by nlinarith

end Ebv.Finance

#print axioms Ebv.Finance.cta_max_hidden_share
#print axioms Ebv.Finance.cta_cny_share
#print axioms Ebv.Finance.cta_native_share
#print axioms Ebv.Finance.pf_orig
#print axioms Ebv.Finance.pf_contract
#print axioms Ebv.Finance.pf_geometric
#print axioms Ebv.Finance.pf_gap_k2
#print axioms Ebv.Finance.pf_orig_strictMono
#print axioms Ebv.Finance.pf_contract_strictMono
