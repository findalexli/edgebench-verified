import Mathlib.Tactic.NormNum
import Mathlib.Tactic.Linarith
import Mathlib.Algebra.Order.Field.Rat

/-! # bipedalwalker_locomotion_rl: the score out of 100 is confined to [0, 30]

Claim. For every pair of mean rewards and every outcome of the four engineering checks, the
task score, and hence the score out of 100 after the task's `linear` rescale (lower 0, upper 100),
lies in [0, 30]. 30 is attained (all four checks pass, both mean rewards 300); with three or
fewer checks passing the score is at most 27.5. The `min(30, ...)` in the code never binds: 10 (checks) + 20 (reward) is already 30.
Table values: missing checkpoint 2.5, loadable-untrained 10, normal-only (300, -100) 18, perfect 30.

Sources modelled (work image copy `/home/workspace/loco-rl/`):
* `sebench_eval.py` sha256 9bb2f8bf44ac02849ae723bd1035bfd0194042daa5b132b305ecd2e526c2838a
  - lines 39-40 `compute_normal_score`, 43-44 `compute_hardcore_score`, 47-48 `compute_final_score`
  - lines 122-126 `strict_score`: `10*e/4 + 20*clip(final,0,100)/100`, then `min(30, ...)`;
    `round(score, 2)` (line 127) is abstracted away (it cannot push a value ≤ 30 above 30).
  - lines 148-204: exactly one detail is appended for each of the four names
    `engineering/{dependencies_import, checkpoint_submitted, policy_loads, policy_evaluates}`,
    so `engineering_passed` (217-220) is in 0..4: hypothesis `he : e ≤ 4`.
  - lines 169-173, 197-198: rewards default to -200 / scores to 0 when not evaluated.
* `sforge/harness/score_rescale.py` sha256 98feb630390f217cb67e21315b5ca8a4f2eb6d1bb28cc9822152b3ed58be4b19,
  lines 80-84 (`linear`) and 60-63 (`_clip`).
* `tasks/bipedalwalker_locomotion_rl.json`: rescale `{"kind": "linear", "lower": 0.0, "upper": 100.0}`,
  parser `structured_json` (the JSON `score` field).
* `task_prompt.md` sha256 e4023718e500912b17e9d8285ad34055ce9a80706304697b96f6e150f36aadcf, lines
  117-118: "engineering checks plus `0.20 * final_score`, capped at 30" (the stated design). -/

namespace Ebv.Bipedal

def clip (lo hi v : ℚ) : ℚ := max lo (min hi v)

def normalScore (r : ℚ) : ℚ := clip 0 1 (r / 300) * 100            -- 39-40
def hardScore (r : ℚ) : ℚ := clip 0 1 ((r + 100) / 400) * 100      -- 43-44
def finalScore (n h : ℚ) : ℚ := 4 / 10 * n + 6 / 10 * h            -- 47-48
def strictScore (e : ℕ) (f : ℚ) : ℚ :=                             -- 122-126
  min 30 (10 * (e : ℚ) / 4 + 20 * (clip 0 100 f / 100))
def linear (raw : ℚ) : ℚ := clip 0 100 (100 * (raw - 0) / (100 - 0))   -- score_rescale 80-84

/-- End-to-end score out of 100 for engineering count `e` and mean rewards `rn`, `rh`. -/
def score100 (e : ℕ) (rn rh : ℚ) : ℚ := linear (strictScore e (finalScore (normalScore rn) (hardScore rh)))

theorem clip_bounds (lo hi v : ℚ) (h : lo ≤ hi) : lo ≤ clip lo hi v ∧ clip lo hi v ≤ hi := by
  unfold clip
  exact ⟨le_max_left _ _, max_le h (min_le_left _ _)⟩

/-- Without the `min`, the uncapped sum is already in [0, 30]. -/
theorem uncapped_bounds (e : ℕ) (he : e ≤ 4) (f : ℚ) :
    0 ≤ 10 * (e : ℚ) / 4 + 20 * (clip 0 100 f / 100) ∧
    10 * (e : ℚ) / 4 + 20 * (clip 0 100 f / 100) ≤ 30 := by
  obtain ⟨c0, c1⟩ := clip_bounds 0 100 f (by norm_num)
  have he' : (e : ℚ) ≤ 4 := by exact_mod_cast he
  have he0 : (0 : ℚ) ≤ e := Nat.cast_nonneg e
  constructor <;> linarith

/-- The `min 30` never binds. -/
theorem min_never_binds (e : ℕ) (he : e ≤ 4) (f : ℚ) :
    strictScore e f = 10 * (e : ℚ) / 4 + 20 * (clip 0 100 f / 100) := by
  unfold strictScore; exact min_eq_right (uncapped_bounds e he f).2

theorem linear_id (x : ℚ) (h0 : 0 ≤ x) (h1 : x ≤ 100) : linear x = x := by
  unfold linear clip
  rw [show 100 * (x - 0) / (100 - 0) = x by norm_num, min_eq_right h1, max_eq_right h0]

/-- Main theorem: the score out of 100 is in [0, 30] for every input. -/
theorem score100_bounds (e : ℕ) (he : e ≤ 4) (rn rh : ℚ) :
    0 ≤ score100 e rn rh ∧ score100 e rn rh ≤ 30 := by
  unfold score100
  rw [min_never_binds e he]
  obtain ⟨u0, u1⟩ := uncapped_bounds e he (finalScore (normalScore rn) (hardScore rh))
  rw [linear_id _ u0 (by linarith)]
  exact ⟨u0, u1⟩

/-- 30 is attained (perfect policy, all checks passing). -/
theorem perfect_30 : score100 4 300 300 = 30 := by
  norm_num [score100, linear, strictScore, finalScore, normalScore, hardScore, clip]

/-- 30 requires all four checks: with e ≤ 3 the score is at most 27.5. -/
theorem needs_all_checks (e : ℕ) (he : e ≤ 3) (rn rh : ℚ) : score100 e rn rh ≤ 55 / 2 := by
  unfold score100
  rw [min_never_binds e (by omega)]
  obtain ⟨u0, u1⟩ := uncapped_bounds e (by omega) (finalScore (normalScore rn) (hardScore rh))
  rw [linear_id _ u0 (by linarith)]
  obtain ⟨c0, c1⟩ := clip_bounds 0 100 (finalScore (normalScore rn) (hardScore rh)) (by norm_num)
  have he' : (e : ℚ) ≤ 3 := by exact_mod_cast he
  linarith

/-- Differential check against the case table (computed there with the original functions). -/
theorem table_missing : score100 1 (-200) (-200) = 5 / 2 := by
  norm_num [score100, linear, strictScore, finalScore, normalScore, hardScore, clip]
theorem table_untrained : score100 4 (-100) (-100) = 10 := by
  norm_num [score100, linear, strictScore, finalScore, normalScore, hardScore, clip]
theorem table_normal_only : score100 4 300 (-100) = 18 := by
  norm_num [score100, linear, strictScore, finalScore, normalScore, hardScore, clip]

/-! ## Counter-checks (must come out the other way) -/

/-- A too-strong bound (score < 30 always) is false. -/
theorem counter_not_below_30 : ¬ (∀ e ≤ 4, ∀ rn rh : ℚ, score100 e rn rh < 30) := by
  intro h; have := h 4 le_rfl 300 300; rw [perfect_30] at this; exact lt_irrefl _ this

/-- The rescale's upper anchor, 100, is not reachable: no input gives more than 30. -/
theorem counter_100_unreachable : ¬ ∃ e ≤ 4, ∃ rn rh : ℚ, 30 < score100 e rn rh := by
  rintro ⟨e, he, rn, rh, h⟩; linarith [(score100_bounds e he rn rh).2]

/-- The engineering-count bound matters for the uncapped sum: with e = 5 it would be 32.5,
so then it is the `min 30` that caps (the code never reaches this, see lines 148-204). -/
theorem counter_e5_uncapped : 10 * ((5 : ℕ) : ℚ) / 4 + 20 * (clip 0 100 100 / 100) = 65 / 2 := by
  norm_num [clip]

end Ebv.Bipedal

#print axioms Ebv.Bipedal.score100_bounds
#print axioms Ebv.Bipedal.min_never_binds
#print axioms Ebv.Bipedal.perfect_30
#print axioms Ebv.Bipedal.needs_all_checks
#print axioms Ebv.Bipedal.table_missing
#print axioms Ebv.Bipedal.table_untrained
#print axioms Ebv.Bipedal.table_normal_only
#print axioms Ebv.Bipedal.counter_not_below_30
#print axioms Ebv.Bipedal.counter_100_unreachable
#print axioms Ebv.Bipedal.counter_e5_uncapped
