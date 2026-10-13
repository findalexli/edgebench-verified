# jagua_nesting_optimization (pairwise overlap test)

## Claim

The original `polygons_overlap` accepts the published positive-area overlaps: coincident
squares, a half-slide, and a rectangle, triangle or diamond inside a square. The fixed rule
rejects a pair exactly when the intersection area exceeds 1e-6 × the smaller item's area. On
axis-aligned rectangles, a positive intersection area is equivalent to the interiors
intersecting. Touching rectangles have area 0. The fixed rule's criterion never rejects a pair
of rectangles whose interiors do not meet.

## Model and link to the code

`evidence/formal/lean/ebv/Ebv/JaguaOverlap.lean` (output in `JaguaOverlap.out`). The source is
`/home/workspace/jagua_task_scorer/evaluate.py`. The original (sha256 `08159f8e…be1`) was
rebuilt by reversing `repair.patch`; the fix has sha256 `df296c87…622d`. `orient`,
`on_segment`, `segments_cross`, `point_in_polygon`, `polygons_overlap` and the bbox prefilter
(original lines 79–158 and 216–222) are executable definitions over ℚ. So are the fixed
`overlap_area` slab algorithm, `_cross_section`, `_common_length` and the tolerance rule (v2
lines 130–237). The header maps each definition to its source lines and explains why floats
and rationals agree on the witnesses.

## Result

**Proved** within the stated scope.
- Differential check: the original-model verdicts on the seven integer witnesses equal
  `validator_output.txt`. All are accepted except `diag_shift_squares`. The fixed algorithm
  gives the exact areas 0, 100, 50, 50, 50, 50 and 25, which match `shapely_output.txt`. The
  fixed verdicts match the v2 table.
- Exhaustive family: for two 10×10 squares at integer offsets (dx, dy) ∈ [−10, 10]², 441
  cases: the fixed rule rejects exactly the positive-area cases, and the algorithm's area equals
  (10−|dx|)(10−|dy|). The original misses every positive-area case with dx = 0 or dy = 0.
- Rectangles: area > 0 ⇔ the interiors intersect (`interArea_pos_iff`); touching gives area 0;
  the fixed rule's criterion is sound (`fixed_sound`). Half-slide area = 50. These theorems are
  stated about `fixedRejectsRect` (closed-form `interArea` > 1e-6 × the smaller area), not about the
  modelled slab algorithm (`overlapArea` / `rejectFixed`); `fixed_rejects_squares` covers only two
  area-100 rectangles and follows from the definition.

## Counter-check

`orig_not_complete`: "the original rejects every positive-area overlap" is false (half-slide).
`fixed_not_zero_tolerance`: "the fix rejects every positive-area overlap" is also false. The
tiny witness has interiors that meet and an area of exactly 1e-5, below 1e-6·100, and it is
accepted. The fix allows a relative 1e-6 overlap by design, as the v2 README states.

## Limits

General polygons are not covered: the general theorems are about axis-aligned rectangles only.
No theorem states that the slab algorithm computes `interArea` for arbitrary rectangles; the
algorithm and the criterion are linked only by `decide` checks on the seven witnesses, the
441-case family and `tiny_fixed_accepts`.
The polygon algorithm is checked only on the witnesses and the 441-case family, in exact
arithmetic rather than IEEE floats. Rotation is limited to 0. The model drops the `stop_above`
early exit and the incremental active-edge list; the header explains why the verdict does not
change. The checks for orientation, demand and strip bounds are not modelled.
