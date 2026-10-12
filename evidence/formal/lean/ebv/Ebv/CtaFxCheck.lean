/-
EdgeBench Verified -- cta_risk_budget_optimization: the fixed 40% overseas-share check
(exact rationals). Extends FinanceExcessFx.lean (which only checks the witness arithmetic)
with a model of the per-day check itself, original and fixed.

Source modelled
  * Fixed grader /home/workspace/scoring/eval_script.py (local copy
    .internal/repairs/cta_risk_budget_optimization-v2/files/eval_script.py),
    sha256 4e0ddc4e0f28fe5e77aca0e65f48c246ef8c5c21bbc3877769e5d79deff7110a;
    original = the same file before repairs/cta_risk_budget_optimization-v2/repair.patch.
      price_lk[(date,ticker)] = close; missing -> 0                       [1015-1020, 1039]
      mult_lk[ticker] = multiplier; missing -> 1                          [1021-1023, 1039]
      ccy_lk[ticker] = specs.currency (fixed only)                        [1025-1027]
      fx_s = USDCNY series; fx = asof(date), 7.0 if missing (fixed only)   [1028-1031, 1040-1043]
      per day: l = |lots|; skip l == 0; n = l*m*p (orig) / l*m*p*fx (fixed);
               tn += n; on += n if ticker in OVERSEAS_TICKERS              [1032-1045]
      violation iff tn > 0 and on/tn > 0.40                                [1046]
  * Contract: risk_policy_doc.docx: overseas share <= 40%, every overseas position converted to
    its RMB equivalent at the live exchange rate (case page cta_risk_budget_optimization.md).

Model: one day's holdings as a list of positions; the day's USDCNY value `r` stands for the
`asof` lookup (or the 7.0 fallback). The `asof` lookup itself, pandas grouping and the
day-count mapping to cb_checks [1048-1050] are not modelled. Exact rationals replace doubles.
-/
import Mathlib.Algebra.Order.Field.Rat
import Mathlib.Tactic.NormNum
import Mathlib.Tactic.Linarith
import Mathlib.Tactic.Positivity
import Mathlib.Tactic.Ring

namespace Ebv.CtaFx

structure Pos where
  lots : ℚ        -- |lots| (the code takes abs)
  mult : ℚ        -- multiplier (1 if missing)
  price : ℚ       -- close (0 if missing)
  usd : Bool      -- specs.currency == 'USD'
  overseas : Bool -- ticker in OVERSEAS_TICKERS

/-- Per-position notional in the original code (`n = l * m * p`, line 1033 of the original file). -/
def nOrig (p : Pos) : ℚ := p.lots * p.mult * p.price
/-- Per-position notional in the fixed code [1040-1044]: fx = r for USD, else 1.0. -/
def nFixed (r : ℚ) (p : Pos) : ℚ := p.lots * p.mult * p.price * (if p.usd then r else 1)

def tot (f : Pos → ℚ) : List Pos → ℚ
  | [] => 0
  | p :: ps => f p + tot f ps
def ovs (f : Pos → ℚ) : List Pos → ℚ
  | [] => 0
  | p :: ps => (if p.overseas then f p else 0) + ovs f ps

/-- The per-day violation predicate [1046], for a given notional function. -/
def violates (f : Pos → ℚ) (ps : List Pos) : Prop := 0 < tot f ps ∧ 2 / 5 < ovs f ps / tot f ps

/-- Contract: the RMB-equivalent value of a position is its native notional, multiplied by the
USDCNY rate when it is priced in USD. -/
def cnyValue (r : ℚ) (p : Pos) : ℚ := if p.usd then r * (p.lots * p.mult * p.price)
  else p.lots * p.mult * p.price
def contractBreach (r : ℚ) (ps : List Pos) : Prop :=
  0 < tot (cnyValue r) ps ∧ 2 / 5 < ovs (cnyValue r) ps / tot (cnyValue r) ps

theorem nFixed_eq_cny (r : ℚ) (p : Pos) : nFixed r p = cnyValue r p := by
  unfold nFixed cnyValue; split_ifs <;> ring

/-- The fix is correct: the fixed check is exactly the contract's 40% test on RMB values. -/
theorem fixed_iff_contract (r : ℚ) (ps : List Pos) :
    violates (nFixed r) ps ↔ contractBreach r ps := by
  have e : nFixed r = cnyValue r := funext (nFixed_eq_cny r)
  rw [violates, contractBreach, e]

/-- Same-currency (all CNY) books are numerically unchanged by the fix. -/
theorem fixed_eq_orig_of_cny (r : ℚ) (ps : List Pos) (h : ∀ p ∈ ps, p.usd = false) :
    tot (nFixed r) ps = tot nOrig ps ∧ ovs (nFixed r) ps = ovs nOrig ps := by
  induction ps with
  | nil => simp [tot, ovs]
  | cons p ps ih =>
    have hp : p.usd = false := h p List.mem_cons_self
    obtain ⟨h1, h2⟩ := ih (fun q hq => h q (List.mem_cons_of_mem _ hq))
    simp only [tot, ovs, nFixed, nOrig, hp, h1, h2]
    simp

/-! ## "Only downward": with overseas ⇔ USD and USDCNY ≥ 1, an original violation is also a
fixed violation (the fix never removes a violation, so it can only lower the score). -/

theorem split_sums (r : ℚ) (ps : List Pos) (h : ∀ p ∈ ps, p.usd = p.overseas) :
    ovs (nFixed r) ps = r * ovs nOrig ps ∧
    tot (nFixed r) ps = r * ovs nOrig ps + (tot nOrig ps - ovs nOrig ps) := by
  induction ps with
  | nil => simp [tot, ovs]
  | cons p ps ih =>
    have hp : p.usd = p.overseas := h p List.mem_cons_self
    obtain ⟨h1, h2⟩ := ih (fun q hq => h q (List.mem_cons_of_mem _ hq))
    simp only [tot, ovs, h1, h2, nFixed, nOrig, hp]
    constructor
    · cases p.overseas <;> simp <;> ring
    · cases p.overseas <;> simp <;> ring

theorem nonneg_sums (ps : List Pos) (h : ∀ p ∈ ps, 0 ≤ nOrig p) :
    0 ≤ ovs nOrig ps ∧ ovs nOrig ps ≤ tot nOrig ps := by
  induction ps with
  | nil => simp [tot, ovs]
  | cons p ps ih =>
    have hp := h p List.mem_cons_self
    obtain ⟨h1, h2⟩ := ih (fun q hq => h q (List.mem_cons_of_mem _ hq))
    simp only [tot, ovs]
    split_ifs <;> constructor <;> linarith

theorem orig_violation_implies_fixed (r : ℚ) (hr : 1 ≤ r) (ps : List Pos)
    (hcur : ∀ p ∈ ps, p.usd = p.overseas) (hnn : ∀ p ∈ ps, 0 ≤ nOrig p)
    (hv : violates nOrig ps) : violates (nFixed r) ps := by
  obtain ⟨hs1, hs2⟩ := split_sums r ps hcur
  obtain ⟨hn1, hn2⟩ := nonneg_sums ps hnn
  obtain ⟨ht, hq⟩ := hv
  set o := ovs nOrig ps
  set t := tot nOrig ps
  have hq' : 2 / 5 * t < o := by rwa [lt_div_iff₀ ht] at hq
  have hpos : 0 < r * o + (t - o) := by nlinarith
  refine ⟨by rw [hs2]; exact hpos, ?_⟩
  rw [hs1, hs2, lt_div_iff₀ hpos]
  nlinarith

/-! ## The published witness: 2 CNY lots (domestic) + 1 USD lot (overseas), price and
multiplier 1, USDCNY 7. Unconverted share 1/3, RMB share 7/9. -/

def witness : List Pos :=
  [⟨2, 1, 1, false, false⟩, ⟨1, 1, 1, true, true⟩]

theorem witness_orig_share : ovs nOrig witness / tot nOrig witness = 1 / 3 := by
  norm_num [witness, ovs, tot, nOrig]
theorem witness_fixed_share : ovs (nFixed 7) witness / tot (nFixed 7) witness = 7 / 9 := by
  norm_num [witness, ovs, tot, nFixed]

theorem witness_rejected_by_fixed : violates (nFixed 7) witness := by
  unfold violates; rw [witness_fixed_share]; norm_num [witness, tot, nFixed]
theorem witness_breaches_contract : contractBreach 7 witness :=
  (fixed_iff_contract 7 witness).1 witness_rejected_by_fixed

/-- Counter-check: the original check accepts the witness (no violation recorded). -/
theorem witness_accepted_by_orig : ¬ violates nOrig witness := by
  unfold violates; rw [witness_orig_share]; norm_num

/-- Counter-check: the original rule does not satisfy the contract. -/
theorem counter_orig_not_contract :
    ¬ (∀ (r : ℚ) (ps : List Pos), violates nOrig ps ↔ contractBreach r ps) := by
  intro h
  exact witness_accepted_by_orig ((h 7 witness).2 witness_breaches_contract)

/-- Counter-check: the reverse of "only downward" fails — a fixed violation need not be an
original one (the witness), so the fix does change outcomes. -/
theorem counter_fixed_not_implies_orig :
    ¬ (∀ ps : List Pos, violates (nFixed 7) ps → violates nOrig ps) :=
  fun h => witness_accepted_by_orig (h witness witness_rejected_by_fixed)

end Ebv.CtaFx

#print axioms Ebv.CtaFx.nFixed_eq_cny
#print axioms Ebv.CtaFx.fixed_iff_contract
#print axioms Ebv.CtaFx.fixed_eq_orig_of_cny
#print axioms Ebv.CtaFx.split_sums
#print axioms Ebv.CtaFx.orig_violation_implies_fixed
#print axioms Ebv.CtaFx.witness_orig_share
#print axioms Ebv.CtaFx.witness_fixed_share
#print axioms Ebv.CtaFx.witness_rejected_by_fixed
#print axioms Ebv.CtaFx.witness_breaches_contract
#print axioms Ebv.CtaFx.witness_accepted_by_orig
#print axioms Ebv.CtaFx.counter_orig_not_contract
#print axioms Ebv.CtaFx.counter_fixed_not_implies_orig
