# jagua_nesting_optimization v2: interior-intersection overlap test and allowed orientations

## Defect

The scorer's `polygons_overlap` (in `jagua_task_scorer/evaluate.py`) reports an overlap only
in two cases: two edges cross properly, or a vertex lies strictly inside the other polygon. It
therefore accepts large positive-area overlaps with exact integer coordinates:

- coincident copies;
- half-slid equal-height items;
- a rectangle, triangle or diamond contained in a square.

Because the score depends only on strip width, the check cannot guarantee feasible winning
layouts. `validate_solution` also never reads `allowed_orientations`. Review:
`evidence/reviews/jagua_nesting_optimization.md`.

## Exact change (`repair.patch`, generated with `diff -u`)

Only `/home/workspace/jagua_task_scorer/evaluate.py` changes.

1. **`overlap_area(a, b)`** computes the area of the intersection of two simple polygons by
   vertical slab decomposition.
   - Slab boundaries are every vertex x and every crossing x of an a-edge with a b-edge.
   - Inside a slab, the common cross-section length is linear in x, so the midpoint rule is
     exact up to floating-point rounding.
   - Active edges are maintained by a sweep, so the cost per pair is about linear in the
     number of vertices.
   - A malformed (odd) cross-section returns infinity, so it is never accepted.
2. **`polygons_overlap`** now means `overlap_area > 1e-6 × min(item areas)`. Boundary contact
   (shared edges or vertices) has zero area and stays legal. Float noise from rotation and
   translation is far below this tolerance. The tolerance is relative, so it does not depend
   on the instance's units. The most it allows is 1e-6 of an item's area per pair, which is
   negligible against the scorer's 2.5% improvement deadband.
3. **`orientation_allowed`**: when an item lists `allowed_orientations`, each placement's
   rotation must equal one of them modulo 360°, within 1e-6°. Otherwise the result is
   `orientation_not_allowed_<idx>`. If the field is absent (as in `swim_cr`, the
   continuous-rotation instance), any rotation is allowed, as in jagua-rs.

Everything else is unchanged:

- the existing bounding-box prefilter, strip bounds, demand and zero-area checks;
- the score formula, runtime multiplier, reference checkout, assets and work image.

`task.json.in` changes only `judge.image_tag` (`bba393b2dd53` to `bba393b2dd53-ebv-v2`). The
Dockerfile is `FROM` the pinned original judge digest plus one `COPY`.

## Review of the earlier candidate (`$W/work/task-repairs/jagua-general-polygon-overlap-sol-v1/evaluate.py`)

It was not reused.

I ran the candidate in the judge image on the witnesses and on three reference layouts.

- **Its geometry is correct as a test of the represented coordinates.** It uses exact
  `Fraction` arithmetic, a proper-crossing test and an interior-interval test at slab
  midpoints. It rejects all six positive-area overlap witnesses, and it accepts the
  edge-contact witness and the reference layouts for `swim_cr`, `gardeyn6` and `gardeyn4`.
- **Problem 1: it has zero tolerance.** It also rejects the 1e-6-shift witness (overlap area
  1e-5, a relative overlap of 1e-7). So any float-noise overlap of honest reconstructed
  contacts would zero a case. This did not happen on the three reference layouts checked. Its
  docstring says "This is not a tolerance policy for ideal irrational rotations". To reduce
  the risk it also rewrites quarter-turn rotations to exact cos/sin, which is a second
  behaviour change.
- **Problem 2: it does not enforce `allowed_orientations`.** It accepts `forbidden_rotation_90`.
- **Cost.** It took 56.6 s on the gardeyn4 reference layout. That is comparable to the
  original's 54 s; this package's version takes 0.2 s.

## Independent checks done before the paired run

- **Oracle comparison** (`evidence/scripts/jagua_nesting_optimization/v2/oracle_area_check.py`).
  It compares `overlap_area` with an exact rational Sutherland–Hodgman clip of a random simple
  (possibly concave) polygon against a random convex polygon, both ways round, on integer
  coordinates. Result: 7526 comparisons, 0 mismatches, max absolute error 3.4e-13. 1112 of the
  cases were zero-area contacts.
- **Reference outputs** (`max_overlap.py`). The frozen reference lbf outputs have a largest
  pairwise relative overlap of exactly 0 under v2 on the instances checked. All 16 scored
  instances are rechecked in the paired run.

## Score compatibility

Valid layouts with no overlap above the tolerance and with allowed rotations validate and
score identically. v2 scores are not comparable with v1 when a layout:

- contains a positive-area overlap that v1 missed. Such a case becomes `WA` with score 0;
- uses a forbidden rotation;
- contains a sub-tolerance proper crossing that v1's crossing test rejected. v2 accepts it.
  This is more lenient, and limited to at most 1e-6 of an item's area.

## Paired evaluation

See `paired/results.md`.

## Limits

- The area oracle covers concave-against-convex pairs. Concave-against-concave pairs are
  covered only by the witnesses and the reference layouts.
- Floats are used, as in the original. The test is exact only up to rounding, which is far
  below the tolerance.
- No adversarial or near-tolerance layouts beyond the witnesses were constructed. Scorer
  isolation is out of scope.

## Build

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
