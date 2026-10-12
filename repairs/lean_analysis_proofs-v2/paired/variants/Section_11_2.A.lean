import Mathlib.Tactic
import Analysis.Section_11_1

/-!
# Analysis I, Section 11.2: Piecewise constant functions

I have attempted to make the translation as faithful a paraphrasing as possible of the original
text. When there is a choice between a more idiomatic Lean solution and a more faithful
translation, I have generally chosen the latter. In particular, there will be places where the
Lean code could be "golfed" to be more elegant and idiomatic, but I have consciously avoided
doing so.

Main constructions and results of this section:
- Piecewise constant functions.
- The piecewise constant integral.

-/

namespace Chapter11
open BoundedInterval

/-- Definition 11.2.1 -/
abbrev Constant {X Y:Type} (f: X → Y) : Prop := ∃ c, ∀ x, f x = c

open Classical in
noncomputable abbrev constant_value {X Y:Type} [hY: Nonempty Y] (f:X → Y) : Y :=
  if h: Constant f then h.choose else hY.some

theorem Constant.const_eq {X Y:Type} {f:X → Y} [hX: Nonempty X] [Nonempty Y] {c:Y} (h: ∀ x, f x = c) :
  constant_value f = c := by
  sorry

abbrev ConstantOn (f: ℝ → ℝ) (X: Set ℝ) : Prop := Constant (fun x : X ↦ f ↑x)

noncomputable abbrev constant_value_on (f:ℝ → ℝ) (X: Set ℝ) : ℝ := constant_value (fun x : X ↦ f ↑x)

theorem ConstantOn.const_eq {f:ℝ → ℝ} {X: Set ℝ} (hX: X.Nonempty) {c:ℝ} (h: ∀ x ∈ X, f x = c) :
  constant_value_on f X = c := by
  haveI := hX.to_subtype
  exact Constant.const_eq (fun x => h x x.2)

theorem ConstantOn.congr' {f g: ℝ → ℝ} {X: Set ℝ} (hf: ConstantOn f X) (h: ∀ x ∈ X, f x = g x) : ConstantOn g X := by
  sorry

/-- Definition 11.2.3 (Piecewise constant functions I) -/
abbrev PiecewiseConstantWith (f:ℝ → ℝ) {I: BoundedInterval} (P: Partition I) : Prop := ∀ J ∈ P, ConstantOn f (J:Set ℝ)

theorem PiecewiseConstantWith.def (f:ℝ → ℝ) {I: BoundedInterval} {P: Partition I} :
  PiecewiseConstantWith f P ↔ ∀ J ∈ P, ∃ c, ∀ x ∈ J, f x = c := by
  sorry

/-- Definition 11.2.5 (Piecewise constant functions I) -/
abbrev PiecewiseConstantOn (f:ℝ → ℝ) (I: BoundedInterval) : Prop := ∃ P : Partition I, PiecewiseConstantWith f P

theorem PiecewiseConstantOn.def (f:ℝ → ℝ) (I: BoundedInterval):
  PiecewiseConstantOn f I ↔ ∃ P : Partition I, ∀ J ∈ P, ConstantOn f (J:Set ℝ) := by
  sorry

/-- Example 11.2.4 / Example 11.2.6 -/
noncomputable abbrev f_11_2_4 : ℝ → ℝ := fun x ↦
  if x < 1 then 0 else  -- junk value
    if x < 3 then 7 else
      if x = 3 then 4 else
        if x < 6 then 5 else
          if x = 6 then 2 else
            0 -- junk value

example : PiecewiseConstantOn f_11_2_4 (Icc 1 6) := by
  sorry

example : PiecewiseConstantOn f_11_2_4 (Icc 1 6) := by
  sorry

/-- Lemma 11.2.7 / Exercise 11.2.1 -/
theorem PiecewiseConstantWith.mono {f:ℝ → ℝ} {I: BoundedInterval} {P P': Partition I} (hPP': P ≤ P')
  (hP: PiecewiseConstantWith f P) : PiecewiseConstantWith f P' := by
  sorry

theorem ebv_toSet_ordConnected (I : BoundedInterval) : (I : Set ℝ).OrdConnected := by
  cases I with
  | Ioo a b => exact Set.ordConnected_Ioo
  | Icc a b => exact Set.ordConnected_Icc
  | Ioc a b => exact Set.ordConnected_Ioc
  | Ico a b => exact Set.ordConnected_Ico

theorem ebv_toSet_sub_Icc (I : BoundedInterval) : (I : Set ℝ) ⊆ Set.Icc I.a I.b := by
  cases I with
  | Ioo a b => exact Set.Ioo_subset_Icc_self
  | Icc a b => exact subset_rfl
  | Ioc a b => exact Set.Ioc_subset_Icc_self
  | Ico a b => exact Set.Ico_subset_Icc_self

theorem ebv_inter (I J : BoundedInterval) : ∃ K : BoundedInterval, (K : Set ℝ) = (I : Set ℝ) ∩ (J : Set ℝ) := by
  set S := (I : Set ℝ) ∩ (J : Set ℝ) with hSdef
  have hS : S.OrdConnected := (ebv_toSet_ordConnected I).inter (ebv_toSet_ordConnected J)
  have hsub : S ⊆ Set.Icc I.a I.b := Set.inter_subset_left.trans (ebv_toSet_sub_Icc I)
  have hA : BddAbove S := (bddAbove_Icc).mono hsub
  have hB : BddBelow S := (bddBelow_Icc).mono hsub
  have hm := hS.isPreconnected.mem_intervals
  simp only [Set.mem_insert_iff, Set.mem_singleton_iff] at hm
  rcases hm with h | h | h | h | h | h | h | h | h | h
  · exact ⟨Icc (sInf S) (sSup S), h.symm⟩
  · exact ⟨Ico (sInf S) (sSup S), h.symm⟩
  · exact ⟨Ioc (sInf S) (sSup S), h.symm⟩
  · exact ⟨Ioo (sInf S) (sSup S), h.symm⟩
  · exact absurd (h ▸ hA) (not_bddAbove_Ici _)
  · exact absurd (h ▸ hA) (not_bddAbove_Ioi _)
  · exact absurd (h ▸ hB) (not_bddBelow_Iic _)
  · exact absurd (h ▸ hB) (not_bddBelow_Iio _)
  · exact absurd (h ▸ hA) not_bddAbove_univ
  · exact ⟨Ioo 0 0, by rw [h]; exact Set.Ioo_self 0⟩

/-- Lemma 11.2.8 / Exercise 11.2.2.  I believe the hypothesis that `g` does not vanish is not needed. -/
theorem PiecewiseConstantOn.div {f g: ℝ → ℝ} {I: BoundedInterval}
  (hf: PiecewiseConstantOn f I) (hg: PiecewiseConstantOn g I) : PiecewiseConstantOn (f / g) I := by
  obtain ⟨P, hP⟩ := hf
  obtain ⟨Q, hQ⟩ := hg
  choose ι hι using ebv_inter
  refine ⟨{ intervals := Finset.image₂ ι P.intervals Q.intervals
            exists_unique := ?_
            contains := ?_ }, ?_⟩
  · intro x hx
    obtain ⟨J, ⟨hJ, hxJ⟩, huJ⟩ := P.exists_unique x hx
    obtain ⟨K, ⟨hK, hxK⟩, huK⟩ := Q.exists_unique x hx
    refine ⟨ι J K, ⟨Finset.mem_image₂_of_mem hJ hK, ?_⟩, ?_⟩
    · show x ∈ (ι J K : Set ℝ)
      rw [hι]; exact ⟨hxJ, hxK⟩
    · rintro L ⟨hL, hxL⟩
      obtain ⟨J', hJ', K', hK', rfl⟩ := Finset.mem_image₂.mp hL
      have hx' : x ∈ (ι J' K' : Set ℝ) := hxL
      rw [hι] at hx'
      rw [huJ J' ⟨hJ', hx'.1⟩, huK K' ⟨hK', hx'.2⟩]
  · intro L hL
    obtain ⟨J, hJ, K, hK, rfl⟩ := Finset.mem_image₂.mp hL
    intro x hx
    have hx' : x ∈ (ι J K : Set ℝ) := hx
    rw [hι] at hx'
    exact P.contains J hJ x hx'.1
  · intro L hL
    obtain ⟨J, hJ, K, hK, rfl⟩ := Finset.mem_image₂.mp hL
    obtain ⟨c, hc⟩ := hP J hJ
    obtain ⟨d, hd⟩ := hQ K hK
    refine ⟨c / d, fun ⟨v, hv⟩ => ?_⟩
    have hy : v ∈ (J : Set ℝ) ∩ (K : Set ℝ) := by rw [← hι]; exact hv
    have h1 : f v = c := hc ⟨v, hy.1⟩
    have h2 : g v = d := hd ⟨v, hy.2⟩
    show f v / g v = c / d
    rw [h1, h2]

/-- Definition 11.2.9 (Piecewise constant integral I)-/
noncomputable abbrev PiecewiseConstantWith.integ (f:ℝ → ℝ) {I: BoundedInterval} (P: Partition I)  :
  ℝ := ∑ J ∈ P.intervals, constant_value_on f (J:Set ℝ) * |J|ₗ

/-- Example 11.2.12 -/
noncomputable abbrev f_11_2_12 : ℝ → ℝ := fun x ↦
    if x < 3 then 2 else
      if x = 3 then 4 else
        6

noncomputable abbrev P_11_2_12 : Partition (Icc 1 4) :=
  ((⊥: Partition (Ico 1 3)).join (⊥ : Partition (Icc 3 3))
  (join_Ico_Icc (by norm_num) (by norm_num) )).join
  (⊥: Partition (Ioc 3 4))
  (join_Icc_Ioc (by norm_num) (by norm_num))

example : PiecewiseConstantWith f_11_2_12 P_11_2_12 := by
  sorry

example : PiecewiseConstantWith.integ f_11_2_12 P_11_2_12 = 10 := by
  sorry

noncomputable abbrev P_11_2_12' : Partition (Icc 1 4) :=
  ((((⊥: Partition (Ico 1 2)).join (⊥ : Partition (Ico 2 3))
  (join_Ico_Ico (by norm_num) (by norm_num) )).join
  (⊥: Partition (Icc 3 3))
  (join_Ico_Icc (by norm_num) (by norm_num))).join
  (⊥: Partition (Ioc 3 4))
  (join_Icc_Ioc (by norm_num) (by norm_num))).add_empty

example : PiecewiseConstantWith f_11_2_12 P_11_2_12' := by
  sorry

example : PiecewiseConstantWith.integ f_11_2_12 P_11_2_12' = 10 := by
  sorry

open Classical in
/-- Definition 11.2.14 (Piecewise constant integral II)  -/
noncomputable abbrev PiecewiseConstantOn.integ (f:ℝ → ℝ) (I: BoundedInterval) :
  ℝ := if h: PiecewiseConstantOn f I then PiecewiseConstantWith.integ f h.choose else 0

noncomputable abbrev PiecewiseConstantOn.integ' {f:ℝ → ℝ} {I: BoundedInterval} (_:PiecewiseConstantOn f I) := integ f I

/-- Example 11.2.15 -/
example : PiecewiseConstantOn.integ f_11_2_4 (Icc 1 6) = 10 := by
  sorry

/-- Theorem 11.2.16 (d) (Laws of integration) / Exercise 11.2.4 -/
theorem PiecewiseConstantOn.integ_of_nonneg {f: ℝ → ℝ} {I: BoundedInterval} (h: ∀ x ∈ I, 0 ≤ f x)
  (hf: PiecewiseConstantOn f I) :
  0 ≤ integ f I := by
  sorry

open Classical in
/-- Theorem 11.2.16 (g) (Laws of integration) / Exercise 11.2.4 -/
theorem PiecewiseConstantOn.of_extend {I J: BoundedInterval} (hIJ: I ⊆ J)
  {f: ℝ → ℝ} (h: PiecewiseConstantOn f I) :
  PiecewiseConstantOn (fun x ↦ if x ∈ I then f x else 0) J := by
  sorry

open Classical in
/-- Theorem 11.2.16 (g) (Laws of integration) / Exercise 11.2.4 -/
theorem PiecewiseConstantOn.integ_of_extend {I J: BoundedInterval} (hIJ: I ⊆ J)
  {f: ℝ → ℝ} (h: PiecewiseConstantOn f I) :
  integ (fun x ↦ if x ∈ I then f x else 0) J = integ f I := by
  sorry

end Chapter11
