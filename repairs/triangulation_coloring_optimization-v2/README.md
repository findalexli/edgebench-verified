# triangulation_coloring_optimization, fixed version (convex-flip rule + regenerated inputs)

## What this fixes

The README allows an edge flip only when the two triangles around the edge form a convex four-sided shape, but the grader's rule skips that condition and accepts flips that fold the mesh over itself. The same rule built the hidden inputs, so all of them contain overlapping triangles. The fixed version rejects forbidden flips and ships test inputs rebuilt without overlaps; its scores are not comparable with the original version.

### The problem in detail

The task README defines a flip as legal only when the edge is "a diagonal of a **convex
quadrilateral** formed by two adjacent triangles". The shared library rule
`Triangulation.is_flippable` (`tools/src/triangulation.py`) checks only that the two apexes
a, b lie on opposite sides of line uv. It never checks that u, v lie on opposite sides of
line ab. It therefore accepts non-convex flips, which fold the mesh. The same rule is
used in two places:

1. By `gen.py`, to apply the K random pre-flips that built every hidden case and
   sample. So all 10 hidden cases and all 3 samples contain overlapping triangles (6 hidden
   cases also contain duplicate triangles / non-manifold edges).
2. By the official verifier/tester. So the grader accepts, and can reward, README-forbidden flips.

Full analysis: [`../../evidence/reviews/triangulation_coloring_optimization.md`](../../evidence/reviews/triangulation_coloring_optimization.md).

## What changes

1. `tools/src/triangulation.py`, `is_flippable`, in the grader image **and** the agent's working image. The
   `tools/bin/tester` and `verifier.py` that the agent can see import it unchanged. The rule now
   also requires `a != b`, that edge ab does not already exist, and
   `ccw(a,b,u) * ccw(a,b,v) < 0` (strict). Nothing else in the file changes.
2. `cases/0000..0009.txt` (grader) and `sample_data/0000..0002.txt` (working image) are regenerated with the
   **shipped, unmodified** `gen.py` + `delaunay.py` and the fixed `triangulation.py`
   (`../../evidence/scripts/triangulation_coloring_optimization/v2/regen_v2.py`). The only substitution
   in the generator path is for speed, as in the review: the O(N³) `has_collinear_triple` is replaced by an exactly equivalent
   exact-integer test (same boolean result).

| File | Seed | K | X,Y | Origin |
|---|---|---|---|---|
| cases/0000 | 9000000 | 16 | 10,160 | recovered: original reproduced byte-for-byte with the original rule |
| cases/0001–0004 | 9000001–9000004 | 16 | from original header | **seed new** (original not recovered); K inferred from the pattern of defects |
| cases/0005–0009 | 9000005–9000009 | 256 | from original header | **seed new**; K inferred from the pattern of defects |
| sample_data/0000–0002 | 1000001–1000003 | 16,16,256 | 10/160, 40/40, 80/20 | recovered: originals reproduced byte-for-byte (seeds/K published in `sample_data/README.md`) |

P=256, Q=1024 (generator defaults, as in every original). The pipeline was re-checked in this
package. With the original `triangulation.py` it reproduces cases/0000 and all three samples
byte-for-byte (sha256 `8e0c5efc…`, `3c3a4ec2…`, `d6c6ddcb…`, `ea69321d…`). Hidden cases
0001–0009 therefore contain **different point sets** from the originals (same N, X, Y, P, Q, K).
`sample_data/README.md` stays accurate (same seeds, K, X, Y; grader seeds start at 9,000,000).

**Why minimal.** There is one rule fix in the one shared file, plus the data that the faulty rule produced.
These are unchanged: `verifier.py`, `tester`, `gen.py`, `delaunay.py`, the grader, the `README.md`s, the prompt,
parser, timeouts and score scale. The Dockerfiles are digest-pinned FROM + COPY only.
On every one of the 26 inputs (10+3 original, 10+3 fixed), the fixed rule equals an independent
exact convex-quadrilateral test, edge for edge. It allows only flips the old rule allowed
(`paired/rule_check.jsonl`). The fixed version forbids no flip the README allows.

### Score scale and score compatibility

**All four original reference points of the 0–100 scale are kept unchanged** (`baseline 6102378`, `rank30 3372655`,
`rank1 200033`, `super_anchor 100016.5`). They come from past leaderboard runs and cannot
be recomputed for the fixed version. No new reference points are invented. The only candidate that can be computed exactly
is the shipped do-nothing total: 6,092,622 on the fixed version against 6,092,430 on the original (0.003% apart).
Both are just below the original `baseline` and convert to 0.054 and 0.055 out of 100. So replacing
`baseline` would not change the meaning of the low end, and it was not done.
`task.json.in` changes only `judge.image_tag` and `work.image_tag` (to `convex-flip-v2`).

**Fixed-version scores are not comparable with original scores.** 9 of 10 hidden inputs are new instances. All
inputs are now valid triangulations. The set of legal moves is smaller: about 25–35% of interior
edges that the original rule allowed are forbidden. The rank-based reference points keep their original values as a fixed reference
scale only. They no longer correspond to leaderboard ranks on the fixed version.

## How it was checked

A side-by-side run of the original and fixed graders on the same submissions. See [`paired/results.md`](paired/results.md). Summary:

- The test submission that shows the problem (a README-forbidden flip) is accepted
  by the original grader and rejected by the fixed grader.
- The shipped do-nothing solution and an independent honest greedy solution are valid under both,
  with essentially unchanged scores out of 100.
- An invalid test submission is rejected by both.
- All 13 regenerated inputs are valid triangulations under the review's exact-integer checker.

## Limits

- Original seeds for hidden cases 0001–0009 are unknown; their K is inferred, not recovered.
- A side effect of the shipped `delaunay.py` (its Delaunay "super-triangle" construction) is untouched. 12 of 13 fixed
  inputs miss 1–3 hull triangles: each is a triangulated polygon of all points, not of the full convex
  hull (`area_excess_twice < 0`, `M < 2N−2−h`). Every fixed input is otherwise a valid flat
  triangulated disk: no overlaps, crossings, folds, duplicates or non-manifold edges; Euler
  characteristic 1; all vertex links valid; all 512 vertices used. The README wording "a
  triangulation of those points" is slightly stronger than this. This is noted, not changed.
- CodeChef TRICOL's own statement/checker was not consulted.
- The workspace `.git` in both images is not updated, so `git status` shows the replaced files as
  modified. Only COPY is used, as the fix rules require.
- The fixed images were built and tested inside the E2B cloud machine and then removed. The image IDs in
  `source-lock.json` are local build IDs, not registry digests.

## Build and use

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

Build the agent's working image with `docker build -f Dockerfile.work -t ebv/triangulation_coloring_optimization-work:v2 .`. The regenerated `cases/` and `sample_data/` are shipped as diffs against the in-image originals.
