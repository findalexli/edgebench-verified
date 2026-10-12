/-
LOCAL MIRROR (Lean/Mathlib of the ebv project, not the task toolchain).
Definitions below are verbatim excerpts from the acquired task source
Analysis/Section_11_1.lean, Section_11_2.lean, Section_11_3.lean (only the
definitions the two statements depend on; no task lemmas). The authoritative
check is scripts/lean_analysis_proofs/Refute.lean run inside the pinned judge image.
-/
import Mathlib.Tactic

namespace Chapter11

inductive BoundedInterval where
  | Ioo (a b:ℝ) : BoundedInterval
  | Icc (a b:ℝ) : BoundedInterval
  | Ioc (a b:ℝ) : BoundedInterval
  | Ico (a b:ℝ) : BoundedInterval

open BoundedInterval

@[coe]
def BoundedInterval.toSet (I: BoundedInterval) : Set ℝ := match I with
  | Ioo a b => .Ioo a b
  | Icc a b => .Icc a b
  | Ioc a b => .Ioc a b
  | Ico a b => .Ico a b

instance BoundedInterval.inst_coeSet : Coe BoundedInterval (Set ℝ) where
  coe := toSet

open Classical in
noncomputable instance BoundedInterval.decidableEq : DecidableEq BoundedInterval := instDecidableEqOfLawfulBEq

instance BoundedInterval.instMembership : Membership ℝ BoundedInterval where
  mem I x := x ∈ (I:Set ℝ)

instance BoundedInterval.instSubset : HasSubset BoundedInterval where
  Subset I J := ∀ x, x ∈ I → x ∈ J

@[ext]
structure Partition (I: BoundedInterval) where
  intervals : Finset BoundedInterval
  exists_unique (x:ℝ) (hx : x ∈ I) : ∃! J, J ∈ intervals ∧ x ∈ J
  contains (J : BoundedInterval) (hJ : J ∈ intervals) : J ⊆ I

instance Partition.instMembership (I: BoundedInterval) : Membership BoundedInterval (Partition I) where
  mem P J := J ∈ P.intervals

abbrev Constant {X Y:Type} (f: X → Y) : Prop := ∃ c, ∀ x, f x = c
abbrev ConstantOn (f: ℝ → ℝ) (X: Set ℝ) : Prop := Constant (fun x : X ↦ f ↑x)
abbrev PiecewiseConstantWith (f:ℝ → ℝ) {I: BoundedInterval} (P: Partition I) : Prop := ∀ J ∈ P, ConstantOn f (J:Set ℝ)
abbrev PiecewiseConstantOn (f:ℝ → ℝ) (I: BoundedInterval) : Prop := ∃ P : Partition I, PiecewiseConstantWith f P
abbrev MajorizesOn (g f:ℝ → ℝ) (I: BoundedInterval) : Prop := ∀ x ∈ (I:Set ℝ), f x ≤ g x

theorem MajorizesOn.anti_symm {f g: ℝ → ℝ} {I: BoundedInterval}:
  ∀ x ∈ (I:Set ℝ), f x = g x ↔ MajorizesOn f g I ∧ MajorizesOn g f I := by
  sorry

theorem PiecewiseConstantOn.div {f g: ℝ → ℝ} {I: BoundedInterval}
  (hf: PiecewiseConstantOn f I) (hg: PiecewiseConstantOn f I) : PiecewiseConstantOn (f / g) I := by
  sorry

end Chapter11
namespace EbvRefute
open Chapter11 BoundedInterval

/-- Negation of the literal type of `Chapter11.MajorizesOn.anti_symm`. -/
theorem anti_symm_false :
    ¬ (∀ {f g : ℝ → ℝ} {I : BoundedInterval},
        ∀ x ∈ (I:Set ℝ), f x = g x ↔ MajorizesOn f g I ∧ MajorizesOn g f I) := by
  intro h
  -- I = [0,1], f = 0, g = id, x = 0: f 0 = g 0, but g ≤ f fails at 1.
  have h0 : (0:ℝ) ∈ ((Icc 0 1 : BoundedInterval) : Set ℝ) := by
    show (0:ℝ) ∈ Set.Icc 0 1; norm_num
  have h1 : (1:ℝ) ∈ ((Icc 0 1 : BoundedInterval) : Set ℝ) := by
    show (1:ℝ) ∈ Set.Icc 0 1; norm_num
  have hm := (@h (fun _ => (0:ℝ)) (fun x => x) (Icc 0 1) 0 h0).mp rfl
  -- MajorizesOn f g I means ∀ y ∈ I, g y ≤ f y, i.e. y ≤ 0
  have := hm.1 1 h1
  norm_num at this

/-- Negation of the literal type of `Chapter11.PiecewiseConstantOn.div`
(note both hypotheses are about `f`). -/
theorem div_false :
    ¬ (∀ {f g : ℝ → ℝ} {I : BoundedInterval},
        PiecewiseConstantOn f I → PiecewiseConstantOn f I → PiecewiseConstantOn (f / g) I) := by
  intro h
  -- I = [1,2], f = 1, g = id.  f is constant (one-piece partition built here, not ⊥).
  let P0 : Partition (Icc 1 2) :=
    { intervals := {Icc 1 2}
      exists_unique := fun x hx => ⟨Icc 1 2, ⟨Finset.mem_singleton_self _, hx⟩,
        fun J hJ => Finset.mem_singleton.mp hJ.1⟩
      contains := fun J hJ => by
        rw [Finset.mem_singleton.mp hJ]; exact fun x hx => hx }
  have hf : PiecewiseConstantOn (fun _ => (1:ℝ)) (Icc 1 2) :=
    ⟨P0, fun J _ => ⟨1, fun _ => rfl⟩⟩
  obtain ⟨P, hP⟩ := @h (fun _ => (1:ℝ)) (fun x => x) (Icc 1 2) hf hf
  -- every cell of P is a subsingleton, because x ↦ 1/x is injective on ℝ
  have hsub : ∀ J ∈ P.intervals, ((J:Set ℝ)).Subsingleton := by
    intro J hJ a ha b hb
    obtain ⟨c, hc⟩ := hP J hJ
    have ea := hc ⟨a, ha⟩
    have eb := hc ⟨b, hb⟩
    simp only [Pi.div_apply] at ea eb
    have : (1:ℝ) / a = 1 / b := ea.trans eb.symm
    simpa [one_div, inv_inj] using this
  have hcov : Set.Icc (1:ℝ) 2 ⊆ ⋃ J ∈ P.intervals, (J:Set ℝ) := by
    intro x hx
    obtain ⟨J, ⟨hJ, hxJ⟩, _⟩ := P.exists_unique x hx
    exact Set.mem_biUnion (Finset.mem_coe.mpr hJ) hxJ
  have hfin : (⋃ J ∈ P.intervals, (J:Set ℝ)).Finite :=
    Set.Finite.biUnion P.intervals.finite_toSet (fun J hJ => (hsub J hJ).finite)
  exact (Set.Icc_infinite (by norm_num : (1:ℝ) < 2)) (hfin.subset hcov)

/-- Corrected anti_symm (parenthesised) is provable with the task definitions. -/
theorem anti_symm_corrected {f g : ℝ → ℝ} {I : BoundedInterval} :
    (∀ x ∈ (I:Set ℝ), f x = g x) ↔ MajorizesOn f g I ∧ MajorizesOn g f I := by
  constructor
  · intro h
    exact ⟨fun x hx => (h x hx).symm.le, fun x hx => (h x hx).le⟩
  · rintro ⟨h1, h2⟩ x hx
    exact le_antisymm (h2 x hx) (h1 x hx)

end EbvRefute

/-! Identity checks: the installed declarations have exactly the refuted types.
These two theorems DO depend on `sorryAx` (through the task's sorried proofs);
they only show that the refuted propositions are syntactically the installed ones. -/
theorem EbvRefute.installed_anti_symm_inconsistent : False :=
  EbvRefute.anti_symm_false @Chapter11.MajorizesOn.anti_symm
theorem EbvRefute.installed_div_inconsistent : False :=
  EbvRefute.div_false @Chapter11.PiecewiseConstantOn.div

#print axioms EbvRefute.anti_symm_false
#print axioms EbvRefute.div_false
#print axioms EbvRefute.anti_symm_corrected
#print axioms EbvRefute.installed_anti_symm_inconsistent
#print axioms EbvRefute.installed_div_inconsistent
#check @Chapter11.MajorizesOn.anti_symm
#check @Chapter11.PiecewiseConstantOn.div
