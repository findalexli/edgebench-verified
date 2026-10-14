import Analysis.Section_11_3
namespace Chapter11
open BoundedInterval
example {f:ℝ → ℝ} {X: Set ℝ} (hX: X.Nonempty) {c:ℝ} (h: ∀ x ∈ X, f x = c) :
  constant_value_on f X = c := by
  haveI := hX.to_subtype
  exact Constant.const_eq (fun x => h x x.2)
example {f g h: ℝ → ℝ} {I: BoundedInterval}
  (hfg: MajorizesOn f g I) (hgh: MajorizesOn g h I) : MajorizesOn f h I := by
  exact fun x hx => le_trans (hgh x hx) (hfg x hx)
end Chapter11
