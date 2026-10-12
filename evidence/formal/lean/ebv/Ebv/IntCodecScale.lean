/-
EdgeBench Verified -- integer_compression_codec: formula maximum, fixed score scale and the
regraded Opus 5.5 composite (exact rationals).

Sources modelled
  * Fixed grader `runner_judge.py` (judge image path /home/workspace/integer-compression-codec/
    runner_judge.py after repair; local copy .internal/repairs/integer_compression_codec-v2/files/
    runner_judge.py), sha256 f205adb8911b3513aa4723dd89c34048ec43317cb78f09b5bbf9fe5971e7e152.
      DATASETS weights docids 2.0, ts_sec 1.5, ts_ns 1.5, temp/grid/zipf/rand/sparse 1.0   [25-34]
      compute_total_score                                                                  [115-128]
        failed dataset (roundtrip / error) -> score 0                                      [119-121]
        bpi = encoded_bytes*8/max(n,1)                                                     [123]
        comp_ratio  = min(b.bpi / max(bpi,1e-9), 8.0)                                      [124]
        speed_ratio = min(decode_gbps / max(b.decode_gbps,1e-9), 40.0)                    [125]
        score = comp_ratio*speed_ratio; total = Σ w·score / Σ w                            [126-128]
    The formula and weights are unchanged from the original grader (repair.patch only changes
    the source of b.bpi and b.decode_gbps).
  * Harness rescale `sforge/harness/score_rescale.py` (sha256 98feb630...4b19): `linear`
    [80-84], `_clip` [60-63]. Original task JSON: linear 0..100; fixed task.json.in: linear 1..320.
  * Regrade log evidence/runs/opus55-regrade/result/out/logs/ic-agent-20-v2.raw.txt
    (structured result: score 160.76388698076738 and the eight per-dataset entries).

Model abstractions: exact rationals instead of doubles; `max(x,1e-9)` guards are dropped
(all measured denominators in the log are far above 1e-9); ratios are assumed ≥ 0 (they are
quotients of non-negative measurements).
-/
import Mathlib.Algebra.Order.Field.Rat
import Mathlib.Tactic.NormNum
import Mathlib.Tactic.Linarith
import Mathlib.Tactic.Ring

namespace Ebv.IntCodec

def clip (lo hi v : ℚ) : ℚ := max lo (min hi v)
def linear (lower upper raw : ℚ) : ℚ := clip 0 100 (100 * (raw - lower) / (upper - lower))

/-- Per-dataset score [124-126]. -/
def S (c s : ℚ) : ℚ := min c 8 * min s 40

/-- Weighted composite [115-128] with the weights of DATASETS [25-34]; Σ w = 10. -/
def composite (d1 d2 d3 d4 d5 d6 d7 d8 : ℚ) : ℚ :=
  (2 * d1 + 3/2 * d2 + 3/2 * d3 + d4 + d5 + d6 + d7 + d8) / 10

theorem S_nonneg (c s : ℚ) (hc : 0 ≤ c) (hs : 0 ≤ s) : 0 ≤ S c s :=
  mul_nonneg (le_min hc (by norm_num)) (le_min hs (by norm_num))

theorem S_le (c s : ℚ) (hc : 0 ≤ c) (hs : 0 ≤ s) : S c s ≤ 320 := by
  unfold S
  have h1 : min c 8 ≤ 8 := min_le_right _ _
  have h2 : min s 40 ≤ 40 := min_le_right _ _
  have h3 : 0 ≤ min c 8 := le_min hc (by norm_num)
  have h4 : 0 ≤ min s 40 := le_min hs (by norm_num)
  nlinarith

/-- S = 320 exactly when both caps bind. -/
theorem S_eq_iff (c s : ℚ) (hc : 0 ≤ c) (hs : 0 ≤ s) : S c s = 320 ↔ (8 ≤ c ∧ 40 ≤ s) := by
  constructor
  · intro h
    unfold S at h
    have h1 : min c 8 ≤ 8 := min_le_right _ _
    have h2 : min s 40 ≤ 40 := min_le_right _ _
    have h3 : 0 ≤ min c 8 := le_min hc (by norm_num)
    have h4 : 0 ≤ min s 40 := le_min hs (by norm_num)
    have e1 : min c 8 = 8 := by nlinarith
    have e2 : min s 40 = 40 := by nlinarith
    exact ⟨by rw [min_eq_iff] at e1; rcases e1 with h | h <;> linarith [h.1, h.2],
           by rw [min_eq_iff] at e2; rcases e2 with h | h <;> linarith [h.1, h.2]⟩
  · rintro ⟨h1, h2⟩
    unfold S; rw [min_eq_right h1, min_eq_right h2]; norm_num

/-- Composite ≤ 320 whenever every per-dataset score lies in [0, 320] (a failed dataset is 0). -/
theorem composite_le (d1 d2 d3 d4 d5 d6 d7 d8 : ℚ)
    (h1 : d1 ≤ 320) (h2 : d2 ≤ 320) (h3 : d3 ≤ 320) (h4 : d4 ≤ 320)
    (h5 : d5 ≤ 320) (h6 : d6 ≤ 320) (h7 : d7 ≤ 320) (h8 : d8 ≤ 320) :
    composite d1 d2 d3 d4 d5 d6 d7 d8 ≤ 320 := by
  unfold composite; rw [div_le_iff₀ (by norm_num)]; linarith

/-- Composite = 320 forces every dataset to 320, hence (S_eq_iff) every dataset at both caps;
a failed dataset (score 0) makes 320 impossible. -/
theorem composite_eq_320 (d1 d2 d3 d4 d5 d6 d7 d8 : ℚ)
    (h1 : d1 ≤ 320) (h2 : d2 ≤ 320) (h3 : d3 ≤ 320) (h4 : d4 ≤ 320)
    (h5 : d5 ≤ 320) (h6 : d6 ≤ 320) (h7 : d7 ≤ 320) (h8 : d8 ≤ 320)
    (h : composite d1 d2 d3 d4 d5 d6 d7 d8 = 320) :
    d1 = 320 ∧ d2 = 320 ∧ d3 = 320 ∧ d4 = 320 ∧ d5 = 320 ∧ d6 = 320 ∧ d7 = 320 ∧ d8 = 320 := by
  unfold composite at h
  rw [div_eq_iff (by norm_num)] at h
  refine ⟨?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_⟩ <;> linarith

theorem composite_all_caps : composite 320 320 320 320 320 320 320 320 = 320 := by
  norm_num [composite]

/-- Fixed scale linear(1, 320): starter (documented 1.0) -> 0, formula maximum -> 100. -/
def fixedScale (x : ℚ) : ℚ := linear 1 320 x
def origScale (x : ℚ) : ℚ := linear 0 100 x

theorem fixed_one : fixedScale 1 = 0 := by norm_num [fixedScale, linear, clip]
theorem fixed_max : fixedScale 320 = 100 := by norm_num [fixedScale, linear, clip]

/-- On [1, 320] the fixed scale never clips: it is exactly 100(x-1)/319. -/
theorem fixed_no_clip (x : ℚ) (h1 : 1 ≤ x) (h2 : x ≤ 320) :
    fixedScale x = 100 * (x - 1) / 319 := by
  unfold fixedScale linear clip
  have hlo : (0 : ℚ) ≤ 100 * (x - 1) / (320 - 1) := by apply div_nonneg <;> linarith
  have hhi : 100 * (x - 1) / (320 - 1) ≤ 100 := by rw [div_le_iff₀ (by norm_num)]; linarith
  rw [min_eq_right hhi, max_eq_right hlo]; norm_num

/-! ## Regraded Opus 5.5 best submission (ic-agent-20-v2.raw.txt) -/

/-- The eight printed per-dataset scores, in DATASETS order. -/
def pDocids : ℚ := 229.66897961360772
def pTsSec  : ℚ := 320.0
def pTsNs   : ℚ := 130.4664558248411
def pTemp   : ℚ := 22.191852544477758
def pGrid   : ℚ := 49.3499156135183
def pZipf   : ℚ := 46.708811786995724
def pRand   : ℚ := 49.350176309969676
def pSparse : ℚ := 305.0004705882353
/-- Printed composite. -/
def pComposite : ℚ := 160.76388698076738

def regrade : ℚ := composite pDocids pTsSec pTsNs pTemp pGrid pZipf pRand pSparse

/-- Exact weighted mean of the printed per-dataset scores. -/
theorem regrade_exact : regrade = 200954858725959231 / 1250000000000000 := by
  norm_num [regrade, composite, pDocids, pTsSec, pTsNs, pTemp, pGrid, pZipf, pRand, pSparse]

/-- It agrees with the printed composite to within 5e-15 (double rounding). -/
theorem regrade_matches_print : |regrade - pComposite| < 5 / 10 ^ 15 := by
  rw [regrade_exact, abs_lt]; constructor <;> norm_num [pComposite]

/-- Fixed-scale value of the printed composite: exactly 7988194349038369/159500000000000
≈ 50.0827231914631, and it lies in [50.0827, 50.0828). -/
theorem regrade_fixed :
    fixedScale pComposite = 7988194349038369 / 159500000000000 ∧
    (500827 : ℚ) / 10000 ≤ 7988194349038369 / 159500000000000 ∧
    (7988194349038369 : ℚ) / 159500000000000 < 500828 / 10000 := by
  refine ⟨?_, by norm_num, by norm_num⟩
  rw [fixed_no_clip _ (by norm_num [pComposite]) (by norm_num [pComposite])]
  norm_num [pComposite]

/-- Differential check of two per-dataset entries against the raw fields of the same log
(encoded_bytes, n, decode_gbps for submission and measured starter): ts_sec is at both caps
(320) and sparse is at the compression cap with speed 32.4063/0.85. -/
def ratioC (bBytes sBytes n : ℚ) : ℚ := (bBytes * 8 / n) / (sBytes * 8 / n)

theorem tsSec_from_fields :
    S (ratioC 250000004 663958 50000000) (50.2767 / 0.8477) = pTsSec := by
  rw [show pTsSec = 320 by norm_num [pTsSec]]
  rw [S_eq_iff _ _ (by norm_num [ratioC]) (by norm_num)]
  constructor <;> norm_num [ratioC]

theorem sparse_from_fields :
    |S (ratioC 241176008 28376092 50000000) (32.4063 / 0.85) - pSparse| < 1 / 10 ^ 12 := by
  have h : S (ratioC 241176008 28376092 50000000) (32.4063 / 0.85) = 8 * (32.4063 / 0.85) := by
    unfold S ratioC
    rw [min_eq_right (by norm_num), min_eq_left (by norm_num)]
  rw [h, abs_lt]; constructor <;> norm_num [pSparse]

/-- Other published fixed-scale values (case page and repair README): starter raw 0.9786 and
1.0155 -> 0.00; honest codec 6.7024 -> 1.79 and 6.9708 -> 1.87; earlier agent submission
114.19 -> 35.48 (each as a half-open interval of width 0.01 around the shown value). -/
theorem published_other :
    fixedScale 0.9786 = 0 ∧
    fixedScale 1.0155 < 5 / 1000 ∧
    (1785 : ℚ) / 1000 ≤ fixedScale 6.7024 ∧ fixedScale 6.7024 < 1795 / 1000 ∧
    (1865 : ℚ) / 1000 ≤ fixedScale 6.9708 ∧ fixedScale 6.9708 < 1875 / 1000 ∧
    (35475 : ℚ) / 1000 ≤ fixedScale 114.19 ∧ fixedScale 114.19 < 35485 / 1000 := by
  refine ⟨by norm_num [fixedScale, linear, clip], ?_, ?_, ?_, ?_, ?_, ?_, ?_⟩ <;>
    norm_num [fixed_no_clip, fixedScale, linear, clip]

/-! ## Counter-checks -/

/-- The original scale linear(0, 100) clips the regraded composite to 100. -/
theorem counter_orig_clips : origScale pComposite = 100 := by
  norm_num [origScale, linear, clip, pComposite]

/-- …and it would also clip the earlier submission (raw 114.19), so the two tie at 100. -/
theorem counter_orig_ties : origScale pComposite = origScale 114.19 := by
  norm_num [origScale, linear, clip, pComposite]

/-- A too-strong bound is false: the composite can reach 320 (> 319). -/
theorem counter_bound_319 : ¬ (∀ d : ℚ, d ≤ 320 → composite d d d d d d d d ≤ 319) := by
  intro h; have := h 320 le_rfl; norm_num [composite] at this

/-- One dataset just below its compression cap prevents 320. -/
theorem counter_one_below_cap : S (799/100) 40 < 320 := by norm_num [S]

end Ebv.IntCodec

#print axioms Ebv.IntCodec.S_le
#print axioms Ebv.IntCodec.S_eq_iff
#print axioms Ebv.IntCodec.composite_le
#print axioms Ebv.IntCodec.composite_eq_320
#print axioms Ebv.IntCodec.composite_all_caps
#print axioms Ebv.IntCodec.fixed_one
#print axioms Ebv.IntCodec.fixed_max
#print axioms Ebv.IntCodec.fixed_no_clip
#print axioms Ebv.IntCodec.regrade_exact
#print axioms Ebv.IntCodec.regrade_matches_print
#print axioms Ebv.IntCodec.regrade_fixed
#print axioms Ebv.IntCodec.tsSec_from_fields
#print axioms Ebv.IntCodec.sparse_from_fields
#print axioms Ebv.IntCodec.published_other
#print axioms Ebv.IntCodec.counter_orig_clips
#print axioms Ebv.IntCodec.counter_orig_ties
#print axioms Ebv.IntCodec.counter_bound_319
#print axioms Ebv.IntCodec.counter_one_below_cap
