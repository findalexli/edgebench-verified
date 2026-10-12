/-
EdgeBench Verified -- triangulation_coloring_optimization: the edge-flip rule (kernel-checked).

README contract: a flip of edge uv is legal iff uv "is a diagonal of a convex quadrilateral
formed by two adjacent triangles"; "the result remains a valid triangulation".

Modelled source: `tools/src/triangulation.py`, shared by verifier.py, tools/bin/tester and gen.py,
path in both images: /home/workspace/triangulation_coloring/tools/src/triangulation.py
  * ORIGINAL (judge image seededge/edgebench.judge.triangulation_coloring_optimization@sha256:
    beeea76373084ef4e1fe5324172cf4d5fbc166943daf4cd8b60306cd89dcf671, identical in the work image)
    sha256 32862fe50b439836bc6c32e09d08568ff2a9884745b17b6259652fd641c1a844
  * FIXED (repairs/triangulation_coloring_optimization-v2, repair.patch applied)
    sha256 8b5b9cbbae071206b3ac8cb08f6f02030186c60e197755c4f8de4ccad9d86bbd
Source-to-model mapping:
  * `orient`, `ccw`                         lines 11-19 (both)      -> `orient`
  * `_rebuild_edges`, `has_edge`, `_triangles_on_edge`  lines 38-50 -> `edgesOf`, `hasEdge`, `trisOn`
  * `is_flippable` ORIGINAL lines 52-63:  len(tris)==2, apexes a,b (first vertex not in (u,v)),
       `if s1 == 0 or s2 == 0: return False; return s1 * s2 < 0`  -> `origGeom`, `isFlippable false`
  * `is_flippable` FIXED lines 52-71: additionally
       `if a == b or self.has_edge(a, b): return False` (59-60),
       `if s1 == 0 or s2 == 0 or s1 * s2 > 0: return False` (65-66),
       `s3 = ccw(a,b,u); s4 = ccw(a,b,v); if s3 == 0 or s4 == 0: return False; return s3*s4 < 0`
       (67-71)                                                   -> `fixedFlip`, `isFlippable true`
  * `flip` lines 73-88 (unchanged): replaces t1,t2 by (a,b,u),(a,b,v)  -> the triangles in part (b)
Python ints are unbounded, so ℤ arithmetic is exact. Geometry statements use ℚ.
-/
import Mathlib.Tactic.Linarith
import Mathlib.Tactic.NormNum
import Mathlib.Tactic.Ring
import Mathlib.Tactic.FieldSimp
import Mathlib.Tactic.Positivity
import Mathlib.Tactic.LinearCombination
import Mathlib.Algebra.Order.Field.Rat

namespace EbvTriangulation

abbrev Pt := ℤ × ℤ

/-- `orient` / `ccw`, triangulation.py lines 11-19. -/
def orient (p q r : Pt) : ℤ := (q.1 - p.1) * (r.2 - p.2) - (q.2 - p.2) * (r.1 - p.1)

/-- Geometric part of the ORIGINAL `is_flippable` (lines 59-63). -/
def origGeom (u v a b : Pt) : Bool :=
  if orient u v a = 0 ∨ orient u v b = 0 then false else decide (orient u v a * orient u v b < 0)

/-- FIXED `is_flippable` after the apex selection (lines 59-71); `aEqB` is the index test `a == b`,
`hasAB` is `self.has_edge(a, b)`. -/
def fixedFlip (aEqB hasAB : Bool) (u v a b : Pt) : Bool :=
  if aEqB || hasAB then false else
  if orient u v a = 0 ∨ orient u v b = 0 ∨ orient u v a * orient u v b > 0 then false else
  if orient a b u = 0 ∨ orient a b v = 0 then false else
  decide (orient a b u * orient a b v < 0)

/-! ### Executable model of the whole method (for the differential check on the N=4 input) -/

def nEdge (u v : ℕ) : ℕ × ℕ := if u < v then (u, v) else (v, u)
/-- edge keys of a (sorted) triangle, as in `_rebuild_edges` lines 41-44. -/
def edgesOf (t : ℕ × ℕ × ℕ) : List (ℕ × ℕ) := [nEdge t.1 t.2.1, nEdge t.2.1 t.2.2, nEdge t.2.2 t.1]
def trisOn (T : List (ℕ × ℕ × ℕ)) (u v : ℕ) : List (ℕ × ℕ × ℕ) :=
  T.filter (fun t => (edgesOf t).contains (nEdge u v))
def hasEdge (T : List (ℕ × ℕ × ℕ)) (u v : ℕ) : Bool := !(trisOn T u v).isEmpty
def apex (t : ℕ × ℕ × ℕ) (u v : ℕ) : ℕ :=
  ([t.1, t.2.1, t.2.2].find? (fun x => x != u && x != v)).getD 0
/-- `is_flippable` (lines 52-71); `fixed = false` gives the original, `true` the fixed version. -/
def isFlippable (fixed : Bool) (pts : List Pt) (T : List (ℕ × ℕ × ℕ)) (u v : ℕ) : Bool :=
  match trisOn T u v with
  | [t1, t2] =>
    let a := apex t1 u v; let b := apex t2 u v
    let P := fun i => pts.getD i (0, 0)
    if fixed then fixedFlip (a == b) (hasEdge T a b) (P u) (P v) (P a) (P b)
    else origGeom (P u) (P v) (P a) (P b)
  | _ => false

/-! ### Geometric notions (over ℚ) -/

/-- Strict convexity of the quadrilateral u→a→v→b (boundary of triangles uva ∪ uvb): all four
turns strictly in the same direction. -/
def StrictConvex (u a v b : Pt) : Prop :=
  (0 < orient u a v ∧ 0 < orient a v b ∧ 0 < orient v b u ∧ 0 < orient b u a) ∨
  (orient u a v < 0 ∧ orient a v b < 0 ∧ orient v b u < 0 ∧ orient b u a < 0)

instance (u a v b : Pt) : Decidable (StrictConvex u a v b) := by
  unfold StrictConvex; infer_instance

/-- The diagonals uv and ab cross at a point interior to both, and the four points are not
collinear. -/
def ProperCross (u v a b : Pt) : Prop :=
  orient u v a ≠ 0 ∧ ∃ t s : ℚ, 0 < t ∧ t < 1 ∧ 0 < s ∧ s < 1 ∧
    (u.1 : ℚ) + t * (v.1 - u.1) = a.1 + s * (b.1 - a.1) ∧
    (u.2 : ℚ) + t * (v.2 - u.2) = a.2 + s * (b.2 - a.2)

/-- Point x in the closed triangle pqr (barycentric). -/
def InTri (p q r : Pt) (x : ℚ × ℚ) : Prop :=
  ∃ α β γ : ℚ, 0 ≤ α ∧ 0 ≤ β ∧ 0 ≤ γ ∧ α + β + γ = 1 ∧
    x.1 = α * p.1 + β * q.1 + γ * r.1 ∧ x.2 = α * p.2 + β * q.2 + γ * r.2

/-- Point x in the open triangle pqr (all barycentric coordinates positive). -/
def InOpenTri (p q r : Pt) (x : ℚ × ℚ) : Prop :=
  ∃ α β γ : ℚ, 0 < α ∧ 0 < β ∧ 0 < γ ∧ α + β + γ = 1 ∧
    x.1 = α * p.1 + β * q.1 + γ * r.1 ∧ x.2 = α * p.2 + β * q.2 + γ * r.2

/-! ### Algebraic lemmas -/

/-- Two splittings of the quadrilateral's signed area: s2 - s1 = s3 - s4. -/
lemma area_identity (u v a b : Pt) :
    orient u v b - orient u v a = orient a b u - orient a b v := by
  unfold orient; ring

lemma combo_neg {x y r : ℚ} (hr0 : 0 < r) (hr1 : r < 1) (hx : x ≠ 0)
    (h : (1 - r) * x + r * y = 0) : x * y < 0 := by
  have h1 : r * (x * y) = -((1 - r) * x ^ 2) := by linear_combination x * h
  have hx2 : 0 < x ^ 2 := by positivity
  have h2 : r * (x * y) < 0 := by rw [h1]; nlinarith
  by_contra hc; push_neg at hc; nlinarith

/-! ### (a) the fixed predicate is exactly strict convexity -/

theorem fixedGeom_iff_signs (u v a b : Pt) :
    fixedFlip false false u v a b = true ↔
      orient u v a * orient u v b < 0 ∧ orient a b u * orient a b v < 0 := by
  unfold fixedFlip
  constructor
  · intro h
    simp only [Bool.or_false, Bool.false_eq_true, if_false] at h
    by_cases h1 : orient u v a = 0 ∨ orient u v b = 0 ∨ orient u v a * orient u v b > 0
    · rw [if_pos h1] at h; exact absurd h (by simp)
    rw [if_neg h1] at h
    by_cases h2 : orient a b u = 0 ∨ orient a b v = 0
    · rw [if_pos h2] at h; exact absurd h (by simp)
    rw [if_neg h2] at h
    push_neg at h1
    exact ⟨lt_of_le_of_ne h1.2.2 (mul_ne_zero h1.1 h1.2.1), of_decide_eq_true h⟩
  · rintro ⟨h12, h34⟩
    have n1 := left_ne_zero_of_mul (ne_of_lt h12)
    have n2 := right_ne_zero_of_mul (ne_of_lt h12)
    have n3 := left_ne_zero_of_mul (ne_of_lt h34)
    have n4 := right_ne_zero_of_mul (ne_of_lt h34)
    simp only [Bool.or_false, Bool.false_eq_true, if_false]
    rw [if_neg (by push_neg; exact ⟨n1, n2, le_of_lt h12⟩), if_neg (by push_neg; exact ⟨n3, n4⟩)]
    simpa using h34

theorem signs_iff_convex (u v a b : Pt) :
    (orient u v a * orient u v b < 0 ∧ orient a b u * orient a b v < 0) ↔ StrictConvex u a v b := by
  have e1 : orient u a v = -orient u v a := by unfold orient; ring
  have e2 : orient a v b = -orient a b v := by unfold orient; ring
  have e3 : orient v b u = orient u v b := by unfold orient; ring
  have e4 : orient b u a = orient a b u := by unfold orient; ring
  have hid := area_identity u v a b
  unfold StrictConvex
  rw [e1, e2, e3, e4]
  constructor
  · rintro ⟨h12, h34⟩
    rcases mul_neg_iff.mp h12 with ⟨p1, p2⟩ | ⟨p1, p2⟩ <;>
    rcases mul_neg_iff.mp h34 with ⟨p3, p4⟩ | ⟨p3, p4⟩
    · exfalso; linarith
    · right; exact ⟨by linarith, by linarith, p2, p3⟩
    · left; exact ⟨by linarith, by linarith, p2, p3⟩
    · exfalso; linarith
  · rintro (⟨q1, q2, q3, q4⟩ | ⟨q1, q2, q3, q4⟩)
    · exact ⟨mul_neg_of_neg_of_pos (by linarith) q3, mul_neg_of_pos_of_neg q4 (by linarith)⟩
    · exact ⟨mul_neg_of_pos_of_neg (by linarith) q3, mul_neg_of_neg_of_pos q4 (by linarith)⟩

theorem signs_iff_cross (u v a b : Pt) :
    (orient u v a * orient u v b < 0 ∧ orient a b u * orient a b v < 0) ↔ ProperCross u v a b := by
  -- rational versions of s1..s4
  set s1 : ℚ := ((v.1 : ℚ) - u.1) * (a.2 - u.2) - (v.2 - u.2) * (a.1 - u.1) with hs1
  set s2 : ℚ := ((v.1 : ℚ) - u.1) * (b.2 - u.2) - (v.2 - u.2) * (b.1 - u.1) with hs2
  set s3 : ℚ := ((b.1 : ℚ) - a.1) * (u.2 - a.2) - (b.2 - a.2) * (u.1 - a.1) with hs3
  set s4 : ℚ := ((b.1 : ℚ) - a.1) * (v.2 - a.2) - (b.2 - a.2) * (v.1 - a.1) with hs4
  have c1 : ((orient u v a : ℤ) : ℚ) = s1 := by simp [orient, hs1]
  have c2 : ((orient u v b : ℤ) : ℚ) = s2 := by simp [orient, hs2]
  have c3 : ((orient a b u : ℤ) : ℚ) = s3 := by simp [orient, hs3]
  have c4 : ((orient a b v : ℤ) : ℚ) = s4 := by simp [orient, hs4]
  have hid : s2 - s1 = s3 - s4 := by rw [hs1, hs2, hs3, hs4]; ring
  have cast_neg : ∀ x y : ℤ, x * y < 0 ↔ ((x : ℚ) * (y : ℚ) < 0) := by
    intro x y; constructor <;> intro h <;> exact_mod_cast h
  rw [cast_neg, cast_neg, c1, c2, c3, c4]
  unfold ProperCross
  constructor
  · rintro ⟨h12, h34⟩
    have n1 : s1 ≠ 0 := left_ne_zero_of_mul (ne_of_lt h12)
    refine ⟨fun h => n1 (by rw [← c1, h]; simp), ?_⟩
    have hD : s1 - s2 ≠ 0 := by
      intro h; have : s1 = s2 := by linarith
      rw [this] at h12; nlinarith [sq_nonneg s2]
    have hE : s3 - s4 ≠ 0 := by intro h; apply hD; linarith
    refine ⟨s3 / (s3 - s4), s1 / (s1 - s2), ?_, ?_, ?_, ?_, ?_, ?_⟩
    · rcases mul_neg_iff.mp h34 with ⟨p, q⟩ | ⟨p, q⟩
      · exact div_pos p (by linarith)
      · exact div_pos_of_neg_of_neg p (by linarith)
    · rcases mul_neg_iff.mp h34 with ⟨p, q⟩ | ⟨p, q⟩
      · rw [div_lt_one (by linarith)]; linarith
      · rw [div_lt_one_of_neg (by linarith)]; linarith
    · rcases mul_neg_iff.mp h12 with ⟨p, q⟩ | ⟨p, q⟩
      · exact div_pos p (by linarith)
      · exact div_pos_of_neg_of_neg p (by linarith)
    · rcases mul_neg_iff.mp h12 with ⟨p, q⟩ | ⟨p, q⟩
      · rw [div_lt_one (by linarith)]; linarith
      · rw [div_lt_one_of_neg (by linarith)]; linarith
    · rw [show s3 - s4 = -(s1 - s2) by linarith]
      field_simp
      rw [hs1, hs2, hs3]; ring
    · rw [show s3 - s4 = -(s1 - s2) by linarith]
      field_simp
      rw [hs1, hs2, hs3]; ring
  · rintro ⟨n1, t, s, ht0, ht1, hs0, hs1', hx, hy⟩
    have n1' : s1 ≠ 0 := by rw [← c1]; exact_mod_cast n1
    have h0 : (1 - s) * s1 + s * s2 = 0 := by
      rw [hs1, hs2]
      linear_combination (-((v.1 : ℚ) - u.1)) * hy + ((v.2 : ℚ) - u.2) * hx
    have h0' : (1 - t) * s3 + t * s4 = 0 := by
      rw [hs3, hs4]
      linear_combination ((b.1 : ℚ) - a.1) * hy - ((b.2 : ℚ) - a.2) * hx
    have h12 := combo_neg hs0 hs1' n1' h0
    refine ⟨h12, ?_⟩
    have n3 : s3 ≠ 0 := by
      intro h3
      rw [h3] at h0'
      have h4 : s4 = 0 := by
        rcases mul_eq_zero.mp (show t * s4 = 0 by linarith) with h | h
        · linarith
        · exact h
      have : s2 = s1 := by linarith
      rw [this] at h12; nlinarith [sq_nonneg s1]
    exact combo_neg ht0 ht1 n3 h0'

/-- **(a)** The fixed geometric test (lines 61-71) holds iff the quadrilateral u→a→v→b is
strictly convex, iff its diagonals cross properly. -/
theorem fixed_iff_convex (u v a b : Pt) :
    fixedFlip false false u v a b = true ↔ StrictConvex u a v b :=
  (fixedGeom_iff_signs u v a b).trans (signs_iff_convex u v a b)

theorem fixed_iff_cross (u v a b : Pt) :
    fixedFlip false false u v a b = true ↔ ProperCross u v a b :=
  (fixedGeom_iff_signs u v a b).trans (signs_iff_cross u v a b)

/-- With the combinatorial guards: the fixed rule accepts iff strictly convex, a ≠ b (index),
and ab is not already an edge. -/
theorem fixedFlip_iff (aEqB hasAB : Bool) (u v a b : Pt) :
    fixedFlip aEqB hasAB u v a b = true ↔
      StrictConvex u a v b ∧ aEqB = false ∧ hasAB = false := by
  rw [← fixed_iff_convex]
  cases aEqB <;> cases hasAB <;> simp [fixedFlip]

/-! ### Subset and completeness (the case-page claims) -/

/-- Every flip the fixed rule allows, the original rule allowed. -/
theorem fixed_subset_orig (aEqB hasAB : Bool) (u v a b : Pt) :
    fixedFlip aEqB hasAB u v a b = true → origGeom u v a b = true := by
  intro h
  have hs := ((fixedGeom_iff_signs u v a b).mp
    ((fixed_iff_convex u v a b).mpr ((fixedFlip_iff aEqB hasAB u v a b).mp h).1)).1
  have n1 := left_ne_zero_of_mul (ne_of_lt hs)
  have n2 := right_ne_zero_of_mul (ne_of_lt hs)
  unfold origGeom
  rw [if_neg (by push_neg; exact ⟨n1, n2⟩)]
  simpa using hs

/-- The fixed rule forbids no README-legal flip: if the quadrilateral u→a→v→b is strictly convex,
`a == b` (an index test) can only hold when the two apex points coincide, and no existing edge
ab properly crosses uv (true in any valid triangulation, which the README promises; in a folded
mesh this guard can reject a convex flip that would create a duplicate edge), then the fixed
rule accepts. -/
theorem fixed_complete (aEqB hasAB : Bool) (u v a b : Pt)
    (hconv : StrictConvex u a v b)
    (hidx : aEqB = true → a = b)
    (hnc : hasAB = true → ¬ ProperCross u v a b) :
    fixedFlip aEqB hasAB u v a b = true := by
  have hs := (signs_iff_convex u v a b).mpr hconv
  have hx := (signs_iff_cross u v a b).mp hs
  rw [fixedFlip_iff]
  refine ⟨hconv, ?_, ?_⟩
  · cases aEqB
    · rfl
    · exfalso; have := hidx rfl; subst this; nlinarith [hs.1, sq_nonneg (orient u v a)]
  · cases hasAB
    · rfl
    · exact absurd hx (hnc rfl)

/-! ### (b) after a fixed-rule flip the two new triangles are non-degenerate and do not overlap -/

lemma orient_bary (a b r : Pt) (x : ℚ × ℚ) (α β γ : ℚ) (hs : α + β + γ = 1)
    (h1 : x.1 = α * a.1 + β * b.1 + γ * r.1) (h2 : x.2 = α * a.2 + β * b.2 + γ * r.2) :
    ((b.1 : ℚ) - a.1) * (x.2 - a.2) - (b.2 - a.2) * (x.1 - a.1) = γ * (orient a b r : ℚ) := by
  have : α = 1 - β - γ := by linarith
  rw [h1, h2, this]; simp [orient]; ring

/-- **(b)** If the fixed rule accepts uv, the new triangles (a,b,u), (a,b,v) built by `flip`
(lines 82-85) have nonzero area, lie strictly on opposite sides of the new diagonal ab, have
disjoint interiors, and their closed triangles meet only in the segment ab. -/
theorem fixed_flip_sound (u v a b : Pt) (h : fixedFlip false false u v a b = true) :
    orient a b u ≠ 0 ∧ orient a b v ≠ 0 ∧ orient a b u * orient a b v < 0 ∧
    (∀ x, InOpenTri a b u x → ¬ InOpenTri a b v x) ∧
    (∀ x, InTri a b u x → InTri a b v x →
       ∃ β : ℚ, 0 ≤ β ∧ β ≤ 1 ∧ x.1 = a.1 + β * (b.1 - a.1) ∧ x.2 = a.2 + β * (b.2 - a.2)) := by
  have h34 := ((fixedGeom_iff_signs u v a b).mp h).2
  have h34q : ((orient a b u : ℤ) : ℚ) * (orient a b v : ℚ) < 0 := by exact_mod_cast h34
  refine ⟨left_ne_zero_of_mul (ne_of_lt h34), right_ne_zero_of_mul (ne_of_lt h34), h34, ?_, ?_⟩
  · rintro x ⟨α, β, γ, -, -, hγ, hs, h1, h2⟩ ⟨α', β', δ, -, -, hδ, hs', h1', h2'⟩
    have e1 := orient_bary a b u x α β γ hs h1 h2
    have e2 := orient_bary a b v x α' β' δ hs' h1' h2'
    have : γ * (orient a b u : ℚ) = δ * (orient a b v : ℚ) := by rw [← e1, ← e2]
    rcases mul_neg_iff.mp h34q with ⟨p, q⟩ | ⟨p, q⟩
    · nlinarith [mul_pos hγ p, mul_neg_of_pos_of_neg hδ q]
    · nlinarith [mul_neg_of_pos_of_neg hγ p, mul_pos hδ q]
  · rintro x ⟨α, β, γ, hα, hβ, hγ, hs, h1, h2⟩ ⟨α', β', δ, -, -, hδ, hs', h1', h2'⟩
    have e1 := orient_bary a b u x α β γ hs h1 h2
    have e2 := orient_bary a b v x α' β' δ hs' h1' h2'
    have hγδ : γ * (orient a b u : ℚ) = δ * (orient a b v : ℚ) := by rw [← e1, ← e2]
    have hγ0 : γ = 0 := by
      rcases mul_neg_iff.mp h34q with ⟨p, q⟩ | ⟨p, q⟩
      · have : γ * (orient a b u : ℚ) = 0 := by nlinarith [mul_nonneg hγ p.le, mul_nonneg hδ (neg_nonneg.mpr q.le)]
        rcases mul_eq_zero.mp this with h | h
        · exact h
        · exact absurd h (ne_of_gt p)
      · have : γ * (orient a b u : ℚ) = 0 := by nlinarith [mul_nonneg hγ (neg_nonneg.mpr p.le), mul_nonneg hδ q.le]
        rcases mul_eq_zero.mp this with h | h
        · exact h
        · exact absurd h (ne_of_lt p)
    subst hγ0
    refine ⟨β, hβ, by linarith, ?_, ?_⟩
    · rw [h1, show α = 1 - β by linarith]; ring
    · rw [h2, show α = 1 - β by linarith]; ring

/-! ### (c) counter-checks: the published N=4 input
`evidence/scripts/triangulation_coloring_optimization/n4_nonconvex.txt`
(points 1:(1,1) 2:(100,1) 3:(-5,50) 4:(-5,-48), triangles 1 2 3 and 1 2 4; output flips edge 1 2;
original tester: `Score = 41`, n4_nonconvex.out; fixed tester: `wrong answer: Invalid flip (1,2)`,
repairs/.../paired/result/out/rule_v2.log). 0-based indices below. -/

def n4pts : List Pt := [(1, 1), (100, 1), (-5, 50), (-5, -48)]
def n4tris : List (ℕ × ℕ × ℕ) := [(0, 1, 2), (0, 1, 3)]

/-- Differential check against the saved tester outputs: original accepts, fixed rejects. -/
theorem n4_orig_accepts : isFlippable false n4pts n4tris 0 1 = true := by decide
theorem n4_fixed_rejects : isFlippable true n4pts n4tris 0 1 = false := by decide

def p1 : Pt := (1, 1)
def p2 : Pt := (100, 1)
def p3 : Pt := (-5, 50)
def p4 : Pt := (-5, -48)

theorem n4_not_convex : ¬ StrictConvex p1 p3 p2 p4 := by decide
theorem n4_orig_geom : origGeom p1 p2 p3 p4 = true := by decide

/-- After the flip that the original accepts, the new triangles (3,4,1) and (3,4,2) share the
interior point (-4, 1). -/
theorem n4_overlap :
    InOpenTri p3 p4 p1 ((-4 : ℚ), 1) ∧ InOpenTri p3 p4 p2 ((-4 : ℚ), 1) := by
  refine ⟨⟨5/12, 5/12, 1/6, ?_⟩, ⟨52/105, 52/105, 1/105, ?_⟩⟩ <;>
    simp [p1, p2, p3, p4] <;> norm_num

/-- Counter-check for (a): the original predicate is NOT equivalent to strict convexity. -/
theorem orig_not_convexity : ¬ ∀ u v a b : Pt, origGeom u v a b = true → StrictConvex u a v b :=
  fun h => n4_not_convex (h p1 p2 p3 p4 n4_orig_geom)

/-- Counter-check for (b): the original rule does not guarantee disjoint interiors. -/
theorem orig_unsound :
    ¬ ∀ u v a b : Pt, origGeom u v a b = true →
      ∀ x, InOpenTri a b u x → ¬ InOpenTri a b v x :=
  fun h => h p1 p2 p3 p4 n4_orig_geom _ n4_overlap.1 n4_overlap.2

/-- Counter-check for the subset claim: the inclusion is strict. -/
theorem orig_not_subset_fixed :
    origGeom p1 p2 p3 p4 = true ∧ fixedFlip false false p1 p2 p3 p4 = false := by decide

end EbvTriangulation

#print axioms EbvTriangulation.fixed_iff_convex
#print axioms EbvTriangulation.fixed_iff_cross
#print axioms EbvTriangulation.fixedFlip_iff
#print axioms EbvTriangulation.fixed_subset_orig
#print axioms EbvTriangulation.fixed_complete
#print axioms EbvTriangulation.fixed_flip_sound
#print axioms EbvTriangulation.n4_orig_accepts
#print axioms EbvTriangulation.n4_fixed_rejects
#print axioms EbvTriangulation.n4_overlap
#print axioms EbvTriangulation.orig_not_convexity
#print axioms EbvTriangulation.orig_unsound
#print axioms EbvTriangulation.orig_not_subset_fixed
