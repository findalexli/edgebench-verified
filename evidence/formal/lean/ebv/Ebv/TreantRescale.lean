/-
EdgeBench Verified -- treant_forest: the score cap and the two score scales (exact rationals).

Sources modelled
  * Harness rescale: `sforge/harness/score_rescale.py` in this repository,
    sha256 98feb630390f217cb67e21315b5ca8a4f2eb6d1bb28cc9822152b3ed58be4b19.
      `_clip(v, lo, hi) = max(lo, min(hi, v))`                         [60-63]
      `linear`: `_clip(100*(raw-lower)/(upper-lower))`                  [80-84]
      `piecewise_max`: baseline / rank30 / rank1 / super_anchor          [137-153]
  * Tester: `tools/bin/tester` in
    seededge/edgebench.judge.treant_forest@sha256:783e9ca24139ac6aa672ec0576b5f75648e8ad47c0d937988deeb41b639bf21a,
    sha256 6cbb3a729d0899495bf924f39d34b5cb2767ec167dffa727e1c064911e0e8551
    (local copy evidence/scripts/_game-tasks-correctness/orig/treant_tester, same sha256).
      `max_turns = N * N * 2`                                           [63]
      `turns = 0`                                                       [65]
      `while turns < max_turns:` ... goal check / break                  [140-145]
      `turns += 1` (once per iteration)                                 [202]
      break after the move if the goal is reached                       [245-246]
      `Score = {turns}`                                                 [250]
    WA / invalid paths call `sys.exit(1)` without a Score line.
  * Evaluator `/tmp/eval_treants_forest.py`, sha256
    ce2833ac1fadf2fc531901b4a168b31942530a8ac64decf7b762252983682048: TOTAL_SCORE is the sum of
    the per-case Score over cases with status OK; every other status adds nothing        [52-58]
  * Task JSON tasks/treant_forest.json (sha256 2fdb98ce...a615e): piecewise_max
    5369 / 88189 / 330195 / 451198; fixed task.json.in: linear 3418 / 92304.

Model abstractions
  * Python floats are replaced by exact rationals (ℚ); the grader computes in IEEE doubles, so
    its outputs agree with these values only up to rounding (checked below for the cap value).
  * The tester's loop body (path finding, treant placement, reveals) is abstracted into two
    arbitrary predicates `stopBefore` / `stopAfter`; only the turn counter is modelled.
  * The per-case grid sizes N_i of the 50 shipped cases are NOT available in this repository or
    in a local image, so Σ 2·N_i² = 92304 is not re-derived here. It is the value computed by
    evidence/scripts/_game-tasks-correctness/check_arith.py on the shipped cases (listing sha256
    bc256294fcbd5fe2850fc5c7d568430bafa95489f8a64f8de35903c401dafbb0), saved in
    check_arith.out.json. The theorems below take it as the named constant `capTotal`.
-/
import Mathlib.Algebra.Order.Field.Rat
import Mathlib.Tactic.NormNum
import Mathlib.Tactic.Linarith
import Mathlib.Tactic.Ring
import Mathlib.Tactic.FieldSimp

namespace Ebv.Treant

/-! ## Harness rescale functions (score_rescale.py) -/

/-- `_clip` [60-63]. -/
def clip (lo hi v : ℚ) : ℚ := max lo (min hi v)

/-- `linear` [80-84] (the `upper = lower` NaN branch is excluded by the hypotheses used). -/
def linear (lower upper raw : ℚ) : ℚ := clip 0 100 (100 * (raw - lower) / (upper - lower))

/-- `piecewise_max` [137-153]. -/
def piecewiseMax (b r30 r1 sup raw : ℚ) : ℚ :=
  if raw ≤ b then 0
  else if raw ≤ r30 then clip 0 20 (20 * (raw - b) / (r30 - b))
  else if raw ≤ r1 then clip 20 80 (20 + 60 * (raw - r30) / (r1 - r30))
  else if raw ≤ sup then clip 80 100 (80 + 20 * (raw - r1) / (sup - r1))
  else 100

/-- Original treant scale (tasks/treant_forest.json). -/
def orig (raw : ℚ) : ℚ := piecewiseMax 5369 88189 330195 451198 raw
/-- Fixed treant scale (repairs/treant_forest-v2/task.json.in). -/
def fixed (raw : ℚ) : ℚ := linear 3418 92304 raw

/-! ## Tester turn counter: a case's score never exceeds 2·N² -/

/-- The `while turns < max_turns` loop [140-246] with the body abstracted: `stopBefore t` is the
goal check at the top of an iteration [143-145] (and any other exit before `turns += 1`),
`stopAfter t` the check after the move [245-246]. `fuel` bounds the number of iterations. -/
def loop (maxT : ℕ) (stopBefore stopAfter : ℕ → Bool) : ℕ → ℕ → ℕ
  | 0, t => t
  | fuel + 1, t =>
    if t < maxT then
      if stopBefore t then t
      else if stopAfter (t + 1) then t + 1
      else loop maxT stopBefore stopAfter fuel (t + 1)
    else t

theorem loop_le (maxT : ℕ) (sb sa : ℕ → Bool) :
    ∀ (fuel t : ℕ), t ≤ maxT → loop maxT sb sa fuel t ≤ maxT := by
  intro fuel
  induction fuel with
  | zero => intro t h; simpa [loop] using h
  | succ k ih =>
    intro t h
    unfold loop
    split_ifs with h1 h2 h3
    · exact h
    · omega
    · exact ih (t + 1) (by omega)
    · exact h

/-- Per-case score (the printed `turns`, starting from 0 [65]) is at most 2·N² [63]. -/
theorem case_score_le (N : ℕ) (sb sa : ℕ → Bool) (fuel : ℕ) :
    loop (N * N * 2) sb sa fuel 0 ≤ 2 * N ^ 2 := by
  have := loop_le (N * N * 2) sb sa fuel 0 (Nat.zero_le _)
  have e : N * N * 2 = 2 * N ^ 2 := by ring
  omega

/-- TOTAL_SCORE over any list of cases: a case contributes its turns if OK, else 0 [52-58].
`ok i = true` with `turns i ≤ 2 N_i²` for OK cases. -/
def total : List (Bool × ℕ) → ℕ
  | [] => 0
  | (ok, t) :: rest => (if ok then t else 0) + total rest

def capSum : List ℕ → ℕ
  | [] => 0
  | n :: rest => 2 * n ^ 2 + capSum rest

theorem total_le_capSum :
    ∀ (cs : List ((Bool × ℕ) × ℕ)), (∀ c ∈ cs, c.1.2 ≤ 2 * c.2 ^ 2) →
      total (cs.map Prod.fst) ≤ capSum (cs.map Prod.snd) := by
  intro cs
  induction cs with
  | nil => intro _; simp [total, capSum]
  | cons c rest ih =>
    intro h
    obtain ⟨⟨ok, t⟩, n⟩ := c
    have hc : t ≤ 2 * n ^ 2 := h _ List.mem_cons_self
    have hr := ih (fun x hx => h x (List.mem_cons_of_mem _ hx))
    simp only [List.map, total, capSum]
    split_ifs <;> omega

/-! ## The cap and the two scales -/

/-- Σ 2·N_i² over the 50 shipped cases, as computed by check_arith.py (not re-derived here). -/
def capTotal : ℚ := 92304

/-- Published: the cap maps to exactly 2543510/121003 ≈ 21.02 under the original scale. -/
theorem orig_cap : orig capTotal = 2543510 / 121003 := by
  norm_num [orig, piecewiseMax, clip, capTotal]

/-- No raw total at or below the cap scores above 2543510/121003 under the original scale. -/
theorem orig_le_of_le_cap (raw : ℚ) (h : raw ≤ capTotal) : orig raw ≤ 2543510 / 121003 := by
  unfold capTotal at h
  unfold orig piecewiseMax clip
  split_ifs with h1 h2 h3
  · norm_num
  · have : 20 * (raw - 5369) / (88189 - 5369) ≤ 20 := by
      rw [div_le_iff₀ (by norm_num)]; linarith
    rw [max_le_iff]; constructor
    · norm_num
    · exact le_trans (min_le_right _ _) (by linarith)
  · have : 20 + 60 * (raw - 88189) / (330195 - 88189) ≤ 2543510 / 121003 := by
      have e : 20 + 60 * (raw - 88189) / (330195 - 88189) = 20 + 60 * (raw - 88189) / 242006 := by
        norm_num
      rw [e]
      have : 60 * (raw - 88189) / 242006 ≤ 60 * (92304 - 88189) / 242006 := by
        apply div_le_div_of_nonneg_right _ (by norm_num); linarith
      have e2 : (20 : ℚ) + 60 * (92304 - 88189) / 242006 = 2543510 / 121003 := by norm_num
      linarith
    rw [max_le_iff]; constructor
    · norm_num
    · exact le_trans (min_le_right _ _) this
  · exfalso; linarith
  · exfalso; linarith

/-- The cap is attained only at the cap: the bound above is the exact maximum of the scale on
reachable totals (it is the value at `capTotal`). Fixed scale: end points. -/
theorem fixed_baseline : fixed 3418 = 0 := by norm_num [fixed, linear, clip]
theorem fixed_cap : fixed capTotal = 100 := by norm_num [fixed, linear, clip, capTotal]

/-- Values in the case-page table. -/
theorem fixed_5369 : fixed 5369 = 97550 / 44443 := by norm_num [fixed, linear, clip]
theorem orig_baseline : orig 3418 = 0 := by norm_num [orig, piecewiseMax]
theorem orig_rank1 : orig 330195 = 80 := by norm_num [orig, piecewiseMax, clip]
theorem fixed_rank1 : fixed 330195 = 100 := by norm_num [fixed, linear, clip]
theorem orig_greedy : orig 17960 = 12591 / 4141 := by norm_num [orig, piecewiseMax, clip]
theorem fixed_greedy : fixed 17960 = 727100 / 44443 := by norm_num [fixed, linear, clip]
theorem greedy_two_dp :
    (3035 : ℚ) / 1000 ≤ 12591 / 4141 ∧ (12591 : ℚ) / 4141 < 3045 / 1000 ∧
    (16355 : ℚ) / 1000 ≤ 727100 / 44443 ∧ (727100 : ℚ) / 44443 < 16365 / 1000 := by norm_num
/-- rank1 / cap ≈ 3.58. -/
theorem rank1_over_cap : (3575 : ℚ) / 1000 ≤ 330195 / 92304 ∧ (330195 : ℚ) / 92304 < 3585 / 1000 := by
  norm_num

/-- Differential check: the saved Python value `rescaled_cap = 21.02022263910812`
(check_arith.out.json, computed in doubles by score_rescale.py) is within 1e-13 of the exact value. -/
theorem cap_matches_python :
    |(2543510 : ℚ) / 121003 - 21.02022263910812| < 1 / 10 ^ 13 := by
  rw [abs_lt]; constructor <;> norm_num

/-! ## Inversion used in IMPACT.md -/

/-- For raw in (5369, 88189] the original scale is the line s = 20(raw-5369)/82820. -/
theorem orig_on_segment (raw : ℚ) (h1 : 5369 < raw) (h2 : raw ≤ 88189) :
    orig raw = 20 * (raw - 5369) / 82820 := by
  have hlo : 0 ≤ 20 * (raw - 5369) / 82820 := by
    apply div_nonneg _ (by norm_num); linarith
  have hhi : 20 * (raw - 5369) / 82820 ≤ 20 := by
    rw [div_le_iff₀ (by norm_num)]; linarith
  unfold orig piecewiseMax clip
  rw [if_neg (by linarith), if_pos h2]
  norm_num
  rw [min_eq_right (by linarith), max_eq_right (by linarith)]

/-- Inverse map: for s in (0, 20), raw = 5369 + s/20·82820 is the unique raw total with
original score s, and it lies inside the first segment. -/
def inv (s : ℚ) : ℚ := 5369 + s / 20 * 82820

theorem inv_correct (s : ℚ) (h0 : 0 < s) (h20 : s < 20) : orig (inv s) = s := by
  unfold inv
  rw [orig_on_segment _ (by nlinarith) (by nlinarith)]
  field_simp
  ring

theorem inv_unique (s raw : ℚ) (h0 : 0 < s) (h20 : s < 20) (h : orig raw = s) : raw = inv s := by
  unfold orig piecewiseMax clip at h
  split_ifs at h with h1 h2 h3 h4
  · linarith
  · -- first segment
    have hlo : 0 ≤ 20 * (raw - 5369) / (88189 - 5369) := by
      apply div_nonneg _ (by norm_num); linarith
    have hhi : 20 * (raw - 5369) / (88189 - 5369) ≤ 20 := by
      rw [div_le_iff₀ (by norm_num)]; linarith
    rw [min_eq_right hhi, max_eq_right hlo] at h
    unfold inv
    rw [← h]; field_simp; ring
  · -- second segment: the value is ≥ 20
    have : (20 : ℚ) ≤ max 20 (min 80 (20 + 60 * (raw - 88189) / (330195 - 88189))) :=
      le_max_left _ _
    linarith
  · have : (80 : ℚ) ≤ max 80 (min 100 (80 + 20 * (raw - 330195) / (451198 - 330195))) :=
      le_max_left _ _
    linarith
  · linarith

/-- The fixed score as a function of the original score s ∈ (0, 20). -/
theorem fixed_of_orig (s : ℚ) (h0 : 0 < s) (h20 : s < 20) :
    fixed (inv s) = 100 * (1951 + s * 4141) / 88886 := by
  unfold fixed linear clip inv
  have hlo : (0 : ℚ) ≤ 100 * (5369 + s / 20 * 82820 - 3418) / (92304 - 3418) := by
    apply div_nonneg _ (by norm_num); nlinarith
  have hhi : 100 * (5369 + s / 20 * 82820 - 3418) / (92304 - 3418) ≤ 100 := by
    rw [div_le_iff₀ (by norm_num)]; nlinarith
  rw [min_eq_right hhi, max_eq_right hlo]
  field_simp; ring

/-- The five published Treant scores (Opus 4.8, GPT-5.5, GPT-5.4, GLM-5.1, DS-V4-Pro). -/
theorem published_fixed :
    fixed (inv 18) = 3824450 / 44443 ∧ fixed (inv (156/10)) = 3327530 / 44443 ∧
    fixed (inv (133/10)) = 2851315 / 44443 ∧ fixed (inv (169/10)) = 3596695 / 44443 ∧
    fixed (inv (135/10)) = 2892725 / 44443 := by
  refine ⟨?_, ?_, ?_, ?_, ?_⟩ <;>
    (rw [fixed_of_orig _ (by norm_num) (by norm_num)]; norm_num)

/-- Two-decimal values: 86.05, 74.87, 64.16, 80.93, 65.09 (IMPACT.md one-decimal values
86.1, 74.9, 64.2, 80.9, 65.1 follow). Each is stated as a half-open interval of width 0.01
around the shown value. -/
theorem published_two_dp :
    (86045 : ℚ) / 1000 ≤ 3824450 / 44443 ∧ (3824450 : ℚ) / 44443 < 86055 / 1000 ∧
    (74865 : ℚ) / 1000 ≤ 3327530 / 44443 ∧ (3327530 : ℚ) / 44443 < 74875 / 1000 ∧
    (64155 : ℚ) / 1000 ≤ 2851315 / 44443 ∧ (2851315 : ℚ) / 44443 < 64165 / 1000 ∧
    (80925 : ℚ) / 1000 ≤ 3596695 / 44443 ∧ (3596695 : ℚ) / 44443 < 80935 / 1000 ∧
    (65085 : ℚ) / 1000 ≤ 2892725 / 44443 ∧ (2892725 : ℚ) / 44443 < 65095 / 1000 := by
  norm_num

/-! ## Counter-checks (must come out the other way) -/

/-- A too-strong bound is false: the cap scores above 21 under the original scale. -/
theorem counter_orig_cap_gt_21 : ¬ (orig capTotal ≤ 21) := by
  rw [orig_cap]; norm_num

/-- The original scale does not give 100 at the cap (the fixed one does). -/
theorem counter_orig_cap_ne_100 : orig capTotal ≠ 100 := by rw [orig_cap]; norm_num

/-- A value above 20 does not invert by the segment-1 formula: inv 20.5 lands on the second
segment and scores 2482175/121003 ≈ 20.513, not 20.5. -/
theorem counter_inv_above_20 : orig (inv (205/10)) = 2482175 / 121003 ∧
    orig (inv (205/10)) ≠ 205/10 := by
  have h : orig (inv (205/10)) = 2482175 / 121003 := by
    norm_num [orig, inv, piecewiseMax, clip]
  exact ⟨h, by rw [h]; norm_num⟩

/-- The inversion also fails at s = 0: every raw ≤ 5369 has original score 0, but fixed scores
there range over [0, 97550/44443]; e.g. the shipped baseline 3418 has orig 0 and fixed 0, while
inv 0 = 5369 has fixed 97550/44443. So a run with original score 0 is not converted exactly. -/
theorem counter_inv_at_zero : orig 3418 = 0 ∧ inv 0 = 5369 ∧ fixed 3418 ≠ fixed (inv 0) := by
  refine ⟨orig_baseline, by norm_num [inv], ?_⟩
  rw [fixed_baseline, show inv 0 = 5369 by norm_num [inv], fixed_5369]; norm_num

end Ebv.Treant

#print axioms Ebv.Treant.loop_le
#print axioms Ebv.Treant.case_score_le
#print axioms Ebv.Treant.total_le_capSum
#print axioms Ebv.Treant.orig_cap
#print axioms Ebv.Treant.orig_le_of_le_cap
#print axioms Ebv.Treant.fixed_baseline
#print axioms Ebv.Treant.fixed_cap
#print axioms Ebv.Treant.fixed_5369
#print axioms Ebv.Treant.orig_greedy
#print axioms Ebv.Treant.fixed_greedy
#print axioms Ebv.Treant.cap_matches_python
#print axioms Ebv.Treant.orig_on_segment
#print axioms Ebv.Treant.inv_correct
#print axioms Ebv.Treant.inv_unique
#print axioms Ebv.Treant.fixed_of_orig
#print axioms Ebv.Treant.published_fixed
#print axioms Ebv.Treant.published_two_dp
#print axioms Ebv.Treant.counter_orig_cap_gt_21
#print axioms Ebv.Treant.counter_orig_cap_ne_100
#print axioms Ebv.Treant.counter_inv_above_20
#print axioms Ebv.Treant.counter_inv_at_zero
