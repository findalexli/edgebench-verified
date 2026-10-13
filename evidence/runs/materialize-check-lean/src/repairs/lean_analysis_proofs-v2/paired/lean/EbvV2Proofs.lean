/-
Sorry-free proofs of the two corrected v2 statements, using only task DEFINITIONS
(no task lemma, all of which may be `sorry`). Imports the task's own modules.
-/
import Analysis.Section_11_3

namespace EbvV2
open Chapter11 BoundedInterval

theorem toSet_ordConnected (I : BoundedInterval) : (I : Set ℝ).OrdConnected := by
  cases I with
  | Ioo a b => exact Set.ordConnected_Ioo
  | Icc a b => exact Set.ordConnected_Icc
  | Ioc a b => exact Set.ordConnected_Ioc
  | Ico a b => exact Set.ordConnected_Ico

theorem toSet_sub_Icc (I : BoundedInterval) : (I : Set ℝ) ⊆ Set.Icc I.a I.b := by
  cases I with
  | Ioo a b => exact Set.Ioo_subset_Icc_self
  | Icc a b => exact subset_rfl
  | Ioc a b => exact Set.Ioc_subset_Icc_self
  | Ico a b => exact Set.Ico_subset_Icc_self

/-- The intersection of two bounded intervals is a bounded interval (proved here, not the
task's sorried `BoundedInterval.inter`). -/
theorem inter' (I J : BoundedInterval) : ∃ K : BoundedInterval, (K : Set ℝ) = (I : Set ℝ) ∩ (J : Set ℝ) := by
  set S := (I : Set ℝ) ∩ (J : Set ℝ) with hSdef
  have hS : S.OrdConnected := (toSet_ordConnected I).inter (toSet_ordConnected J)
  have hsub : S ⊆ Set.Icc I.a I.b := Set.inter_subset_left.trans (toSet_sub_Icc I)
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

/-- Corrected `Chapter11.PiecewiseConstantOn.div` (Tao, Lemma 11.2.8; no nonvanishing
hypothesis is needed because `x / 0 = 0` in Lean). -/
theorem div_corrected {f g : ℝ → ℝ} {I : BoundedInterval}
    (hf : PiecewiseConstantOn f I) (hg : PiecewiseConstantOn g I) :
    PiecewiseConstantOn (f / g) I := by
  obtain ⟨P, hP⟩ := hf
  obtain ⟨Q, hQ⟩ := hg
  choose ι hι using inter'
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

/-- Corrected `Chapter11.MajorizesOn.anti_symm` (same proof as scripts/lean_analysis_proofs/Refute.lean). -/
theorem anti_symm_corrected {f g : ℝ → ℝ} {I : BoundedInterval} :
    (∀ x ∈ (I:Set ℝ), f x = g x) ↔ MajorizesOn f g I ∧ MajorizesOn g f I := by
  constructor
  · intro h
    exact ⟨fun x hx => (h x hx).symm.le, fun x hx => (h x hx).le⟩
  · rintro ⟨h1, h2⟩ x hx
    exact le_antisymm (h2 x hx) (h1 x hx)

end EbvV2

#print axioms EbvV2.inter'
#print axioms EbvV2.div_corrected
#print axioms EbvV2.anti_symm_corrected
#check @Chapter11.MajorizesOn.anti_symm
#check @Chapter11.PiecewiseConstantOn.div
