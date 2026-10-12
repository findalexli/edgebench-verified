import Mathlib.Analysis.SpecialFunctions.Pow.Real

/-! # portfolio_risk_calibration: ordering claim for the real exponent k = 252/N

`FinanceExcessFx.lean` proves the identities and strict monotonicity only for k = 2 (126 NAV
points). The published claim concerns the real test period, k = 252/242 (and 252/241 for the
exported strategy `annual_return`). This file extends the ORDERING part to every real k > 0:

* the grader's excess  E_g(a) = (1 + a - b)^k - 1          (eval_script.py:925-928, per the review)
* the stated contract  E_c(a) = (1 + a)^k - (1 + b)^k     ("strategy annualized − benchmark annualized")

For a fixed benchmark period return b (the hidden test period is fixed), both are strictly
increasing in the strategy period return a on their domains, so they rank any two strategies
identically, and both are positive exactly when a > b. The contract version with a different
strategy exponent k₁ (241 intervals) and benchmark exponent k₂ (242 points) is also covered.

NOT covered: the magnitude claims (gap ≤ ~0.56–0.71 pp, ≤ 0.17 excess-score points, ≤ ~0.4
total points). Those need certified enclosures of x^(126/121) and remain float64 sweeps
(`evidence/scripts/portfolio_risk_calibration/sensitivity.out`).

Source: `eval_script.py` in judge image
`seededge/edgebench.judge.portfolio_risk_calibration@sha256:42997fb5770532b08cf9b97927d28f34466868348cc75ae13824b81c90e9458d`,
lines 925-928 as quoted in `evidence/reviews/portfolio_risk_calibration.md` (the file itself was
not re-hashed here). Domain: Python `x ** k` with x < 0 and fractional k gives a complex number,
so the grader formula is only meaningful for 1 + a - b > 0 (a strategy loss below b − 100%). -/

namespace Ebv.PortfolioReal

open Real

noncomputable def eG (k b a : ℝ) : ℝ := (1 + a - b) ^ k - 1
noncomputable def eC (k₁ k₂ b a : ℝ) : ℝ := (1 + a) ^ k₁ - (1 + b) ^ k₂

theorem eG_strictMono (k b a₁ a₂ : ℝ) (hk : 0 < k) (h0 : 0 < 1 + a₁ - b) (h : a₁ < a₂) :
    eG k b a₁ < eG k b a₂ := by
  unfold eG
  have := Real.rpow_lt_rpow (le_of_lt h0) (by linarith : 1 + a₁ - b < 1 + a₂ - b) hk
  linarith

theorem eC_strictMono (k₁ k₂ b a₁ a₂ : ℝ) (hk : 0 < k₁) (h0 : 0 < 1 + a₁) (h : a₁ < a₂) :
    eC k₁ k₂ b a₁ < eC k₁ k₂ b a₂ := by
  unfold eC
  have := Real.rpow_lt_rpow (le_of_lt h0) (by linarith : 1 + a₁ < 1 + a₂) hk
  linarith

/-- Same ranking of any two strategies against the fixed benchmark. -/
theorem same_order (k k₁ k₂ b a₁ a₂ : ℝ) (hk : 0 < k) (hk₁ : 0 < k₁)
    (h1 : 0 < 1 + a₁ - b) (h2 : 0 < 1 + a₂ - b) (ha1 : 0 < 1 + a₁) (ha2 : 0 < 1 + a₂) :
    (eG k b a₁ < eG k b a₂ ↔ eC k₁ k₂ b a₁ < eC k₁ k₂ b a₂) := by
  constructor
  · intro h
    rcases lt_trichotomy a₁ a₂ with hlt | heq | hgt
    · exact eC_strictMono k₁ k₂ b a₁ a₂ hk₁ ha1 hlt
    · subst heq; exact absurd h (lt_irrefl _)
    · exact absurd h (not_lt.mpr (le_of_lt (eG_strictMono k b a₂ a₁ hk h2 hgt)))
  · intro h
    rcases lt_trichotomy a₁ a₂ with hlt | heq | hgt
    · exact eG_strictMono k b a₁ a₂ hk h1 hlt
    · subst heq; exact absurd h (lt_irrefl _)
    · exact absurd h (not_lt.mpr (le_of_lt (eC_strictMono k₁ k₂ b a₂ a₁ hk₁ ha2 hgt)))

/-- Same sign: both formulas report a positive excess exactly when a > b (same exponent k). -/
theorem same_sign (k b a : ℝ) (hk : 0 < k) (h0 : 0 < 1 + a - b) (ha : 0 < 1 + a) (hb : -1 < b) :
    (0 < eG k b a ↔ b < a) ∧ (0 < eC k k b a ↔ b < a) := by
  unfold eG eC
  constructor
  · constructor
    · intro h
      by_contra hn
      have hle : 1 + a - b ≤ 1 := by linarith [not_lt.mp hn]
      have := Real.rpow_le_rpow (le_of_lt h0) hle (le_of_lt hk)
      rw [Real.one_rpow] at this; linarith
    · intro h
      have := Real.rpow_lt_rpow (by norm_num : (0 : ℝ) ≤ 1) (by linarith : (1 : ℝ) < 1 + a - b) hk
      rw [Real.one_rpow] at this; linarith
  · rw [sub_pos, Real.rpow_lt_rpow_iff (by linarith) (le_of_lt ha) hk]
    constructor <;> intro h <;> linarith

/-- The real test period's exponents are positive (hypothesis instances). -/
theorem k_real_pos : (0 : ℝ) < 252 / 242 ∧ (0 : ℝ) < 252 / 241 := by
  constructor <;> norm_num

/-! ## Counter-check (must come out the other way)

Ordering is preserved only for a FIXED benchmark. Across different benchmark returns it can
flip: with k = 2, (a, b) = (1/5, 1/10) has grader 21/100 < 221025/1000000 = grader for
(a, b) = (21/200, 0), while the contract values are 23/100 > 221025/1000000. -/

theorem counter_order_across_benchmarks :
    eG 2 (1 / 10) (1 / 5) < eG 2 0 (21 / 200) ∧
    eC 2 2 0 (21 / 200) < eC 2 2 (1 / 10) (1 / 5) := by
  unfold eG eC
  simp only [Real.rpow_two]
  constructor <;> norm_num

end Ebv.PortfolioReal

#print axioms Ebv.PortfolioReal.eG_strictMono
#print axioms Ebv.PortfolioReal.eC_strictMono
#print axioms Ebv.PortfolioReal.same_order
#print axioms Ebv.PortfolioReal.same_sign
#print axioms Ebv.PortfolioReal.k_real_pos
#print axioms Ebv.PortfolioReal.counter_order_across_benchmarks
