import Mathlib.Tactic.NormNum
import Mathlib.Tactic.Linarith
import Mathlib.Algebra.Order.Field.Rat

/-! # grid_turing_robot: the baseline-anchor offset is exactly 2.84 points (2.84005...)

Claim. Under the task's `piecewise_min` rescale (baseline 9,025,986, rank30 4,490), the shipped
do-nothing solution, whose 50 case scores sum to 7,744,909, scores exactly
20·(9025986 − 7744909)/(9025986 − 4490) = 6405385/2255374 ≈ 2.84005 out of 100, not 0.
Compared with the same scale anchored at 7,744,909, the extra credit is ≥ 0 for every raw score,
at most 6405385/2255374, attained at raw = 7,744,909, and zero at or below rank30.

Sources modelled:
* `sforge/harness/score_rescale.py` sha256 98feb630390f217cb67e21315b5ca8a4f2eb6d1bb28cc9822152b3ed58be4b19
  (upstream and maintained identical): `_clip` lines 60-63, `piecewise_min` lines 155-171.
  Only the first two branches matter here (raw ≤ 0 or raw ≥ baseline → 0, lines 157-158;
  rank30 ≤ raw < baseline → clip(20·(baseline − raw)/(baseline − rank30), 0, 20), lines 159-162).
  Below rank30 the result does not depend on `baseline` (lines 163-171), modelled as an
  arbitrary function `low`.
* `tasks/grid_turing_robot.json` sha256 b88eff2092c1cd10f2356746f0e486f094d09c0c3966497ad1a798f7e7b83948:
  rescale piecewise_min, baseline 9025986.0, rank30 4490.0, rank1 1575.0, super_anchor 554.75.
* `evidence/scripts/grid_turing_robot/native/shipped_baseline.log` sha256
  bb916f62db1ff325268ee5696a30babe617a5644d22a11935337eb133e9b8aa9: the 50 CASE scores of the
  shipped baseline under the original grader (`TOTAL_SCORE 7744909`). -/

namespace Ebv.GridTuring

def clip (lo hi v : ℚ) : ℚ := max lo (min hi v)

/-- `piecewise_min` (score_rescale.py 155-171). `low` stands for the branches below rank30,
which do not read `B`. -/
def pmin (low : ℚ → ℚ) (B R30 raw : ℚ) : ℚ :=
  if raw ≤ 0 ∨ B ≤ raw then 0
  else if R30 ≤ raw then clip 0 20 (20 * (B - raw) / (B - R30))
  else low raw

def B : ℚ := 9025986
def R30 : ℚ := 4490
/-- Measured total of the shipped baseline. -/
def B' : ℚ := 7744909

/-- The 50 per-case scores of the shipped baseline (shipped_baseline.log, CASE 0000..0049). -/
def baselineCases : List ℚ :=
  [117900, 308294, 216461, 56736, 83888, 22000, 67093, 113175, 63713, 54288, 248184, 270216,
   61056, 406400, 147200, 29800, 144450, 180047, 262764, 47376, 98784, 72670, 278692, 111150,
   315153, 214727, 114075, 61178, 175712, 261792, 433200, 412000, 226865, 141824, 27000, 53280,
   260172, 94668, 37631, 341506, 96040, 32912, 331037, 48960, 69797, 51408, 241056, 61854,
   32549, 146176]

theorem baseline_cases_count : baselineCases.length = 50 := by rfl
theorem baseline_sum : baselineCases.sum = B' := by norm_num [baselineCases, B']

theorem clip_id (x : ℚ) (h0 : 0 ≤ x) (h1 : x ≤ 20) : clip 0 20 x = x := by
  unfold clip; rw [min_eq_right h1, max_eq_right h0]

/-- The shipped baseline's score out of 100, exactly. -/
theorem baseline_score (low : ℚ → ℚ) : pmin low B R30 B' = 6405385 / 2255374 := by
  have h1 : ¬ (B' ≤ 0 ∨ B ≤ B') := by norm_num [B, B']
  have h2 : R30 ≤ B' := by norm_num [R30, B']
  simp only [pmin, h1, h2, ↓reduceIte]
  rw [clip_id _ (by norm_num [B, B', R30]) (by norm_num [B, B', R30])]
  norm_num [B, B', R30]

theorem baseline_score_bounds : (284 : ℚ) / 100 < 6405385 / 2255374 ∧
    (6405385 : ℚ) / 2255374 < 28401 / 10000 := by norm_num

/-- Differential check against `native/grade_out.txt` (normalized=19.8014 and 19.5614, rounded). -/
theorem diff_good (low : ℚ → ℚ) :
    pmin low B R30 94092 = 20 * 8931894 / 9021496 ∧
    (198013 : ℚ) / 10000 < 20 * 8931894 / 9021496 ∧ (20 * 8931894 : ℚ) / 9021496 < 198014 / 10000 := by
  have h1 : ¬ ((94092 : ℚ) ≤ 0 ∨ B ≤ 94092) := by norm_num [B]
  have h2 : R30 ≤ (94092 : ℚ) := by norm_num [R30]
  refine ⟨?_, by norm_num, by norm_num⟩
  simp only [pmin, h1, h2, ↓reduceIte]
  rw [clip_id _ (by norm_num [B, R30]) (by norm_num [B, R30])]
  norm_num [B, R30]

/-- Extra credit from the misplaced anchor, for every raw score: between 0 and the
baseline's 6405385/2255374, and 0 at or below rank30. -/
theorem offset_bounds (low : ℚ → ℚ) (r : ℚ) :
    0 ≤ pmin low B R30 r - pmin low B' R30 r ∧
    pmin low B R30 r - pmin low B' R30 r ≤ 6405385 / 2255374 ∧
    (r < R30 → pmin low B R30 r - pmin low B' R30 r = 0) := by
  unfold pmin
  by_cases hr0 : r ≤ 0
  · simp only [hr0, true_or, ↓reduceIte, sub_self]
    exact ⟨le_refl _, by norm_num, fun _ => by simp⟩
  by_cases hrB : B ≤ r
  · have hrB' : B' ≤ r := le_trans (by norm_num [B, B']) hrB
    simp only [hr0, hrB, hrB', or_true, ↓reduceIte, sub_self]
    exact ⟨le_refl _, by norm_num, fun _ => by simp⟩
  have hrB_lt : r < B := lt_of_not_ge hrB
  by_cases hrB' : B' ≤ r
  · -- only the original scale gives credit: 20(B - r)/(B - R30) ≤ value at r = B'
    have hR : R30 ≤ r := le_trans (by norm_num [R30, B']) hrB'
    simp only [hr0, hrB, hrB', hR, or_true, or_false, ↓reduceIte, sub_zero]
    unfold B R30 B' at *
    rw [clip_id _ (by
        apply div_nonneg <;> linarith) (by
        rw [div_le_iff₀ (by norm_num)]; linarith)]
    refine ⟨div_nonneg (by linarith) (by norm_num), ?_, fun h => absurd h (by linarith)⟩
    rw [div_le_div_iff₀ (by norm_num) (by norm_num)]; linarith
  · have hrB'_lt : r < B' := lt_of_not_ge hrB'
    by_cases hR : R30 ≤ r
    · simp only [hr0, hrB, hrB', hR, or_false, ↓reduceIte]
      unfold B R30 B' at *
      rw [clip_id _ (by apply div_nonneg <;> linarith) (by
          rw [div_le_iff₀ (by norm_num)]; linarith),
        clip_id _ (by apply div_nonneg <;> linarith) (by
          rw [div_le_iff₀ (by norm_num)]; linarith)]
      refine ⟨?_, ?_, fun h => absurd h (by linarith)⟩
      · rw [sub_nonneg, div_le_div_iff₀ (by norm_num) (by norm_num)]; nlinarith
      · rw [div_sub_div _ _ (by norm_num) (by norm_num),
          div_le_div_iff₀ (by norm_num) (by norm_num)]; nlinarith
    · simp only [hr0, hrB, hrB', hR, or_false, ↓reduceIte, sub_self]
      exact ⟨le_refl _, by norm_num, fun _ => by simp⟩

/-! ## Counter-checks (must come out the other way) -/

/-- The do-nothing baseline does not score 0 under the configured anchor... -/
theorem counter_not_zero (low : ℚ → ℚ) : pmin low B R30 B' ≠ 0 := by
  rw [baseline_score]; norm_num

/-- ...but does score 0 under the measured anchor. -/
theorem counter_fixed_zero (low : ℚ → ℚ) : pmin low B' R30 B' = 0 := by
  simp [pmin]

/-- A too-strong bound (offset ≤ 2.84 exactly) is false: the exact offset exceeds 2.84. -/
theorem counter_too_strong (low : ℚ → ℚ) :
    ¬ (pmin low B R30 B' - pmin low B' R30 B' ≤ 284 / 100) := by
  rw [baseline_score, counter_fixed_zero]; norm_num

end Ebv.GridTuring

#print axioms Ebv.GridTuring.baseline_sum
#print axioms Ebv.GridTuring.baseline_score
#print axioms Ebv.GridTuring.baseline_score_bounds
#print axioms Ebv.GridTuring.diff_good
#print axioms Ebv.GridTuring.offset_bounds
#print axioms Ebv.GridTuring.counter_not_zero
#print axioms Ebv.GridTuring.counter_fixed_zero
#print axioms Ebv.GridTuring.counter_too_strong
