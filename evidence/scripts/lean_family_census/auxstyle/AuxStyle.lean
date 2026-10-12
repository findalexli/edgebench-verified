import Lean
/-! Core-only probe: names/types of auxiliary declarations generated for an `@[simp]` iff theorem,
by proof style. Statements differ only in a constant, so identical aux lemmas are not shared (mkAuxLemma dedups by type). -/
@[simp] theorem t_sorry (a b : Nat) : a + b = b + a ↔ 0 ≤ a + 0 := by sorry
@[simp] theorem t_term (a b : Nat) : a + b = b + a ↔ 1 ≤ a + 1 :=
  ⟨fun _ => Nat.le_add_left 1 a, fun _ => Nat.add_comm a b⟩
@[simp] theorem t_omega (a b : Nat) : a + b = b + a ↔ 2 ≤ a + 2 := by
  constructor <;> intro _ <;> omega
@[simp] theorem t_simp (a b : Nat) : a + b = b + a ↔ 3 ≤ a + 3 := by
  simp [Nat.add_comm]
open Lean Meta in
#eval show MetaM Unit from do
  let env ← getEnv
  for (n, ci) in env.constants.map₂.toList do
    if (`t_sorry).isPrefixOf n || (`t_term).isPrefixOf n || (`t_omega).isPrefixOf n || (`t_simp).isPrefixOf n then
      if n.getPrefix != .anonymous then
        IO.println s!"AUX {n} : {← ppExpr ci.type}"
