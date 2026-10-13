import Mathlib.Tactic.NormNum
import Mathlib.Tactic.Linarith
import Mathlib.Algebra.Order.Field.Rat

/-! # wireless_electricity_layout: a compile failure never changes a score out of 100

Claim. Under the task's `score_first` / `minimize` selection and its `piecewise_log_min`
rescale, adding a compile-failure entry (raw total 1e17) anywhere in a non-empty history
changes neither (a) the 0-100 score of the selected entry, nor (b) the maximum 0-100 score
over entries. It can change the raw `best_score` (counter-check 1), and the invariance
depends on the CE penalty being at or above the baseline anchor (counter-check 2).

Sources modelled (EdgeBench harness 6e4e5f4; hashes match `sforge/UPSTREAM.lock`):
* `sforge/harness/score_rescale.py` sha256 98feb630390f217cb67e21315b5ca8a4f2eb6d1bb28cc9822152b3ed58be4b19
  `rescale` below = lines 60-63 (`_clip`) and 173-194
  (`piecewise_log_min`).
* `sforge/harness/selection.py` (upstream) sha256 abb55b7b0466f73e4fab248dfed31ad89b1caec19b1a8117edcbf2429571cf0a.
  `step`/`selectScore` below = lines 45-48 (`_is_better_score`) and 83-103 (`_score_first`):
  scan in order, replace the incumbent iff `new < old`, skip `score is None`.
* `sforge/visualizer/scanner.py` (upstream) sha256 f124d3402dc036ba05195d92f0c281c76cf45977829dfdf24704b4edaafca866,
  lines 467-468: `best_score_0_100 = max(rescaled)`. `bestMax` below.
* `tasks/wireless_electricity_layout.json` sha256 050ab35f...0809: anchors (exact values of the
  JSON doubles) and `/tmp/eval_wirel.sh` (sha256 c670ff6d...): CE emits `TOTAL_SCORE 1e17`.

Abstractions. Raw scores are rationals (every JSON double is an exact rational; float
comparisons of these magnitudes are exact). `math.log` is replaced by an ARBITRARY function
`lg : ℚ → ℚ`: every theorem holds for all `lg`, so nothing depends on the logarithm.
Python returns NaN when a log denominator is 0; with these distinct anchors that branch is
unreachable for the real log. Entries with `score is None` and the history filter are
abstracted to the list of scores of completed submissions, in order. -/

namespace Ebv.Wireless

structure Spec where
  B : ℚ
  R30 : ℚ
  R1 : ℚ
  S : ℚ

/-- Exact rational values of the task JSON anchors. -/
def task : Spec :=
  ⟨26059066264593484, 2444746514528109, 362439546835871, 362439546835871 / 2⟩

/-- CE penalty from `eval_wirel.sh`: `TOTAL_SCORE 1e17`. -/
def ce : ℚ := 100000000000000000

/-- `_clip` (score_rescale.py 60-63), without the NaN case. -/
def clip (lo hi v : ℚ) : ℚ := max lo (min hi v)

/-- `piecewise_log_min` (score_rescale.py 173-194) with `math.log` replaced by `lg`. -/
def rescale (lg : ℚ → ℚ) (s : Spec) (raw : ℚ) : ℚ :=
  if raw ≤ 0 ∨ s.B ≤ 0 ∨ s.R30 ≤ 0 ∨ s.R1 ≤ 0 ∨ s.S ≤ 0 then 0          -- 175-176
  else if s.B ≤ raw then 0                                                 -- 177-178
  else if s.R30 ≤ raw then clip 0 20 (20 * lg (s.B / raw) / lg (s.B / s.R30))   -- 179-183
  else if s.R1 ≤ raw then clip 20 80 (20 + 60 * lg (s.R30 / raw) / lg (s.R30 / s.R1)) -- 184-188
  else if s.S ≤ raw then clip 80 100 (80 + 20 * lg (s.R1 / raw) / lg (s.R1 / s.S))   -- 189-193
  else 100                                                                 -- 194

/-- One iteration of `_score_first` (selection.py 89-96) on the incumbent best score. -/
def step (best : Option ℚ) (x : ℚ) : Option ℚ :=
  match best with
  | none => some x
  | some b => if x < b then some x else some b

/-- `_score_first(...)["best_score"]` for minimize (selection.py 83-103). -/
def selectScore (l : List ℚ) : Option ℚ := l.foldl step none

/-- The 0-100 score of the selected entry (run_evaluation / report of best_round);
`none` when nothing was selected. -/
def selectedNorm (lg : ℚ → ℚ) (s : Spec) (l : List ℚ) : Option ℚ :=
  (selectScore l).map (rescale lg s)

/-- `max(rescaled)` (scanner.py 467-468) as a fold with base 0; equals Python's `max` on a
non-empty list because every rescaled value is ≥ 0 (`rescale_nonneg`, `bestMax_attained`). -/
def bestMax (lg : ℚ → ℚ) (s : Spec) (l : List ℚ) : ℚ :=
  (l.map (rescale lg s)).foldr max 0

/-! ## Facts about the rescale read directly off the source -/

theorem rescale_zero_of_ge (lg : ℚ → ℚ) (s : Spec) (r : ℚ) (h : s.B ≤ r) :
    rescale lg s r = 0 := by
  unfold rescale
  split_ifs <;> rfl

theorem rescale_nonneg (lg : ℚ → ℚ) (s : Spec) (r : ℚ) : 0 ≤ rescale lg s r := by
  unfold rescale clip
  split_ifs
  all_goals first
    | exact le_refl _
    | norm_num

theorem task_ce_ge_baseline : task.B ≤ ce := by norm_num [task, ce]

/-! ## The selection scan returns a minimum element -/

theorem foldl_step_spec (l : List ℚ) :
    ∀ (acc : Option ℚ) (m : ℚ), l.foldl step acc = some m →
      (m ∈ l ∨ acc = some m) ∧ (∀ x ∈ l, m ≤ x) ∧ (∀ a, acc = some a → m ≤ a) := by
  induction l with
  | nil =>
    intro acc m h
    simp only [List.foldl_nil] at h
    subst h
    exact ⟨Or.inr rfl, by simp, fun a ha => by cases ha; exact le_refl _⟩
  | cons y ys ih =>
    intro acc m h
    simp only [List.foldl_cons] at h
    obtain ⟨hmem, hle, hacc⟩ := ih _ m h
    cases acc with
    | none =>
      simp only [step] at hmem hacc
      have hmy : m ≤ y := hacc y rfl
      refine ⟨?_, ?_, fun a ha => by cases ha⟩
      · rcases hmem with hm | hm
        · exact Or.inl (List.mem_cons_of_mem _ hm)
        · cases hm; exact Or.inl List.mem_cons_self
      · intro x hx
        rcases List.mem_cons.mp hx with rfl | hx
        · exact hmy
        · exact hle x hx
    | some b =>
      simp only [step] at hmem hacc
      by_cases hyb : y < b
      · simp only [hyb, ↓reduceIte] at hmem hacc
        have hmy : m ≤ y := hacc y rfl
        refine ⟨?_, ?_, fun a ha => ?_⟩
        · rcases hmem with hm | hm
          · exact Or.inl (List.mem_cons_of_mem _ hm)
          · cases hm; exact Or.inl List.mem_cons_self
        · intro x hx
          rcases List.mem_cons.mp hx with rfl | hx
          · exact hmy
          · exact hle x hx
        · cases ha; exact le_of_lt (lt_of_le_of_lt hmy hyb)
      · simp only [hyb, ↓reduceIte] at hmem hacc
        have hmb : m ≤ b := hacc b rfl
        refine ⟨?_, ?_, fun a ha => ?_⟩
        · rcases hmem with hm | hm
          · exact Or.inl (List.mem_cons_of_mem _ hm)
          · exact Or.inr hm
        · intro x hx
          rcases List.mem_cons.mp hx with rfl | hx
          · exact le_trans hmb (not_lt.mp hyb)
          · exact hle x hx
        · cases ha; exact hmb

theorem foldl_step_some (l : List ℚ) : ∀ a : ℚ, ∃ m, l.foldl step (some a) = some m := by
  induction l with
  | nil => intro a; exact ⟨a, rfl⟩
  | cons y ys ih =>
    intro a
    simp only [List.foldl_cons, step]
    split_ifs
    · exact ih y
    · exact ih a

theorem selectScore_spec (l : List ℚ) (m : ℚ) (h : selectScore l = some m) :
    m ∈ l ∧ ∀ x ∈ l, m ≤ x := by
  obtain ⟨hmem, hle, -⟩ := foldl_step_spec l none m h
  exact ⟨hmem.resolve_right (by simp), hle⟩

theorem selectScore_isSome (l : List ℚ) (h : l ≠ []) : ∃ m, selectScore l = some m := by
  cases l with
  | nil => exact absurd rfl h
  | cons y ys =>
    simp only [selectScore, List.foldl_cons, step]
    exact foldl_step_some ys y

/-! ## Main theorems -/

/-- (a) Inserting any entry with raw ≥ baseline (in particular the CE entry) at any position
of a non-empty history leaves the 0-100 score of the selected entry unchanged. -/
theorem selected_norm_invariant (lg : ℚ → ℚ) (s : Spec) (c : ℚ) (hc : s.B ≤ c)
    (l1 l2 : List ℚ) (hne : l1 ++ l2 ≠ []) :
    selectedNorm lg s (l1 ++ c :: l2) = selectedNorm lg s (l1 ++ l2) := by
  obtain ⟨m, hm⟩ := selectScore_isSome (l1 ++ l2) hne
  obtain ⟨m', hm'⟩ := selectScore_isSome (l1 ++ c :: l2) (by simp)
  obtain ⟨hmem, hle⟩ := selectScore_spec _ m hm
  obtain ⟨hmem', hle'⟩ := selectScore_spec _ m' hm'
  simp only [selectedNorm, hm, hm', Option.map_some, Option.some.injEq]
  have hm'c : m' ≤ c := hle' c (by simp)
  have hm'm : m' ≤ m := hle' m (by simp at hmem ⊢; tauto)
  -- m' is c or an element of l1 ++ l2
  have hcase : m' = c ∨ m' ∈ l1 ++ l2 := by
    simp only [List.mem_append, List.mem_cons] at hmem' ⊢; tauto
  by_cases hlt : m < c
  · rcases hcase with h | h
    · exact absurd (lt_of_le_of_lt (h ▸ hm'm) hlt) (lt_irrefl c)
    · have : m ≤ m' := hle m' h
      rw [le_antisymm hm'm this]
  · have hcm : c ≤ m := not_lt.mp hlt
    have hBm : s.B ≤ m := le_trans hc hcm
    have hBm' : s.B ≤ m' := by
      rcases hcase with h | h
      · rw [h]; exact hc
      · exact le_trans hBm (hle m' h)
    rw [rescale_zero_of_ge lg s m hBm, rescale_zero_of_ge lg s m' hBm']

theorem foldr_max_nonneg (l : List ℚ) : 0 ≤ l.foldr max 0 := by
  induction l with
  | nil => exact le_refl _
  | cons x xs ih => simp only [List.foldr_cons]; exact le_trans ih (le_max_right _ _)

/-- (b) The order-independent `max(score_0_100)` consumer is unchanged too. -/
theorem bestMax_invariant (lg : ℚ → ℚ) (s : Spec) (c : ℚ) (hc : s.B ≤ c) (l1 l2 : List ℚ) :
    bestMax lg s (l1 ++ c :: l2) = bestMax lg s (l1 ++ l2) := by
  simp only [bestMax, List.map_append, List.map_cons, List.foldr_append, List.foldr_cons,
    rescale_zero_of_ge lg s c hc]
  rw [max_eq_right (foldr_max_nonneg _)]

/-- `bestMax` is Python's `max` on a non-empty list of rescaled values: it is attained and is
an upper bound. -/
theorem bestMax_attained (lg : ℚ → ℚ) (s : Spec) (l : List ℚ) (h : l ≠ []) :
    (∃ x ∈ l, rescale lg s x = bestMax lg s l) ∧ ∀ x ∈ l, rescale lg s x ≤ bestMax lg s l := by
  induction l with
  | nil => exact absurd rfl h
  | cons y ys ih =>
    simp only [bestMax, List.map_cons, List.foldr_cons] at ih ⊢
    constructor
    · by_cases hys : ys = []
      · subst hys
        refine ⟨y, by simp, ?_⟩
        simp [max_eq_left (rescale_nonneg lg s y)]
      · obtain ⟨⟨x, hx, hxe⟩, -⟩ := ih hys
        rcases le_total (rescale lg s y) ((ys.map (rescale lg s)).foldr max 0) with hle | hle
        · exact ⟨x, List.mem_cons_of_mem _ hx, by rw [max_eq_right hle, hxe]⟩
        · exact ⟨y, List.mem_cons_self, by rw [max_eq_left hle]⟩
    · intro x hx
      rcases List.mem_cons.mp hx with rfl | hx
      · exact le_max_left _ _
      · by_cases hys : ys = []
        · subst hys; simp at hx
        · exact le_trans ((ih hys).2 x hx) (le_max_right _ _)

/-- Instantiation for the task: the CE entry (1e17) never changes either 0-100 consumer. -/
theorem task_ce_invariant (lg : ℚ → ℚ) (l1 l2 : List ℚ) (hne : l1 ++ l2 ≠ []) :
    selectedNorm lg task (l1 ++ ce :: l2) = selectedNorm lg task (l1 ++ l2) ∧
    bestMax lg task (l1 ++ ce :: l2) = bestMax lg task (l1 ++ l2) :=
  ⟨selected_norm_invariant lg task ce task_ce_ge_baseline l1 l2 hne,
   bestMax_invariant lg task ce task_ce_ge_baseline l1 l2⟩

/-- Empty history: without CE nothing is selected (`none`); with only CE the selected score is 0. -/
theorem task_ce_only (lg : ℚ → ℚ) : selectedNorm lg task [ce] = some 0 := by
  simp only [selectedNorm, selectScore, List.foldl, step, Option.map_some]
  rw [rescale_zero_of_ge lg task ce task_ce_ge_baseline]

/-! ## Differential check against the saved logs (`evidence/scripts/.../observed/`)
baseline raw 663100735542396309 (float 663100735542396288), ce 1e17,
re_some 1356919142089112260 (float 1356919142089112320); the review recorded
selected=ce in each history and norm=0.0 for all three. -/

def baselineRaw : ℚ := 663100735542396288
def reSomeRaw : ℚ := 1356919142089112320

theorem diff_select_baseline_ce : selectScore [baselineRaw, ce] = some ce := by
  norm_num [selectScore, step, baselineRaw, ce]
theorem diff_select_ce_baseline : selectScore [ce, baselineRaw] = some ce := by
  norm_num [selectScore, step, baselineRaw, ce]
theorem diff_select_three : selectScore [baselineRaw, reSomeRaw, ce] = some ce := by
  norm_num [selectScore, step, baselineRaw, reSomeRaw, ce]
theorem diff_norms_zero (lg : ℚ → ℚ) :
    rescale lg task baselineRaw = 0 ∧ rescale lg task ce = 0 ∧ rescale lg task reSomeRaw = 0 :=
  ⟨rescale_zero_of_ge lg task _ (by norm_num [task, baselineRaw]),
   rescale_zero_of_ge lg task _ task_ce_ge_baseline,
   rescale_zero_of_ge lg task _ (by norm_num [task, reSomeRaw])⟩

/-! ## Counter-checks (must come out the other way) -/

/-- 1. The raw `best_score` DOES change: the defect is real in raw units. -/
theorem counter_raw_changes : selectScore [baselineRaw] ≠ selectScore [baselineRaw, ce] := by
  norm_num [selectScore, step, baselineRaw, ce]

/-- 2. The hypothesis `B ≤ c` is needed: a hypothetical CE penalty of 1e15 (below baseline,
inside the rank1..rank30 band) would raise the selected 0-100 score from 0 to at least 20,
for every `lg`. -/
theorem counter_low_penalty (lg : ℚ → ℚ) :
    selectedNorm lg task [baselineRaw] = some 0 ∧
    ∃ v, selectedNorm lg task [baselineRaw, 1000000000000000] = some v ∧ 20 ≤ v := by
  constructor
  · simp only [selectedNorm, selectScore, List.foldl, step, Option.map_some]
    rw [rescale_zero_of_ge lg task _ (by norm_num [task, baselineRaw])]
  · have hsel : selectScore [baselineRaw, 1000000000000000] = some 1000000000000000 := by
      norm_num [selectScore, step, baselineRaw]
    refine ⟨rescale lg task 1000000000000000, by simp [selectedNorm, hsel], ?_⟩
    unfold rescale clip
    have h1 : ¬ ((1000000000000000 : ℚ) ≤ 0 ∨ task.B ≤ 0 ∨ task.R30 ≤ 0 ∨ task.R1 ≤ 0 ∨
        task.S ≤ 0) := by norm_num [task]
    have h2 : ¬ (task.B ≤ (1000000000000000 : ℚ)) := by norm_num [task]
    have h3 : ¬ (task.R30 ≤ (1000000000000000 : ℚ)) := by norm_num [task]
    have h4 : task.R1 ≤ (1000000000000000 : ℚ) := by norm_num [task]
    simp only [h1, h2, h3, h4, ↓reduceIte]
    exact le_max_left _ _

end Ebv.Wireless

#print axioms Ebv.Wireless.selected_norm_invariant
#print axioms Ebv.Wireless.bestMax_invariant
#print axioms Ebv.Wireless.bestMax_attained
#print axioms Ebv.Wireless.task_ce_invariant
#print axioms Ebv.Wireless.task_ce_only
#print axioms Ebv.Wireless.diff_select_three
#print axioms Ebv.Wireless.diff_norms_zero
#print axioms Ebv.Wireless.counter_raw_changes
#print axioms Ebv.Wireless.counter_low_penalty
