import Mathlib.Analysis.SpecialFunctions.Log.Basic
import Mathlib.Tactic.NormNum
import Mathlib.Tactic.Linarith
import Mathlib.Tactic.Positivity

/-!
# ffmpeg_swscale_reimplementation: speed credit for failing / no-op timed calls

Source modelled:
* Original `/opt/tests/compute_reward.py` in
  `seededge/edgebench.judge.ffmpeg_swscale_reimplementation@sha256:38b256686afe14f6cec76790a7e884eb46ac70eb918a60351942a9c35c0f879f`,
  sha256 `2f457ffd67d624f9f739b4dd34b80b858a9bbb152e40e4385a8c10a81159365b`:
  - `bench_lib` l.515-541: `lib.swscale_process(...)` return value discarded (l.528, l.534),
    output buffer never read; returns the median time, or None if `swscale_create` is NULL.
  - l.543-549 exception -> speedup 0; l.552-554 NULL ctx -> 0; l.556-557
    `speedup = base_time / max(cand_time, 1e-15)`                       -> `origSpeedup`
  - l.671-677 `safe = max(s, 1e-15)`; `geo = exp(sum(log safe) / n)`    -> `safe`, `geo`
* Fixed `files/compute_reward.py` (v2), sha256
  `6d4e1095f906955833405bf714aab14644029288790d41f38783bafb7f3a132a`:
  - l.526-549 first nonzero return code of the 110 calls, plus the last call's output;
  - l.569-577 baseline or candidate return != 0 -> speedup 0;
  - l.578-594 any output plane below the PSNR threshold (40 dB scaling, 60 dB same size,
    the `check_correctness` thresholds, l.37-38) -> speedup 0;
  - l.596-597 otherwise the same speedup as the original                -> `fixedSpeedup`
  - l.710-716 geometric mean unchanged.
* `sforge/harness/score_rescale.py` sha256
  `98feb630390f217cb67e21315b5ca8a4f2eb6d1bb28cc9822152b3ed58be4b19`, l.110-114 `log_anchor`:
  `0 if raw <= 1 or anchor_raw <= 1 else clip(anchor_score*log(raw)/log(anchor_raw))`, clip to
  [0,100] (l.60-63); task anchor 14.155 -> 43 (`tasks/ffmpeg_swscale_reimplementation.json` l.31-33)
  -> `logAnchor`.

Abstractions: real arithmetic instead of IEEE doubles; `round(geo, 6)` (orig l.679) omitted;
the PSNR comparison is an opaque Boolean `outOk` (whether the candidate's last timed output
meets the threshold against the baseline's); timings are free parameters.
-/

namespace Ebv.Ffmpeg

open Real

noncomputable section

/-- Outcome of one timed workload. -/
structure Call where
  created : Bool   -- both contexts non-NULL and no exception (l.543-554)
  base : ℝ         -- baseline median time
  cand : ℝ         -- candidate median time
  baseRet : Int    -- first nonzero return code of the baseline's calls (0 if none)
  candRet : Int    -- same for the candidate
  outOk : Bool     -- candidate's last timed output meets the per-plane PSNR threshold

def eps : ℝ := 1 / 10 ^ 15

def ratio (c : Call) : ℝ := c.base / max c.cand eps

/-- Original l.543-557: return code and output ignored. -/
noncomputable def origSpeedup (c : Call) : ℝ := if c.created then ratio c else 0

/-- Fixed l.551-597. -/
noncomputable def fixedSpeedup (c : Call) : ℝ :=
  if c.created ∧ c.baseRet = 0 ∧ c.candRet = 0 ∧ c.outOk then ratio c else 0

/-- A call the fixed grader regards as verified. -/
def verified (c : Call) : Prop := c.created ∧ c.baseRet = 0 ∧ c.candRet = 0 ∧ c.outOk

noncomputable def safe (s : ℝ) : ℝ := max s eps

noncomputable def geo (ss : List ℝ) : ℝ :=
  exp ((ss.map (fun s => log (safe s))).sum / ss.length)

noncomputable def clip (v : ℝ) : ℝ := max 0 (min 100 v)

/-- score_rescale.py l.110-114. -/
noncomputable def logAnchor (a sc raw : ℝ) : ℝ :=
  if raw ≤ 1 ∨ a ≤ 1 then 0 else clip (sc * log raw / log a)

noncomputable def score (ss : List ℝ) : ℝ := logAnchor 14.155 43 (geo ss)

lemma eps_pos : (0 : ℝ) < eps := by unfold eps; positivity

lemma safe_pos (s : ℝ) : 0 < safe s := lt_of_lt_of_le eps_pos (le_max_right _ _)

/-! ## General facts about the scoring pipeline -/

lemma sum_log_safe (ss : List ℝ) :
    (ss.map (fun s => log (safe s))).sum = log (ss.map safe).prod := by
  induction ss with
  | nil => simp
  | cons s ss ih =>
    simp only [List.map_cons, List.sum_cons, List.prod_cons, ih]
    rw [log_mul (ne_of_gt (safe_pos s))]
    exact ne_of_gt (List.prod_pos (by intro x hx; simp at hx; obtain ⟨y, _, rfl⟩ := hx; exact safe_pos y))

lemma prod_safe_pos (ss : List ℝ) : 0 < (ss.map safe).prod :=
  List.prod_pos (by intro x hx; simp at hx; obtain ⟨y, _, rfl⟩ := hx; exact safe_pos y)

/-- The geometric mean exceeds 1 exactly when the product of the floored speedups does. -/
theorem geo_le_one_iff (ss : List ℝ) (hne : ss ≠ []) :
    geo ss ≤ 1 ↔ (ss.map safe).prod ≤ 1 := by
  have hn : (0 : ℝ) < ss.length := by
    have := List.length_pos_of_ne_nil hne; exact_mod_cast this
  unfold geo
  rw [sum_log_safe]
  have e1 : exp (log (ss.map safe).prod / ss.length) ≤ 1 ↔ log (ss.map safe).prod / ss.length ≤ 0 := by
    constructor
    · intro h; by_contra hc; push Not at hc; have := one_lt_exp_iff.mpr hc; linarith
    · intro h; calc exp _ ≤ exp 0 := exp_le_exp.mpr h
        _ = 1 := exp_zero
  rw [e1, div_nonpos_iff]
  constructor
  · rintro (⟨_, h⟩ | ⟨h, _⟩)
    · linarith
    · exact (log_nonpos_iff (le_of_lt (prod_safe_pos ss))).mp h
  · intro h; right; exact ⟨(log_nonpos_iff (le_of_lt (prod_safe_pos ss))).mpr h, le_of_lt hn⟩

/-- log_anchor gives 0 at or below raw 1 (score_rescale.py l.112-113). -/
theorem logAnchor_le_one (a sc raw : ℝ) (h : raw ≤ 1) : logAnchor a sc raw = 0 := by
  simp [logAnchor, h]

/-- ... and strictly positive credit above 1 (anchor 14.155 -> 43). -/
theorem score_pos_of_gt_one (r : ℝ) (h : 1 < r) : 0 < logAnchor 14.155 43 r := by
  have hr : ¬ (r ≤ 1 ∨ (14.155 : ℝ) ≤ 1) := by
    push Not; exact ⟨h, by norm_num⟩
  simp only [logAnchor, hr, ite_false, clip]
  have h1 : 0 < log r := log_pos h
  have h2 : 0 < log (14.155 : ℝ) := log_pos (by norm_num)
  have : 0 < 43 * log r / log 14.155 := by positivity
  exact lt_max_of_lt_right (lt_min (by norm_num) this)

lemma logAnchor_mono (r r' : ℝ) (h : r ≤ r') : logAnchor 14.155 43 r ≤ logAnchor 14.155 43 r' := by
  unfold logAnchor clip
  have ha : ¬ ((14.155 : ℝ) ≤ 1) := by norm_num
  by_cases h1 : r ≤ 1
  · simp only [h1, true_or, ite_true]
    split_ifs <;> simp
  · have h1' : ¬ r' ≤ 1 := by intro h'; exact h1 (le_trans h h')
    simp only [h1, h1', ha, or_false, ite_false]
    have hl : log r ≤ log r' := log_le_log (by linarith) h
    have h2 : 0 < log (14.155 : ℝ) := log_pos (by norm_num)
    have : 43 * log r / log 14.155 ≤ 43 * log r' / log 14.155 := by
      apply div_le_div_of_nonneg_right _ (le_of_lt h2); linarith
    exact max_le_max (le_refl _) (min_le_min (le_refl _) this)

/-- The geometric mean is monotone in each entry (through the 1e-15 floor). -/
theorem geo_mono_at (l₁ l₂ : List ℝ) (a b : ℝ) (h : safe a ≤ safe b) :
    geo (l₁ ++ a :: l₂) ≤ geo (l₁ ++ b :: l₂) := by
  unfold geo
  rw [exp_le_exp]
  have hlen : ((l₁ ++ a :: l₂).length : ℝ) = (l₁ ++ b :: l₂).length := by simp
  rw [hlen]
  apply div_le_div_of_nonneg_right _ (by positivity)
  simp only [List.map_append, List.map_cons, List.sum_append, List.sum_cons]
  have := log_le_log (safe_pos a) h
  linarith

/-! ## The fixed scoring -/

/-- A failing or unverified call gets speedup 0, i.e. the floor 1e-15 in the mean ... -/
theorem fixed_unverified_floor (c : Call) (h : ¬ verified c) : safe (fixedSpeedup c) = eps := by
  unfold fixedSpeedup verified at *
  simp only [h, ite_false]; unfold safe; exact max_eq_right (le_of_lt eps_pos)

/-- ... which is the least any entry can contribute. -/
lemma eps_le_safe (s : ℝ) : eps ≤ safe s := le_max_right _ _

/-- Main theorem (no credit). Under the fixed scoring, a submission in which some timed
workload fails (nonzero return, or output below threshold) scores no more than the same
submission with that workload replaced by any other outcome whatsoever, in particular a correct
but arbitrarily slow one: a failing call never adds credit. -/
theorem fixed_failing_never_helps (l₁ l₂ : List Call) (bad other : Call) (h : ¬ verified bad) :
    score ((l₁ ++ bad :: l₂).map fixedSpeedup) ≤ score ((l₁ ++ other :: l₂).map fixedSpeedup) := by
  unfold score
  apply logAnchor_mono
  simp only [List.map_append, List.map_cons]
  apply geo_mono_at
  rw [fixed_unverified_floor bad h]; exact eps_le_safe _

/-- Correct submissions are unchanged: if every timed call is verified, the fixed and the
original grader compute the same speedup list, hence the same raw value and score. -/
theorem fixed_eq_orig_of_verified (cs : List Call) (h : ∀ c ∈ cs, verified c) :
    cs.map fixedSpeedup = cs.map origSpeedup := by
  apply List.map_congr_left
  intro c hc
  have hv := h c hc
  unfold fixedSpeedup origSpeedup verified at *
  simp [hv]

/-- Counter-check: the original credits a failing call exactly as if it had succeeded; any
error return that finishes faster than the baseline earns a factor above 1. -/
theorem orig_ignores_failure (c : Call) (hc : c.created) :
    origSpeedup { c with candRet := -3, outOk := false } = ratio c := by
  simp [origSpeedup, ratio, hc]

/-! ## Recorded data (evidence/scripts/ffmpeg_swscale_reimplementation/results_local/*/reward.json)

`per_workload_speedups` as recorded by the original grader, in workload order (l.227-357):
yuv420p→rgb24 1080p, rgb24→yuv420p 1080p, rgb24→bgra 1080p, rgb24→nv12 1080p, rgba→rgb24 4K,
yuv420p→rgb24 4K→1080p, rgb24 1080p→4K, rgb24→yuv420p 1080p→360p, rgb24 1080p→360p nearest,
rgb24 720p→1080p bicubic. -/

/-- Variant 1 (returns -3 for RGBA→RGB24): workload 5 recorded as 16468.9989×
(case: "16,469×"). -/
def v1 : List ℝ :=
  [0.0352, 1.4055, 0.2405, 1.4921, 16468.9989, 1.0547, 0.4947, 0.2209, 4.465, 0.184]

/-- The same list with workload 5 scored as the fixed grader scores an error return. -/
def v1fixed : List ℝ :=
  [0.0352, 1.4055, 0.2405, 1.4921, 0, 1.0547, 0.4947, 0.2209, 4.465, 0.184]

/-- Original: product of floored speedups > 1, so raw > 1 (recorded raw 1.393783) and the
score is positive (recorded 5.39). -/
theorem v1_orig_prod : 1 < (v1.map safe).prod := by
  norm_num [v1, safe, eps, max_def]

theorem v1_orig_score_pos : 0 < score v1 := by
  apply score_pos_of_gt_one
  have h := (not_congr (geo_le_one_iff v1 (by simp [v1]))).mpr (not_le.mpr v1_orig_prod)
  exact lt_of_not_ge h

/-- Fixed: the same recorded timings with the error return scored 0 give raw ≤ 1, score 0. -/
theorem v1_fixed_prod : (v1fixed.map safe).prod ≤ 1 := by
  norm_num [v1fixed, safe, eps, max_def]

theorem v1_fixed_score_zero : score v1fixed = 0 :=
  logAnchor_le_one _ _ _ ((geo_le_one_iff v1fixed (by simp [v1fixed])).mpr v1_fixed_prod)

/-- Published fixed-grader raw values (case table): 0.000464, 0.000463, 0.000451 all score 0. -/
theorem published_fixed_raw_zero :
    logAnchor 14.155 43 0.000464 = 0 ∧ logAnchor 14.155 43 0.000463 = 0 ∧
    logAnchor 14.155 43 0.000451 = 0 :=
  ⟨logAnchor_le_one _ _ _ (by norm_num), logAnchor_le_one _ _ _ (by norm_num),
   logAnchor_le_one _ _ _ (by norm_num)⟩

/-- Too-strong claim refuted: the fixed scoring does NOT give every submission with a failing
call a score of 0. Nine verified workloads at 100× and one failing workload: product
100^9 · 1e-15 = 1000 > 1, so the score is positive. (The failing call itself still earns
nothing, by `fixed_failing_never_helps`.) -/
def fastButOneFails : List ℝ := [100, 100, 100, 100, 100, 100, 100, 100, 100, 0]

theorem not_always_zero : 0 < score fastButOneFails := by
  apply score_pos_of_gt_one
  have hp : 1 < (fastButOneFails.map safe).prod := by
    norm_num [fastButOneFails, safe, eps, max_def]
  exact lt_of_not_ge ((not_congr (geo_le_one_iff _ (by simp [fastButOneFails]))).mpr (not_le.mpr hp))

end

end Ebv.Ffmpeg

#print axioms Ebv.Ffmpeg.geo_le_one_iff
#print axioms Ebv.Ffmpeg.logAnchor_le_one
#print axioms Ebv.Ffmpeg.score_pos_of_gt_one
#print axioms Ebv.Ffmpeg.fixed_failing_never_helps
#print axioms Ebv.Ffmpeg.fixed_eq_orig_of_verified
#print axioms Ebv.Ffmpeg.orig_ignores_failure
#print axioms Ebv.Ffmpeg.v1_orig_score_pos
#print axioms Ebv.Ffmpeg.v1_fixed_score_zero
#print axioms Ebv.Ffmpeg.published_fixed_raw_zero
#print axioms Ebv.Ffmpeg.not_always_zero
