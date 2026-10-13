# Fixed version of `jagua_nesting_optimization`: interior-intersection overlap test and allowed orientations

## What this fixes

The original grader's overlap check misses many overlaps between shapes, such as identical copies in the same place or one shape inside another. Because the score depends on strip width (and a runtime multiplier), not on overlap, an overlapping layout that cannot be cut can beat every valid one. The fixed version measures the exact overlap area between shapes and also rejects rotations an instance forbids.

In detail, the grader's `polygons_overlap` (in `jagua_task_scorer/evaluate.py`) reports an overlap only
in two cases: two edges cross properly, or a corner lies strictly inside the other polygon. It
therefore accepts large positive-area overlaps with exact integer coordinates:

- copies at the same position;
- items of the same height slid halfway over each other;
- a rectangle, triangle or diamond inside a square.

Because the score depends on strip width (and a runtime multiplier), not on overlap, the check cannot guarantee that winning
layouts are feasible. `validate_solution` also never reads `allowed_orientations`. Review:
`evidence/reviews/jagua_nesting_optimization.md`.

## What changes

`repair.patch` is generated with `diff -u`. Only `/home/workspace/jagua_task_scorer/evaluate.py` changes.

1. **`overlap_area(a, b)`** computes the area where two simple polygons intersect, by
   cutting the plane into vertical strips (slab decomposition).
   - Strip boundaries are every corner x and every x where an edge of a crosses an edge of b.
   - Inside a strip, the length the two polygons share at each x is linear in x, so the midpoint rule is
     exact up to floating-point rounding.
   - A sweep keeps track of the edges in the current strip, so the cost per pair is about linear in the
     number of corners.
   - A malformed (odd) cross-section returns infinity, so it is never accepted.
2. **`polygons_overlap`** now means `overlap_area > 1e-6 × min(item areas)`. Boundary contact
   (shared edges or corners) has zero area and stays legal. Floating-point noise from rotation and
   translation is far below this tolerance. The tolerance is relative, so it does not depend
   on the instance's units. The most it allows is 1e-6 of an item's area per pair, which is
   negligible against the grader's 2.5% improvement deadband (the smallest improvement that earns credit).
3. **`orientation_allowed`**: when an item lists `allowed_orientations`, each placement's
   rotation must equal one of them modulo 360°, within 1e-3° (`ORIENTATION_TOL_DEG`; v2.1,
   see below). Otherwise the result is `orientation_not_allowed_<idx>`. If the field is absent
   (as in `swim_cr`, the instance with free rotation), any rotation is allowed, as in jagua-rs.
   The overlap and strip checks still use the rotation exactly as reported; the tolerance only
   decides whether that rotation counts as an allowed one.

Everything else is unchanged:

- the existing bounding-box prefilter, strip bounds, demand and zero-area checks;
- the score formula, runtime multiplier, reference checkout, assets and work image.

`task.json.in` changes only `judge.image_tag` (`bba393b2dd53` to `bba393b2dd53-ebv-v2.1`). Tag
`bba393b2dd53-ebv-v2` (the first fixed version) is superseded; rebuild. The Dockerfile is `FROM`
the pinned original grader digest plus one `COPY`.

### Revision v2.1 (2026-10-13): orientation tolerance 1e-3°

The first fixed version (`evaluate.py` `df296c87…`, tag `bba393b2dd53-ebv-v2`) accepted an
allowed angle only within 1e-6°. That value was ours: the original grader never reads
`allowed_orientations` and accepts every rotation. The task asks only for "geometrically valid"
outputs and does not fix how an angle is written. 1e-6° is below the resolution of the f32
angles jagua-rs uses. A solver that keeps its angle in f32 radians and prints it in f64 degrees
writes 90.00000250447816 for 90° and 180.00000500895632 for 180°. v2 rejected such a layout on
every case with an allowed-orientation list, a false rejection that v1 did not make.

v2.1 changes only that constant, to 1e-3° (`files/` sha256 `2c3c189e…`):

- **f32 resolution.** One f32 ulp is 3.05e-5° at 360° and 2.73e-5° at 2π rad. Over every
  allowed angle in [−720°, 720°] and every 0.001° in [−360°, 360°], the f32 conversion paths
  (f32 radians to f64 degrees, f64 radians stored as f32, f32 `to_degrees`) differ from the exact
  angle by at most 6.1e-5° (`evidence/scripts/jagua_nesting_optimization/v2/f32_angles.py`).
  1e-3° leaves a margin of more than 16 times.
- **Distinct angles stay distinct.** The closest allowed angles in the scored instances are 90°
  apart, 90 000 times the tolerance.
- **Geometry.** Overlap, strip bounds and width are computed at the reported angle, not at a
  snapped one, so a near-allowed angle cannot hide an overlap. The most a 1e-3° deviation
  moves a point is 1.75e-5 × its distance from the rotation centre: 0.28 units at 16 000 units
  (the largest `gardeyn6` coordinate is 16 132), against strip widths of 20 000 units and more
  on that instance and the 2.5% deadband.

Paired evidence for the revision (original, v2 and v2.1 on the same inputs, three runs) is in
`paired/results.md`, section "Revision v2.1".

### Why an earlier candidate fix was not reused

The earlier candidate (`jagua-general-polygon-overlap-sol-v1/evaluate.py`, from an earlier
working tree, kept outside the repository) was run in the grader image on the test layouts and
on three reference layouts.

- **Its geometry is correct as a test of the coordinates as written.** It uses exact
  `Fraction` arithmetic, a proper-crossing test and an interior-interval test at strip
  midpoints. It rejects all six positive-area overlap test layouts, and it accepts the
  edge-contact test layout and the reference layouts for `swim_cr`, `gardeyn6` and `gardeyn4`.
- **Problem 1: it has zero tolerance.** It also rejects the 1e-6-shift test layout (overlap area
  1e-5, a relative overlap of 1e-7). So any floating-point overlap in honest layouts whose items only touch
  would zero a case. This did not happen on the three reference layouts checked. Its
  docstring says "This is not a tolerance policy for ideal irrational rotations". To reduce
  the risk it also rewrites quarter-turn rotations to exact cos/sin, which is a second
  change in behaviour.
- **Problem 2: it does not enforce `allowed_orientations`.** It accepts `forbidden_rotation_90`.
- **Cost.** It took 56.6 s on the gardeyn4 reference layout. That is comparable to the
  original's 54 s; this package's version takes 0.2 s.

### Score compatibility

Valid layouts with no overlap above the tolerance and with allowed rotations pass the check and
score identically. Scores under the fixed version are not comparable with the original when a layout:

- contains a positive-area overlap that the original missed. Such a case becomes `WA` (wrong answer) with score 0;
- uses a forbidden rotation (more than 1e-3° from every allowed angle);
- contains a proper edge crossing below the tolerance that the original's crossing test rejected. The fixed version accepts it.
  This is more lenient, and limited to at most 1e-6 of an item's area.

## How it was checked

Independent checks before the side-by-side run:

- **Exact comparison** (`evidence/scripts/jagua_nesting_optimization/v2/oracle_area_check.py`).
  It compares `overlap_area` with an exact rational Sutherland–Hodgman clip (a standard polygon-clipping method) of a random simple
  (possibly concave) polygon against a random convex polygon, both ways round, on integer
  coordinates. Result: 7526 comparisons, 0 mismatches, largest absolute error 3.4e-13. 1112 of the
  cases were contacts with zero area.
- **Reference outputs** (`max_overlap.py`). The frozen reference lbf outputs have a largest
  relative overlap between any two items of exactly 0 under the fixed version on the instances checked. All 16 scored
  instances are rechecked in the side-by-side run.

The side-by-side run of the original and fixed graders on the same submissions is in `paired/results.md`.

## Build and use

Git does not contain any file copied from the EdgeBench images. It holds only our diff (`repair.patch`) and the recipe for rebuilding the full files. Regenerate them, then build:

```bash
./materialize.sh && docker build -t ebv/jagua_nesting_optimization-judge:v2 .
```

`materialize.sh` takes the following steps:

1. Pull the pinned image(s) by digest, unless already present.
2. Extract the original files with `docker create` and `docker cp`. No container runs in this step.
3. Check each original against `source-lock.json`.
4. Apply `repair.patch` with `patch -p1`.
5. Verify the sha256 of every file under `files/` (and `orig/`) against `source-lock.json` → `materialize.outputs`. Any mismatch fails loudly.

After that, the `Dockerfile` builds without changes. Regenerated files keep the file mode they have in the image.
See `../MATERIALIZE-CHECK.md` for how each package was verified.

The task JSON change is in `task-json.diff`.

## Limits

- The exact comparison covers concave polygons against convex ones. Pairs of concave polygons are
  covered only by the test layouts and the reference layouts.
- Floating point is used, as in the original. The test is exact only up to rounding, which is far
  below the tolerance.
- No adversarial or near-tolerance layouts beyond the test layouts were constructed. Whether the grader is
  isolated from the submission is out of scope.
- The f32-angle submission in the revision run rewrites the angles of an honest LBF layout after
  it is solved. No solver whose search itself works on f32-derived angles was run.
