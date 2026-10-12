/-
EdgeBench Verified -- borden_source_inversion: the fixed score scale linear(0, 109) applied to
the published raw values (exact rationals).

Sources modelled
  * Harness rescale `sforge/harness/score_rescale.py` (sha256
    98feb630390f217cb67e21315b5ca8a4f2eb6d1bb28cc9822152b3ed58be4b19):
      `parse_rescale_spec` returns None when the task has no `rescale`              [43-45]
      `rescale_score` returns None when the spec is None                            [72-73]
      `linear`: `_clip(100*(raw-lower)/(upper-lower))`                               [80-84]
  * Original tasks/borden_source_inversion.json: no `judge.rescale` (score_0_100 undefined).
    Fixed repairs/borden_source_inversion-v2/task.json.in [32-36]: linear, lower 0, upper 109.
  * Published raw values (IMPACT.md "The exact corrections"; tools/estimate_impact.py
    `borden_v2(s) = 100*s/109`): 48.4, 38.5, 8.0, 15.1, 38.2.
Exact rationals stand in for doubles. 109 is the raw score of the hidden true source (case
page); that it is the maximum raw result is NOT proved here.
-/
import Mathlib.Algebra.Order.Field.Rat
import Mathlib.Tactic.NormNum
import Mathlib.Tactic.Linarith
import Mathlib.Tactic.Positivity

namespace Ebv.Borden

def clip (lo hi v : ℚ) : ℚ := max lo (min hi v)
def linear (lower upper raw : ℚ) : ℚ := clip 0 100 (100 * (raw - lower) / (upper - lower))

/-- `rescale_score` with an optional spec: None in, None out [72-73]. -/
def rescale (spec : Option (ℚ × ℚ)) (raw : ℚ) : Option ℚ :=
  spec.map fun lu => linear lu.1 lu.2 raw

def origSpec : Option (ℚ × ℚ) := none
def fixedSpec : Option (ℚ × ℚ) := some (0, 109)

theorem fixed_eq (raw : ℚ) (h0 : 0 ≤ raw) (h1 : raw ≤ 109) :
    rescale fixedSpec raw = some (100 * raw / 109) := by
  simp only [rescale, fixedSpec, Option.map_some, linear, clip, sub_zero]
  have hlo : (0 : ℚ) ≤ 100 * raw / 109 := by positivity
  have hhi : 100 * raw / 109 ≤ 100 := by rw [div_le_iff₀ (by norm_num)]; linarith
  rw [min_eq_right hhi, max_eq_right hlo]

theorem fixed_ends : rescale fixedSpec 0 = some 0 ∧ rescale fixedSpec 109 = some 100 := by
  constructor <;> norm_num [rescale, fixedSpec, linear, clip]

/-- The five published values (Opus 4.8, GPT-5.5, GPT-5.4, GLM-5.1, DS-V4-Pro). -/
theorem published :
    rescale fixedSpec 48.4 = some (4840 / 109) ∧ rescale fixedSpec 38.5 = some (3850 / 109) ∧
    rescale fixedSpec 8.0 = some (800 / 109) ∧ rescale fixedSpec 15.1 = some (1510 / 109) ∧
    rescale fixedSpec 38.2 = some (3820 / 109) := by
  refine ⟨?_, ?_, ?_, ?_, ?_⟩ <;>
    (rw [fixed_eq _ (by norm_num) (by norm_num)]; norm_num)

/-- Two decimals: 44.40, 35.32, 7.34, 13.85, 35.05 (so IMPACT.md's 44.4, 35.3, 7.3, 13.9,
35.0). Each is a half-open interval of width 0.01 around the shown value. -/
theorem published_two_dp :
    (44395 : ℚ) / 1000 ≤ 4840 / 109 ∧ (4840 : ℚ) / 109 < 44405 / 1000 ∧
    (35315 : ℚ) / 1000 ≤ 3850 / 109 ∧ (3850 : ℚ) / 109 < 35325 / 1000 ∧
    (7335 : ℚ) / 1000 ≤ 800 / 109 ∧ (800 : ℚ) / 109 < 7345 / 1000 ∧
    (13845 : ℚ) / 1000 ≤ 1510 / 109 ∧ (1510 : ℚ) / 109 < 13855 / 1000 ∧
    (35045 : ℚ) / 1000 ≤ 3820 / 109 ∧ (3820 : ℚ) / 109 < 35055 / 1000 := by
  norm_num

/-- The unclipped map is strictly increasing (on [0, 109] it equals the fixed scale, fixed_eq). -/
theorem fixed_strictMono (a b : ℚ) (hab : a < b) :
    100 * a / 109 < 100 * b / 109 := by
  apply div_lt_div_of_pos_right _ (by norm_num); linarith

/-! ## Counter-checks -/

/-- The original task defines no 0-100 score at all. -/
theorem counter_orig_undefined (raw : ℚ) : rescale origSpec raw = none := rfl

/-- The fixed scale is not the identity on published values (48.4 ↦ 44.40…, not 48.4). -/
theorem counter_not_identity : rescale fixedSpec 48.4 ≠ some 48.4 := by
  rw [fixed_eq _ (by norm_num) (by norm_num)]; norm_num

/-- A default clip(raw, 0, 100) reading (score_rescale.py [196], unknown kinds) would tie the
true source (109) with raw 100, unlike the fixed scale. -/
theorem counter_default_clip_ties :
    clip 0 100 109 = clip 0 100 100 ∧ rescale fixedSpec 100 ≠ rescale fixedSpec 109 := by
  refine ⟨by norm_num [clip], ?_⟩
  rw [fixed_eq _ (by norm_num) (by norm_num), fixed_eq _ (by norm_num) le_rfl]; norm_num

end Ebv.Borden

#print axioms Ebv.Borden.fixed_eq
#print axioms Ebv.Borden.fixed_ends
#print axioms Ebv.Borden.published
#print axioms Ebv.Borden.published_two_dp
#print axioms Ebv.Borden.fixed_strictMono
#print axioms Ebv.Borden.counter_orig_undefined
#print axioms Ebv.Borden.counter_not_identity
#print axioms Ebv.Borden.counter_default_clip_ties
