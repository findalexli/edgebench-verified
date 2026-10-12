#!/usr/bin/env python3
"""Build honest-proof variants of Analysis/Section_4_1.lean (judge baseline copy).
T = term-mode proofs, S = tactic proofs. Both also fill the data hole Int.equivInt.invFun."""
import sys
src = open(sys.argv[1], encoding='utf-8').read()
def rep(s, old, new):
    assert s.count(old) == 1, old
    return s.replace(old, new)
SETOID_OLD = "    refl := by sorry\n    symm := by sorry\n"
PREEQ_OLD = "theorem PreInt.eq (a b c d:ℕ) : (⟨ a,b ⟩: PreInt) ≈ ⟨ c,d ⟩ ↔ a + d = c + b := by\n  sorry\n"
INTEQ_OLD = "theorem Int.eq (a b c d:ℕ): a —— b = c —— d ↔ a + d = c + b := by\n  sorry\n"
OFNAT_OLD = "theorem Int.ofNat_inj (n m:ℕ) : (ofNat(n) : Int) = (ofNat(m) : Int) ↔ ofNat(n) = ofNat(m) := by\n  sorry\n"
NATC_OLD = "theorem Int.natCast_inj (n m:ℕ) : (n : Int) = (m : Int) ↔ n = m := by\n  sorry\n"
EQUIV_OLD = """  toFun := Quotient.lift (fun ⟨ a, b ⟩ ↦ a - b) (by
    sorry)
  invFun := sorry
  left_inv n := sorry
  right_inv n := sorry
"""
EQUIV_NEW = """  toFun := Quotient.lift (fun ⟨ a, b ⟩ ↦ a - b) (by
    intro ⟨ a, b ⟩ ⟨ c, d ⟩ h
    change a + d = c + b at h
    change (a:ℤ) - b = c - d
    omega)
  invFun n := n.toNat —— (-n).toNat
  left_inv n := by
    induction n using Quotient.ind with
    | _ p =>
      obtain ⟨ a, b ⟩ := p
      show ((a:ℤ) - b).toNat —— (-((a:ℤ) - b)).toNat = a —— b
      rw [Int.eq]
      omega
  right_inv n := by
    show ((n.toNat:ℕ):ℤ) - ((-n).toNat:ℕ) = n
    omega
"""
T = {
  SETOID_OLD: "    refl := fun _ => rfl\n    symm := fun h => h.symm\n",
  PREEQ_OLD: PREEQ_OLD.replace(":= by\n  sorry\n", ":=\n  Iff.rfl\n"),
  INTEQ_OLD: INTEQ_OLD.replace(":= by\n  sorry\n", ":=\n  ⟨fun h => (PreInt.eq a b c d).mp (Quotient.exact h),\n   fun h => Quotient.sound ((PreInt.eq a b c d).mpr h)⟩\n"),
  OFNAT_OLD: OFNAT_OLD.replace(":= by\n  sorry\n", ":=\n  Int.eq n 0 m 0\n"),
  NATC_OLD: NATC_OLD.replace(":= by\n  sorry\n", ":=\n  Int.eq n 0 m 0\n"),
  EQUIV_OLD: EQUIV_NEW,
}
S = {
  SETOID_OLD: "    refl := by intro x; rfl\n    symm := by intro x y h; exact h.symm\n",
  PREEQ_OLD: PREEQ_OLD.replace("  sorry\n", "  constructor <;> intro h <;> exact h\n"),
  INTEQ_OLD: INTEQ_OLD.replace("  sorry\n", "  constructor\n  · intro h; exact (PreInt.eq a b c d).mp (Quotient.exact h)\n  · intro h; exact Quotient.sound ((PreInt.eq a b c d).mpr h)\n"),
  OFNAT_OLD: OFNAT_OLD.replace("  sorry\n", "  show n —— 0 = m —— 0 ↔ n = m\n  rw [Int.eq]; omega\n"),
  NATC_OLD: NATC_OLD.replace("  sorry\n", "  show n —— 0 = m —— 0 ↔ n = m\n  rw [Int.eq]; omega\n"),
  EQUIV_OLD: EQUIV_NEW,
}
for tag, table in (("T", T), ("S", S)):
    out = src
    for old, new in table.items():
        out = rep(out, old, new)
    open(f"Section_4_1.{tag}.lean", "w", encoding="utf-8").write(out)
    print("wrote", tag)

# Variant U: same as T, but Int.equivInt's toFun proof avoids `omega` (explicit rewriting),
# and the inverse laws are left as `sorry` (an honest partial solution: data hole filled).
EQUIV_U = """  toFun := Quotient.lift (fun ⟨ a, b ⟩ ↦ a - b) (by
    intro ⟨ a, b ⟩ ⟨ c, d ⟩ h
    change a + d = c + b at h
    change (a:ℤ) - b = c - d
    exact sub_eq_sub_iff_add_eq_add.mpr (by rw [← Nat.cast_add, ← Nat.cast_add, h]))
  invFun n := n.toNat —— (-n).toNat
  left_inv n := sorry
  right_inv n := sorry
"""
out = open("Section_4_1.T.lean", encoding="utf-8").read()
out = rep(out, EQUIV_NEW, EQUIV_U)
open("Section_4_1.U.lean", "w", encoding="utf-8").write(out)
print("wrote U")

# Variant W: same as T, except PreInt.instSetoid's refl/symm are closed by `omega`
# (a common honest tactic choice). Tests whether aux numbering depends on proof style.
out = open("Section_4_1.T.lean", encoding="utf-8").read()
out = rep(out, "    refl := fun _ => rfl\n    symm := fun h => h.symm\n",
          "    refl := by intro x; omega\n    symm := by intro x y h; omega\n")
open("Section_4_1.W.lean", "w", encoding="utf-8").write(out)
print("wrote W")

# Variant X: same as T, plus honest proofs of the two holes in Int.decidableRel.
# Their baseline aux types (`∀ a b c d, a —— b ≤ c —— d` and its negation) omit the case
# hypothesis `h` that `sorry` did not use; any real proof must use `h`.
DEC_OLD = """      | isTrue h =>
        apply isTrue
        sorry
      | isFalse h =>
        apply isFalse
        sorry
  exact Quotient.recOnSubsingleton₂ n m this
"""
DEC_NEW = """      | isTrue h =>
        apply isTrue
        refine ⟨ b + c - (a + d), ?_ ⟩
        show c —— d = (a + (b + c - (a + d))) —— (b + 0)
        rw [Int.eq]
        omega
      | isFalse h =>
        apply isFalse
        rintro ⟨ t, ht ⟩
        change c —— d = (a + t) —— (b + 0) at ht
        rw [Int.eq] at ht
        omega
  exact Quotient.recOnSubsingleton₂ n m this
"""
out = open("Section_4_1.T.lean", encoding="utf-8").read()
out = rep(out, DEC_OLD, DEC_NEW)
open("Section_4_1.X.lean", "w", encoding="utf-8").write(out)
print("wrote X")
