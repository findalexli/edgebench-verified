#!/usr/bin/env python3
"""Honest variants of CombinatorialGames/SignExpansion/Basic.lean (a leaf module). Only `sorry` bodies of
six theorems are replaced; no signature changes. A = term style, B = tactic style."""
import sys
src = open(sys.argv[1], encoding='utf-8').read()
H = {  # (header line ending, A body, B body)
 'IsUpperSet (x ⁻¹\' {0}) := by\n  sorry': ('IsUpperSet (x ⁻¹\' {0}) :=\n  x.isUpperSet_preimage_singleton_zero\'', 'IsUpperSet (x ⁻¹\' {0}) := by\n  cases x with | mk s hs => exact hs'),
 '(h : sign = x) : x.copy sign h = x := by\n  sorry': ('(h : sign = x) : x.copy sign h = x := by\n  subst h; rfl', '(h : sign = x) : x.copy sign h = x := by\n  cases h\n  cases x\n  rfl'),
 '@[simp] theorem coe_mk (f h) : mk f h = f := by\n  sorry': ('@[simp] theorem coe_mk (f h) : mk f h = f :=\n  rfl', '@[simp] theorem coe_mk (f h) : mk f h = f := by\n  rfl'),
 '@[simp] theorem sign_eq_coe (x : SignExpansion) : x.sign = ⇑x := by\n  sorry': ('@[simp] theorem sign_eq_coe (x : SignExpansion) : x.sign = ⇑x :=\n  rfl', '@[simp] theorem sign_eq_coe (x : SignExpansion) : x.sign = ⇑x := by\n  rfl'),
 'x ≤ y ↔ toLex ⇑x ≤ toLex ⇑y := by\n  sorry': ('x ≤ y ↔ toLex ⇑x ≤ toLex ⇑y :=\n  Iff.rfl', 'x ≤ y ↔ toLex ⇑x ≤ toLex ⇑y := by\n  constructor <;> exact id'),
 'x < y ↔ toLex ⇑x < toLex ⇑y := by\n  sorry': ('x < y ↔ toLex ⇑x < toLex ⇑y :=\n  Iff.rfl', 'x < y ↔ toLex ⇑x < toLex ⇑y := by\n  constructor <;> exact id'),
}
for i, v in ((1, 'A'), (2, 'B')):
    s = src
    for k, bodies in H.items():
        assert s.count(k) == 1, k
        s = s.replace(k, bodies[i - 1])
    open(f'Basic.{v}.lean', 'w', encoding='utf-8').write(s)
print('ok')
