/-
EdgeBench Verified -- jagua_nesting_optimization: the pairwise overlap test of `validate_solution`.

Sources modelled (judge image seededge/edgebench.judge.jagua_nesting_optimization, task tag
bba393b2dd53; path /home/workspace/jagua_task_scorer/evaluate.py):
  ORIGINAL sha256 08159f8e3a59648460d8cd352ff3b71908763d9a521b41b95c90ba443f35cbe1 (16960 bytes)
  FIXED v2 sha256 df296c8714ed444317f5269be898993e533813ef7dba8327d8dad9832046622d (21211 bytes)
  (the original was rebuilt from the v2 file by reversing repairs/jagua_nesting_optimization-v2/
   repair.patch; its sha256 matches source-lock.json.)

Original file, line numbers -> model
  25        EPS = 1e-5                                  -> `EPS` (= 1/100000, see "Exactness")
  60-68     rotate_translate; every witness uses rotation 0, where cos 0 = 1.0 and sin 0 = 0.0
            exactly, so it is a translation              -> `sq`, `poly` (translated vertex lists)
  71-76     polygon_area (shoelace)                     -> `polygonArea`
  79-80     orient                                      -> `orient`
  83-88     on_segment                                  -> `onSegment`
  91-108    segments_cross: only line 96 returns True; every other path returns False
                                                         -> `segmentsCross`
  111-125   point_in_polygon: returns False as soon as p is on an edge (117-118), otherwise the
            crossing parity (119-123)                    -> `pointInPolygon`
  128-139   polygons_overlap                            -> `overlapOrig`
  142-158   polygon_bbox, bboxes_may_overlap            -> `bbox`, `bboxMay`
  216-222   pair loop: skip if bboxes are apart, reject if polygons_overlap
                                                         -> `rejectOrig`
Fixed file, line numbers -> model
  130       OVERLAP_AREA_REL_TOL = 1e-6                 -> `TOL`
  133-135   _ring                                       -> `ring`
  138-143   _cross_section                              -> `crossSection`
  146-158   _common_length                              -> `commonLen`
  161-232   overlap_area                                -> `overlapArea` (`none` = math.inf)
  235-237   polygons_overlap: area > TOL * min(|A|,|B|) -> `overlapFixed`; with the unchanged
            bbox prefilter                              -> `rejectFixed`
  Two simplifications in `overlapArea`, both value-preserving:
  * the Python sweep keeps `active_a` incrementally (edges sorted by x0, pointer `ka`, filter
    `e[2] >= s1`).  At slab [s0,s1] that list holds exactly the edges with x0 <= s0 and
    x1 >= s1, so the model takes that filter directly; list order does not matter because the
    cross-section sorts its ordinates and the cuts are a sorted set.
  * `stop_above` (early return once area > limit) is omitted: the increments are >= 0, so the
    verdict `area > limit` is the same with or without the early return.

Exactness.  The model computes in ℚ.  On the witnesses (integer coordinates <= 20, rotation 0)
every float operation of the original check is exact: orient values are integers and the
point-in-polygon abscissae are integers or halves (edges with |dy| in {5,10}, dx in {0,±5});
the `+ 1e-30` in line 121 is absorbed by rounding (|y2-y1| >= 5), and comparisons against EPS
are decided by values that are 0 or >= 1/4 in magnitude, so the float and rational verdicts
coincide.  The ℚ model drops the 1e-30; at an exact tie x = x_int the point lies on that edge
and line 117 has already returned.  The `tiny_overlap_1e-6` witness (translation 9.999999,
not a float-exact value) is used only for the fixed criterion, in exact arithmetic.
-/
import Mathlib.Algebra.Order.Field.Basic
import Mathlib.Data.Rat.Defs
import Mathlib.Tactic.Linarith

namespace EbvJagua

abbrev Pt := ℚ × ℚ

def EPS : ℚ := 1 / 100000
def TOL : ℚ := 1 / 1000000

def qabs (x : ℚ) : ℚ := if x < 0 then -x else x

/-- `poly[:-1] if poly and poly[0] == poly[-1] else poly` -/
def ring (p : List Pt) : List Pt :=
  match p.head?, p.getLast? with
  | some a, some b => if a = b then p.dropLast else p
  | _, _ => p

/-- consecutive pairs (pts[i], pts[(i+1) % n]) -/
def cyc (p : List Pt) : List (Pt × Pt) :=
  match p with
  | [] => []
  | a :: rest => p.zip (rest ++ [a])

def polygonArea (p : List Pt) : ℚ :=
  ((cyc (ring p)).map (fun e => e.1.1 * e.2.2 - e.2.1 * e.1.2)).sum / 2

/-! ### The original check -/

def orient (a b c : Pt) : ℚ := (b.1 - a.1) * (c.2 - a.2) - (b.2 - a.2) * (c.1 - a.1)

def onSegment (a b p : Pt) : Bool :=
  decide (min a.1 b.1 - EPS ≤ p.1) && decide (p.1 ≤ max a.1 b.1 + EPS) &&
  decide (min a.2 b.2 - EPS ≤ p.2) && decide (p.2 ≤ max a.2 b.2 + EPS) &&
  decide (qabs (orient a b p) ≤ EPS)

def segmentsCross (a b c d : Pt) : Bool :=
  decide (orient a b c * orient a b d < -EPS) && decide (orient c d a * orient c d b < -EPS)

def pointInPolygon (p : Pt) (poly : List Pt) : Bool :=
  let es := cyc (ring poly)
  if es.any (fun e => onSegment e.1 e.2 p) then false
  else
    (es.filter (fun e =>
        decide ((e.1.2 > p.2) ≠ (e.2.2 > p.2)) &&
        decide (p.1 < (e.2.1 - e.1.1) * (p.2 - e.1.2) / (e.2.2 - e.1.2) + e.1.1))).length % 2 == 1

def overlapOrig (a b : List Pt) : Bool :=
  let aa := ring a; let bb := ring b
  (cyc aa).any (fun e => (cyc bb).any (fun f => segmentsCross e.1 e.2 f.1 f.2)) ||
  aa.any (fun p => pointInPolygon p bb) || bb.any (fun p => pointInPolygon p aa)

def lmin : List ℚ → ℚ | [] => 0 | x :: xs => xs.foldl min x
def lmax : List ℚ → ℚ | [] => 0 | x :: xs => xs.foldl max x

def bbox (p : List Pt) : ℚ × ℚ × ℚ × ℚ :=
  let q := ring p
  (lmin (q.map (·.1)), lmin (q.map (·.2)), lmax (q.map (·.1)), lmax (q.map (·.2)))

def bboxMay (a b : ℚ × ℚ × ℚ × ℚ) : Bool :=
  !(decide (a.2.2.1 < b.1 - EPS) || decide (b.2.2.1 < a.1 - EPS) ||
    decide (a.2.2.2 < b.2.1 - EPS) || decide (b.2.2.2 < a.2.1 - EPS))

/-- Original: does the pair loop reject this pair? -/
def rejectOrig (a b : List Pt) : Bool := bboxMay (bbox a) (bbox b) && overlapOrig a b

/-! ### The fixed check: exact slab-decomposition area -/

def ins (x : ℚ) : List ℚ → List ℚ
  | [] => [x]
  | y :: ys => if x ≤ y then x :: y :: ys else y :: ins x ys

def isort : List ℚ → List ℚ
  | [] => []
  | x :: xs => ins x (isort xs)

def dedup : List ℚ → List ℚ
  | x :: y :: r => if x = y then dedup (y :: r) else x :: dedup (y :: r)
  | l => l

/-- `sorted(set(l))` -/
def sortedSet (l : List ℚ) : List ℚ := dedup (isort l)

def pairs : List ℚ → List (ℚ × ℚ)
  | a :: b :: r => (a, b) :: pairs r
  | _ => []

def consec : List ℚ → List (ℚ × ℚ)
  | a :: b :: r => (a, b) :: consec (b :: r)
  | _ => []

structure E where
  x0 : ℚ
  y0 : ℚ
  x1 : ℚ
  y1 : ℚ

def crossSection (es : List E) (x : ℚ) : Option (List (ℚ × ℚ)) :=
  let ys := isort (es.map fun e => e.y0 + (e.y1 - e.y0) * (x - e.x0) / (e.x1 - e.x0))
  if ys.length % 2 = 1 then none else some (pairs ys)

/-- two-pointer merge of `_common_length`; `fuel` bounds the steps (each step consumes one interval). -/
def commonLen : Nat → List (ℚ × ℚ) → List (ℚ × ℚ) → ℚ
  | 0, _, _ => 0
  | _, [], _ => 0
  | _, _, [] => 0
  | f + 1, a :: as, b :: bs =>
    let lo := max a.1 b.1; let hi := min a.2 b.2
    (if hi > lo then hi - lo else 0) +
      (if a.2 ≤ b.2 then commonLen f as (b :: bs) else commonLen f (a :: as) bs)

def edgesOf (pts : List Pt) (left right : ℚ) : List E :=
  (cyc pts).filterMap fun e =>
    if e.1.1 = e.2.1 then none
    else
      let g : E := if e.1.1 > e.2.1 then ⟨e.2.1, e.2.2, e.1.1, e.1.2⟩ else ⟨e.1.1, e.1.2, e.2.1, e.2.2⟩
      if g.x1 ≤ left ∨ g.x0 ≥ right then none else some g

def lineAt (e : E) (x : ℚ) : ℚ := e.y0 + (e.y1 - e.y0) / (e.x1 - e.x0) * (x - e.x0)

/-- one slab [s0,s1]: `none` if a cross-section is malformed (Python returns inf) -/
def slabArea (ea eb : List E) (s0 s1 : ℚ) : Option ℚ :=
  let actA := ea.filter (fun e => decide (e.x0 ≤ s0) && decide (e.x1 ≥ s1))
  let actB := eb.filter (fun e => decide (e.x0 ≤ s0) && decide (e.x1 ≥ s1))
  if actA = [] ∨ actB = [] then some 0
  else
    let crossings := actA.flatMap fun a => actB.filterMap fun b =>
      let d0 := lineAt a s0 - lineAt b s0
      let d1 := lineAt a s1 - lineAt b s1
      if (d0 < 0 ∧ 0 < d1) ∨ (d1 < 0 ∧ 0 < d0) then some (s0 + (s1 - s0) * d0 / (d0 - d1)) else none
    let cuts := (sortedSet (s0 :: s1 :: crossings)).filter (fun c => decide (s0 ≤ c) && decide (c ≤ s1))
    (consec cuts).foldl (fun acc u =>
      match acc with
      | none => none
      | some ar =>
        if ¬ (u.2 > u.1) then some ar
        else
          let xm := (u.1 + u.2) / 2
          match crossSection actA xm, crossSection actB xm with
          | some ia, some ib => some (ar + (u.2 - u.1) * commonLen (ia.length + ib.length) ia ib)
          | _, _ => none) (some 0)

def overlapArea (a b : List Pt) : Option ℚ :=
  let aa := ring a; let bb := ring b
  if aa.length < 3 ∨ bb.length < 3 then some 0
  else
    let left := max (lmin (aa.map (·.1))) (lmin (bb.map (·.1)))
    let right := min (lmax (aa.map (·.1))) (lmax (bb.map (·.1)))
    if ¬ left < right then some 0
    else
      let ea := edgesOf aa left right; let eb := edgesOf bb left right
      let xs := sortedSet (left :: right :: ((aa ++ bb).map (·.1)).filter (fun x => decide (left < x) && decide (x < right)))
      (consec xs).foldl (fun acc s =>
        match acc, slabArea ea eb s.1 s.2 with
        | some ar, some d => some (ar + d)
        | _, _ => none) (some 0)

def overlapFixed (a b : List Pt) : Bool :=
  let limit := TOL * min (qabs (polygonArea a)) (qabs (polygonArea b))
  match overlapArea a b with
  | none => true
  | some ar => decide (ar > limit)

/-- Fixed: does the pair loop reject this pair? -/
def rejectFixed (a b : List Pt) : Bool := bboxMay (bbox a) (bbox b) && overlapFixed a b

/-! ### Witness polygons (evidence/scripts/jagua_nesting_optimization/witnesses/*.json),
translated as rotate_translate does with rotation 0; the closing vertex is kept as in the data. -/

def poly (data : List Pt) (tx ty : ℚ) : List Pt := data.map fun p => (p.1 + tx, p.2 + ty)
def square : List Pt := [(0, 0), (10, 0), (10, 10), (0, 10), (0, 0)]
def sq (tx ty : ℚ) : List Pt := poly square tx ty
def rect105 : List Pt := [(0, 0), (10, 0), (10, 5), (0, 5), (0, 0)]
def triangle : List Pt := [(0, 0), (10, 0), (5, 10), (0, 0)]
def diamond : List Pt := [(5, 0), (10, 5), (5, 10), (0, 5), (5, 0)]

/-- (name, polygon a, polygon b); verdicts recorded in witnesses/validator_output.txt and the v2
README table. -/
def witnesses : List (String × List Pt × List Pt) :=
  [("valid_adjacent_squares", sq 0 0, sq 10 0),
   ("coincident_squares", sq 0 0, sq 0 0),
   ("half_slid_squares", sq 0 0, sq 5 0),
   ("rect_inside_square", sq 0 0, poly rect105 0 0),
   ("triangle_inside_square", sq 0 0, poly triangle 0 0),
   ("diamond_inside_square", sq 0 0, poly diamond 0 0),
   ("diag_shift_squares", sq 0 0, sq 5 5)]

/-- Differential check against the original grader's recorded verdicts
(validator_output.txt: all accepted except diag_shift_squares, rejected `overlap_0_1`). -/
theorem orig_verdicts :
    witnesses.map (fun w => rejectOrig w.2.1 w.2.2) =
      [false, false, false, false, false, false, true] := by decide +kernel

/-- Exact overlap areas computed by the fixed grader's algorithm (shapely_output.txt:
0, 100, 50, 50, 50, 50, 25). -/
theorem fixed_areas :
    witnesses.map (fun w => overlapArea w.2.1 w.2.2) =
      [some 0, some 100, some 50, some 50, some 50, some 50, some 25] := by decide +kernel

/-- Fixed verdicts (v2 README table: accept only valid_adjacent_squares). -/
theorem fixed_verdicts :
    witnesses.map (fun w => rejectFixed w.2.1 w.2.2) =
      [false, true, true, true, true, true, true] := by decide +kernel

/-- Each published positive-area witness passes the ORIGINAL check although its exact overlap
area is positive (here: 100 or 50). -/
theorem half_slide_missed :
    rejectOrig (sq 0 0) (sq 5 0) = false ∧ overlapArea (sq 0 0) (sq 5 0) = some 50 := by
  decide +kernel

/-! ### Exhaustive integer family: two 10x10 squares, offset (dx, dy) ∈ [-10, 10]^2 (441 cases).
The fixed rule rejects exactly the positive-area cases; the original misses every positive-area
case with dx = 0 or dy = 0 (axis-aligned slides, coincidence). -/

def iabs (z : Int) : Int := if z < 0 then -z else z

def familyOk (i j : Nat) : Bool :=
  let dx : Int := (i : Int) - 10; let dy : Int := (j : Int) - 10
  let a := sq 0 0; let b := sq dx dy
  let posArea := decide (iabs dx < 10 ∧ iabs dy < 10)
  (rejectFixed a b == posArea) &&
  (rejectOrig a b == (posArea && decide (dx ≠ 0 ∧ dy ≠ 0))) &&
  (overlapArea a b == some (((10 - iabs dx) * (10 - iabs dy) : Int) * (if posArea then 1 else 0)))

theorem family_row_0 : (List.range 21).all (familyOk 0) = true := by decide +kernel
theorem family_row_1 : (List.range 21).all (familyOk 1) = true := by decide +kernel
theorem family_row_2 : (List.range 21).all (familyOk 2) = true := by decide +kernel
theorem family_row_3 : (List.range 21).all (familyOk 3) = true := by decide +kernel
theorem family_row_4 : (List.range 21).all (familyOk 4) = true := by decide +kernel
theorem family_row_5 : (List.range 21).all (familyOk 5) = true := by decide +kernel
theorem family_row_6 : (List.range 21).all (familyOk 6) = true := by decide +kernel
theorem family_row_7 : (List.range 21).all (familyOk 7) = true := by decide +kernel
theorem family_row_8 : (List.range 21).all (familyOk 8) = true := by decide +kernel
theorem family_row_9 : (List.range 21).all (familyOk 9) = true := by decide +kernel
theorem family_row_10 : (List.range 21).all (familyOk 10) = true := by decide +kernel
theorem family_row_11 : (List.range 21).all (familyOk 11) = true := by decide +kernel
theorem family_row_12 : (List.range 21).all (familyOk 12) = true := by decide +kernel
theorem family_row_13 : (List.range 21).all (familyOk 13) = true := by decide +kernel
theorem family_row_14 : (List.range 21).all (familyOk 14) = true := by decide +kernel
theorem family_row_15 : (List.range 21).all (familyOk 15) = true := by decide +kernel
theorem family_row_16 : (List.range 21).all (familyOk 16) = true := by decide +kernel
theorem family_row_17 : (List.range 21).all (familyOk 17) = true := by decide +kernel
theorem family_row_18 : (List.range 21).all (familyOk 18) = true := by decide +kernel
theorem family_row_19 : (List.range 21).all (familyOk 19) = true := by decide +kernel
theorem family_row_20 : (List.range 21).all (familyOk 20) = true := by decide +kernel

/-- All 441 offsets (rows checked one by one to keep the kernel's memory small). -/
theorem family_squares (i : Nat) (hi : i < 21) : (List.range 21).all (familyOk i) = true := by
  match i, hi with
  | 0, _ => exact family_row_0
  | 1, _ => exact family_row_1
  | 2, _ => exact family_row_2
  | 3, _ => exact family_row_3
  | 4, _ => exact family_row_4
  | 5, _ => exact family_row_5
  | 6, _ => exact family_row_6
  | 7, _ => exact family_row_7
  | 8, _ => exact family_row_8
  | 9, _ => exact family_row_9
  | 10, _ => exact family_row_10
  | 11, _ => exact family_row_11
  | 12, _ => exact family_row_12
  | 13, _ => exact family_row_13
  | 14, _ => exact family_row_14
  | 15, _ => exact family_row_15
  | 16, _ => exact family_row_16
  | 17, _ => exact family_row_17
  | 18, _ => exact family_row_18
  | 19, _ => exact family_row_19
  | 20, _ => exact family_row_20
  | n + 21, h => exact absurd h (by omega)

/-! ### Axis-aligned rectangles: the mathematical criterion -/

structure Rect where
  x0 : ℚ
  y0 : ℚ
  x1 : ℚ
  y1 : ℚ

def Rect.wf (r : Rect) : Prop := r.x0 < r.x1 ∧ r.y0 < r.y1
def Rect.closed (r : Rect) (p : Pt) : Prop := r.x0 ≤ p.1 ∧ p.1 ≤ r.x1 ∧ r.y0 ≤ p.2 ∧ p.2 ≤ r.y1
def Rect.interior (r : Rect) (p : Pt) : Prop := r.x0 < p.1 ∧ p.1 < r.x1 ∧ r.y0 < p.2 ∧ p.2 < r.y1
def Rect.area (r : Rect) : ℚ := (r.x1 - r.x0) * (r.y1 - r.y0)

/-- The intersection of two rectangles is the rectangle [max x0, min x1] x [max y0, min y1]. -/
def inter (r s : Rect) : Rect := ⟨max r.x0 s.x0, max r.y0 s.y0, min r.x1 s.x1, min r.y1 s.y1⟩

def ilen (a0 a1 b0 b1 : ℚ) : ℚ := max 0 (min a1 b1 - max a0 b0)
/-- Area of the intersection (0 when it is empty or degenerate). -/
def interArea (r s : Rect) : ℚ := ilen r.x0 r.x1 s.x0 s.x1 * ilen r.y0 r.y1 s.y0 s.y1

theorem inter_closed (r s : Rect) (p : Pt) :
    (r.closed p ∧ s.closed p) ↔ (inter r s).closed p := by
  simp only [Rect.closed, inter, max_le_iff, le_min_iff]; tauto

theorem interArea_nonneg (r s : Rect) : 0 ≤ interArea r s :=
  mul_nonneg (le_max_left _ _) (le_max_left _ _)

theorem ilen_pos_iff (a0 a1 b0 b1 : ℚ) :
    0 < ilen a0 a1 b0 b1 ↔ ∃ x, (a0 < x ∧ x < a1) ∧ (b0 < x ∧ x < b1) := by
  unfold ilen
  constructor
  · intro h
    have h' : max a0 b0 < min a1 b1 := by
      rcases le_or_gt (min a1 b1 - max a0 b0) 0 with hc | hc
      · rw [max_eq_left hc] at h; exact absurd h (lt_irrefl 0)
      · linarith
    refine ⟨(max a0 b0 + min a1 b1) / 2, ?_⟩
    have := le_max_left a0 b0; have := le_max_right a0 b0
    have := min_le_left a1 b1; have := min_le_right a1 b1
    refine ⟨⟨?_, ?_⟩, ?_, ?_⟩ <;> linarith
  · rintro ⟨x, ⟨h1, h2⟩, h3, h4⟩
    have hm : max a0 b0 < min a1 b1 := lt_trans (max_lt h1 h3) (lt_min h2 h4)
    exact lt_of_lt_of_le (by linarith) (le_max_right _ _)

/-- (a) Positive intersection area ⟺ the open interiors meet. -/
theorem interArea_pos_iff (r s : Rect) :
    0 < interArea r s ↔ ∃ p : Pt, r.interior p ∧ s.interior p := by
  unfold interArea
  have hx0 : 0 ≤ ilen r.x0 r.x1 s.x0 s.x1 := le_max_left _ _
  have hy0 : 0 ≤ ilen r.y0 r.y1 s.y0 s.y1 := le_max_left _ _
  constructor
  · intro h
    have hx : 0 < ilen r.x0 r.x1 s.x0 s.x1 := lt_of_le_of_ne hx0 (fun e => by rw [← e] at h; simp at h)
    have hy : 0 < ilen r.y0 r.y1 s.y0 s.y1 := lt_of_le_of_ne hy0 (fun e => by rw [← e] at h; simp at h)
    obtain ⟨x, ⟨a1, a2⟩, b1, b2⟩ := (ilen_pos_iff _ _ _ _).1 hx
    obtain ⟨y, ⟨c1, c2⟩, d1, d2⟩ := (ilen_pos_iff _ _ _ _).1 hy
    exact ⟨(x, y), ⟨a1, a2, c1, c2⟩, ⟨b1, b2, d1, d2⟩⟩
  · rintro ⟨p, ⟨a1, a2, c1, c2⟩, ⟨b1, b2, d1, d2⟩⟩
    exact mul_pos ((ilen_pos_iff _ _ _ _).2 ⟨p.1, ⟨a1, a2⟩, b1, b2⟩)
      ((ilen_pos_iff _ _ _ _).2 ⟨p.2, ⟨c1, c2⟩, d1, d2⟩)

/-- (b) Touching (r's right edge at or left of s's left edge) has intersection area 0. -/
theorem touching_x_zero (r s : Rect) (h : r.x1 ≤ s.x0) : interArea r s = 0 := by
  have : ilen r.x0 r.x1 s.x0 s.x1 = 0 := by
    unfold ilen; apply max_eq_left
    have := min_le_left r.x1 s.x1; have := le_max_right r.x0 s.x0; linarith
  simp [interArea, this]

theorem touching_y_zero (r s : Rect) (h : r.y1 ≤ s.y0) : interArea r s = 0 := by
  have : ilen r.y0 r.y1 s.y0 s.y1 = 0 := by
    unfold ilen; apply max_eq_left
    have := min_le_left r.y1 s.y1; have := le_max_right r.y0 s.y0; linarith
  simp [interArea, this]

/-- The fixed rule on rectangles: reject iff area > 1e-6 * min(area). -/
def fixedRejectsRect (r s : Rect) : Prop := interArea r s > TOL * min r.area s.area

/-- (c) Soundness of the fixed rule: it rejects only pairs whose interiors meet, so it never
rejects touching or separated rectangles. -/
theorem fixed_sound (r s : Rect) (hr : r.wf) (hs : s.wf) (h : fixedRejectsRect r s) :
    ∃ p : Pt, r.interior p ∧ s.interior p := by
  apply (interArea_pos_iff r s).1
  have ha : 0 ≤ r.area := mul_nonneg (by linarith [hr.1]) (by linarith [hr.2])
  have hb : 0 ≤ s.area := mul_nonneg (by linarith [hs.1]) (by linarith [hs.2])
  have : 0 ≤ TOL * min r.area s.area := mul_nonneg (by norm_num [TOL]) (le_min ha hb)
  unfold fixedRejectsRect at h; linarith

/-- (d) Above the tolerance the fixed rule rejects: for two 10x10 squares every overlap of
area > 1/10000 (= 1e-6 * 100) is rejected. -/
theorem fixed_rejects_squares (r s : Rect) (hr : r.area = 100) (hs : s.area = 100)
    (h : 1 / 10000 < interArea r s) : fixedRejectsRect r s := by
  unfold fixedRejectsRect; rw [hr, hs]; norm_num [TOL]; linarith

def R (x0 y0 x1 y1 : ℚ) : Rect := ⟨x0, y0, x1, y1⟩

theorem half_slide_area : interArea (R 0 0 10 10) (R 5 0 15 10) = 50 := by
  norm_num [interArea, ilen, R]
theorem coincident_area : interArea (R 0 0 10 10) (R 0 0 10 10) = 100 := by
  norm_num [interArea, ilen, R]
theorem rect_inside_area : interArea (R 0 0 10 10) (R 0 0 10 5) = 50 := by
  norm_num [interArea, ilen, R]
theorem adjacent_area : interArea (R 0 0 10 10) (R 10 0 20 10) = 0 :=
  touching_x_zero _ _ (by norm_num [R])

/-! ### Counter-checks -/

/-- The original check does NOT satisfy "reject every positive-area overlap": witness
half_slid_squares (area 50) passes it. -/
theorem orig_not_complete :
    ¬ ∀ a b : List Pt, (∃ ar, overlapArea a b = some ar ∧ 0 < ar) → rejectOrig a b = true := by
  intro h
  have := h (sq 0 0) (sq 5 0) ⟨50, by decide +kernel, by norm_num⟩
  rw [half_slide_missed.1] at this; exact Bool.false_ne_true this

/-- Too strong: "the fixed rule rejects every overlap of positive area" is FALSE, because of the
relative tolerance.  Witness tiny_overlap_1e-6: squares [0,10]^2 and [9.999999,19.999999]x[0,10]
share interior points and overlap by exactly 1/100000 (= 1e-5) < 1e-6 * 100. -/
theorem fixed_not_zero_tolerance :
    ¬ ∀ r s : Rect, r.wf → s.wf → (∃ p : Pt, r.interior p ∧ s.interior p) → fixedRejectsRect r s := by
  intro h
  have hx := h (R 0 0 10 10) (R (9999999/1000000) 0 (19999999/1000000) 10)
    (by norm_num [Rect.wf, R]) (by norm_num [Rect.wf, R])
    ⟨(19999999/2000000, 5), by norm_num [Rect.interior, R], by norm_num [Rect.interior, R]⟩
  unfold fixedRejectsRect at hx
  norm_num [interArea, ilen, Rect.area, TOL, R] at hx

/-- The same witness through the fixed grader's algorithm: area exactly 1e-5, accepted. -/
theorem tiny_fixed_accepts :
    overlapArea (sq 0 0) (sq (9999999/1000000) 0) = some (1/100000) ∧
    rejectFixed (sq 0 0) (sq (9999999/1000000) 0) = false := by decide +kernel

end EbvJagua

#print axioms EbvJagua.orig_verdicts
#print axioms EbvJagua.fixed_areas
#print axioms EbvJagua.fixed_verdicts
#print axioms EbvJagua.half_slide_missed
#print axioms EbvJagua.family_squares
#print axioms EbvJagua.inter_closed
#print axioms EbvJagua.interArea_pos_iff
#print axioms EbvJagua.touching_x_zero
#print axioms EbvJagua.touching_y_zero
#print axioms EbvJagua.fixed_sound
#print axioms EbvJagua.fixed_rejects_squares
#print axioms EbvJagua.half_slide_area
#print axioms EbvJagua.coincident_area
#print axioms EbvJagua.rect_inside_area
#print axioms EbvJagua.adjacent_area
#print axioms EbvJagua.orig_not_complete
#print axioms EbvJagua.fixed_not_zero_tolerance
#print axioms EbvJagua.tiny_fixed_accepts
