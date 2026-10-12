# triangulation_coloring_optimization — v2 (convex-flip rule + regenerated inputs)

## Defect

The task README defines a flip as legal only when the edge is "a diagonal of a **convex
quadrilateral** formed by two adjacent triangles". The shared library predicate
`Triangulation.is_flippable` (`tools/src/triangulation.py`) checks only that the two apexes
a, b lie on opposite sides of line uv; it never checks that u, v lie on opposite sides of
line ab. It therefore accepts non-convex flips, which fold the mesh. The same predicate is
used (1) by `gen.py` to apply the K random pre-flips that built every hidden case and
sample, so all 10 hidden cases and all 3 samples contain overlapping triangles (6 hidden
cases also contain duplicate triangles / non-manifold edges); and (2) by the official
verifier/tester, so the scorer accepts, and can reward, README-forbidden flips. Full
analysis: [`../../evidence/reviews/triangulation_coloring_optimization.md`](../../evidence/reviews/triangulation_coloring_optimization.md).

## Exact change

1. `tools/src/triangulation.py`, `is_flippable` (judge **and** work image; the solver-visible
   `tools/bin/tester` and `verifier.py` import it unchanged): additionally require
   `a != b`, that edge ab does not already exist, and
   `ccw(a,b,u) * ccw(a,b,v) < 0` (strict). Nothing else in the file changes.
2. `cases/0000..0009.txt` (judge) and `sample_data/0000..0002.txt` (work) regenerated with the
   **shipped, unmodified** `gen.py` + `delaunay.py` and the fixed `triangulation.py`
   (`../../evidence/scripts/triangulation_coloring_optimization/v2/regen_v2.py`). The only substitution
   in the generator path is the O(N³) `has_collinear_triple`, replaced by an exactly equivalent
   exact-integer test (same boolean) for speed — as in the review.

| file | seed | K | X,Y | provenance |
|---|---|---|---|---|
| cases/0000 | 9000000 | 16 | 10,160 | recovered: original reproduced byte-for-byte with the original rule |
| cases/0001–0004 | 9000001–9000004 | 16 | from original header | **seed new** (original not recovered); K inferred from defect profile |
| cases/0005–0009 | 9000005–9000009 | 256 | from original header | **seed new**; K inferred from defect profile |
| sample_data/0000–0002 | 1000001–1000003 | 16,16,256 | 10/160, 40/40, 80/20 | recovered: originals reproduced byte-for-byte (seeds/K published in `sample_data/README.md`) |

P=256, Q=1024 (generator defaults, as in every original). The pipeline was re-checked in this
package: with the original `triangulation.py` it reproduces cases/0000 and all three samples
byte-for-byte (sha256 `8e0c5efc…`, `3c3a4ec2…`, `d6c6ddcb…`, `ea69321d…`). Hidden cases
0001–0009 therefore contain **different point sets** from the originals (same N, X, Y, P, Q, K).
`sample_data/README.md` stays accurate (same seeds, K, X, Y; judge seeds start at 9,000,000).

## Why minimal

One predicate fix in the one shared file, plus the data that the defective predicate produced.
`verifier.py`, `tester`, `gen.py`, `delaunay.py`, the evaluator, `README.md`s, the prompt,
parser, timeouts and rescale are unchanged. The Dockerfiles are digest-pinned FROM + COPY only.
On every one of the 26 inputs (10+3 original, 10+3 v2) the fixed predicate equals an independent
exact convex-quadrilateral test edge-for-edge, and is a subset of the old predicate
(`paired/rule_check.jsonl`): v2 forbids no README-legal flip.

## Anchor decision and score compatibility

**All four original anchors are kept unchanged** (`baseline 6102378`, `rank30 3372655`,
`rank1 200033`, `super_anchor 100016.5`). They come from historical leaderboard runs and cannot
be recomputed for v2; no new rank anchors are invented. The only exactly computable anchor
candidate, the shipped do-nothing total, is 6,092,622 on v2 vs 6,092,430 on v1 (0.003% apart;
both just below the original `baseline`, normalizing to 0.054 and 0.055), so replacing
`baseline` would not change the meaning of the low end and was not done.
`task.json.in` changes only `judge.image_tag` and `work.image_tag` (to `convex-flip-v2`).

**v2 scores are not comparable with v1 scores**: 9 of 10 hidden inputs are new instances, all
inputs are now valid triangulations, and the legal move set is smaller (about 25–35% of interior
edges that v1 allowed are forbidden). The rank anchors keep their v1 values as a fixed reference
scale only; they no longer correspond to leaderboard ranks on v2.

## Paired evaluation

See [`paired/results.md`](paired/results.md). Summary: trigger (README-forbidden flip) accepted
by v1, rejected by v2; shipped do-nothing and an independent honest greedy solution valid in both
with essentially unchanged normalized scores; invalid control rejected in both; all 13
regenerated inputs are valid triangulations under the review's exact-integer checker.

## Limits

- Original seeds for hidden cases 0001–0009 are unknown; their K is inferred, not recovered.
- The Delaunay super-triangle artifact in the shipped `delaunay.py` is untouched: 12 of 13 v2
  inputs miss 1–3 hull triangles (triangulated polygon of all points, not of the full convex
  hull; `area_excess_twice < 0`, `M < 2N−2−h`). Every v2 input is otherwise a valid planar
  triangulated disk (no overlaps, crossings, folds, duplicates, non-manifold edges; Euler
  characteristic 1; all vertex links valid; all 512 vertices used). README wording "a
  triangulation of those points" is slightly stronger than this; noted, not changed.
- CodeChef TRICOL's own statement/checker was not consulted.
- Workspace `.git` in both images is not updated, so `git status` shows the replaced files as
  modified. Only COPY is used, per the repair spec.
- The v2 images were built and tested inside the E2B worker and removed; the image IDs in
  `source-lock.json` are local build IDs, not registry digests.

## Build

Git does not contain any file copied from the EdgeBench images. It holds only our diff (`repair.patch`) and the recipe for rebuilding the full files. Regenerate them, then build:

```bash
./materialize.sh && docker build -t ebv/triangulation_coloring_optimization-judge:v2 .
```

`materialize.sh` takes the following steps:

1. Pull the pinned image(s) by digest, unless already present.
2. Extract the original files with `docker create` and `docker cp`. No container runs in this step.
3. Check each original against `source-lock.json`.
4. Apply `repair.patch` with `patch -p1`.
5. Verify the sha256 of every file under `files/` (and `orig/`) against `source-lock.json` → `materialize.outputs`. Any mismatch fails loudly.

After that, the `Dockerfile` builds without changes. Regenerated files keep the file mode they have in the image.
See `../MATERIALIZE-CHECK.md` for how each package was verified.

Build the work image with `docker build -f Dockerfile.work -t ebv/triangulation_coloring_optimization-work:v2 .`. The regenerated `cases/` and `sample_data/` are shipped as diffs against the in-image originals.
