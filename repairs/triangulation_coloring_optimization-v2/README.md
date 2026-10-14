# triangulation_coloring_optimization, fixed version v2.2 (convex-flip rule + regenerated full-hull inputs + CPU-quota parallelism)

## What this fixes

The README allows an edge flip only when the two triangles around the edge form a convex four-sided shape, but the grader's rule skips that condition and accepts flips that fold the mesh over itself. The same rule built the hidden inputs, so all of them contain overlapping triangles. The fixed version rejects forbidden flips and ships test inputs rebuilt without overlaps; its scores are not comparable with the original version.

Second, the README promises "Time limit: **30 seconds per case**", but the original grader runs 8 cases at once under a 30 s wall-clock limit whatever its CPU count. On the publisher's 4-CPU leaderboard grader (`judge_cpu_limit: 4`, quoted in [`evidence/impact/edgebench-leaderboard-config.md`](../../evidence/impact/edgebench-leaderboard-config.md)) each case gets about half a CPU, so a valid solution needing 20 s of CPU per case timed out on 8 of 10 cases, and one timeout makes the total `inf` (no score). The fixed version also runs at most as many cases at once as the grader has CPUs (added 2026-10-12; see "CPU-quota parallelism" below).

Third (package v2.2, 2026-10-13, issue #57), the README promises "a **triangulation** of those points", which covers the points' convex hull. The shipped Delaunay generator drops 1–3 triangles next to the hull in most inputs, so 12 of the 13 inputs rebuilt by package v2.1 left gaps. Package v2.2 completes the hull in the generator and regenerates the inputs; all 13 now cover their convex hull exactly (see "Convex-hull coverage (v2.2)" below).

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
   **shipped, unmodified** `gen.py`, the v2.2 `delaunay.py` (item 3) and the fixed `triangulation.py`
   (`../../evidence/scripts/triangulation_coloring_optimization/v2/regen_v2.py`; hashes in `v2/regen_v22.out`). The only substitution
   in the generator path is for speed, as in the review: the O(N³) `has_collinear_triple` is replaced by an exactly equivalent
   exact-integer test (same boolean result).

3. `tools/src/delaunay.py` (v2.2), in the grader image and the agent's working image: `delaunay_triangles()` returns
   `complete_hull(points, result)`, which fills each pocket between the mesh boundary and the convex hull by ear
   clipping and then restores the Delaunay property with Lawson flips. All tests are exact integer determinants
   (orientation and in-circle). Nothing else in the file changes. See "Convex-hull coverage (v2.2)".

| File | Seed | K | X,Y | Origin |
|---|---|---|---|---|
| cases/0000 | 9000000 | 16 | 10,160 | recovered: original reproduced byte-for-byte with the original rule |
| cases/0001–0004 | 9000001–9000004 | 16 | from original header | **seed new** (original not recovered); K inferred from the pattern of defects |
| cases/0005–0009 | 9000005–9000009 | 256 | from original header | **seed new**; K inferred from the pattern of defects |
| sample_data/0000–0002 | 1000001–1000003 | 16,16,256 | 10/160, 40/40, 80/20 | recovered: originals reproduced byte-for-byte (seeds/K published in `sample_data/README.md`) |

P=256, Q=1024 (generator defaults, as in every original). The pipeline was re-checked in this
package. With the original `triangulation.py` and `delaunay.py` it reproduces cases/0000 and all three samples
byte-for-byte (sha256 `8e0c5efc…`, `3c3a4ec2…`, `d6c6ddcb…`, `ea69321d…`). Hidden cases
0001–0009 therefore contain **different point sets** from the originals (same N, X, Y, P, Q, K). The same seeds give
the same points in v2.1 and v2.2; v2.2 adds the missing hull triangles before the K pre-flips, so the pre-flips and
the files differ from v2.1 except cases/0000, which had no gap and is byte-identical (`d0558565…`).
`sample_data/README.md` stays accurate (same seeds, K, X, Y; grader seeds start at 9,000,000).

**Why minimal.** There is one rule fix in the one shared file, one completion step in the generator's
triangulation, plus the data they produce. These are unchanged: `verifier.py`, `tester`, `gen.py`, the grader, the `README.md`s, the prompt,
parser, timeouts and score scale. The Dockerfiles are digest-pinned FROM + COPY only.
On the 13 fixed inputs, the fixed rule equals an exact strictly-convex-quadrilateral test, edge for
edge, and it allows only flips the old rule allowed (`rule_check.jsonl`). The comparison test in
`rule_check.py` shares the fixed rule's `a != b` and "edge ab does not exist" guards. Without those
guards, the 10 original hidden inputs have 2, 1, 2, 2, 2, 19, 17, 24, 20 and 23 on hidden cases 0000–0009 strictly convex flips that
the fixed rule rejects because the other diagonal already exists in the folded mesh. The fixed
version ships regenerated, valid inputs, where there are none. On any valid triangulation, the fixed version forbids no flip the README allows (proved in Lean: `evidence/formal/notes/triangulation_coloring_optimization.md`). Its new check that the new edge does not already exist can only reject a convex flip in a mesh that already has crossing edges.

### CPU-quota parallelism (added 2026-10-12)

**Problem.** `/tmp/eval_triangulation_coloring.py` (sha256 `1c5100f5…c009`) runs each case with `timeout=TIME_LIMIT`, `TIME_LIMIT = 30` (line 9, wall clock), inside `ProcessPoolExecutor(max_workers=min(8, len(case_files)))` (line 44); a timeout scores `float('inf')` (line 36). The task JSON sets no CPU count; the publisher's leaderboard setting gives the grader 4 CPUs. Measured on the original grader at `--cpus 4` (`evidence/runs/triangulation_coloring_optimization-cpu4v8-a`, `-b`): a valid solution doing 12 or 14 s of CPU work per case passes 10/10; 20 s per case gives 2 OK + 8 TLE and `TOTAL_SCORE inf`. At `--cpus 8` it passes 10/10 (866,166, 48.87 out of 100).

**Change.** `/tmp/eval_triangulation_coloring.py` gets the function `cpu_quota_workers()`, copied verbatim from `repairs/grid_turing_robot-v2` (cgroup `cpu.max`, cgroup v1 fallback, then `os.cpu_count()`; rounded down, kept within 1..8), and the pool line becomes `ProcessPoolExecutor(max_workers=min(cpu_quota_workers(), len(case_files)))`. The file grows from 2479 to 3386 bytes (sha256 `082d72b2…acb1`, mode 0755). It is added to `Dockerfile` and `repair.patch`; in `task.json.in` only the judge image tag changes, `convex-flip-v2` → `convex-flip-v2.1`, so an image built from the v1.0 package cannot be mistaken for this one. The flip-rule and input changes above are unchanged. The package as it was before this addition is kept internally and is not published.

**Grading time.** With 4 CPUs, 10 cases take ⌈10/4⌉ = 3 rounds of at most 30 s plus the tester; a solution that times out on every case took 90.5 s (`paired/results.md`), far inside the 1200 s `eval_timeout`. At 1 CPU the worst case is 10 × 30 s plus testers, still inside it.

**Scores.** At 8 or more grader CPUs the cap changes nothing. At 4 CPUs, deterministic solutions that finished in time keep their outputs and scores; solutions needing about 15–30 s of CPU per case are scored instead of voided; solutions that stop at a wall-clock deadline get about twice the CPU per case (measured mean 15.00 against 24.91 s for a 25 s deadline), so their scores at 4 CPUs are not comparable with the original's.

### Convex-hull coverage (v2.2, added 2026-10-13, issue #57)

**Requirement.** A triangulation of a point set covers its convex hull: triangles with vertices among the points,
pairwise disjoint interiors, union equal to the hull. With h hull points it has exactly 2N−2−h triangles, and its
boundary edges are the hull edges. The task README promises "a **triangulation** of those points" and that a flip
leaves "a valid triangulation", so the inputs must meet this. Package v2.1 did not: 12 of its 13 regenerated inputs miss
1–3 hull triangles (M < 2N−2−h, boundary edges ≠ hull edges, positive area gap). The cause is the shipped
`delaunay.py`: its Bowyer–Watson super-triangle is finite (20× the bounding box), so triangles next to the hull whose
circumcircle reaches a super-triangle corner are never created.

**Change.** `delaunay.py` gains `complete_hull()` (item 3 above; sha256 `2681c12e…` → `ef137c0a…`). On the 13 seeds it
adds 0–3 triangles before any pre-flip and changes none of the Bowyer–Watson triangles (`v2/complete_hull_check.jsonl`).
The flip rule, the grader, `gen.py` and the seeds are unchanged.

**Exact check.** `v2/hull_check.py` uses Python integers for orientation and in-circle tests and `fractions.Fraction`
for areas. A file covers its hull when no two triangle interiors overlap (exact separating-axis test) and the triangle
areas add up exactly to the hull area. It also compares boundary edges with hull edges and M with 2N−2−h.

| census | files with a gap | files covering their hull | overlapping pairs |
|---|---:|---:|---:|
| original inputs | 12 of 13 have M < 2N−2−h (and all 13 overlap) | 0 of 13 | 17–583 per file |
| package v2.1 inputs (`v2/hull_v21.jsonl`) | 12 of 13 (missing 1–3 triangles; area gap 3,042–93,674.5) | 1 of 13 (cases/0000) | 0 |
| package v2.2 inputs (`v2/hull_v22.jsonl`) | 0 of 13 | 13 of 13 | 0 |

The same check, run with each image's own `python3` on the files inside the original, v2.1 and v2.2 images
(`evidence/runs/triangulation-v22-geom`), gives identical records. The fixed flip rule still equals the exact
convex-quadrilateral test on every edge of the v2.2 inputs (`v2/rule_check_v22.jsonl`).

**Scores.** The v2.1 and v2.2 grader code give identical results on the same inputs (paired run, swapped inputs), so
every v2.1 → v2.2 score change comes from the new instances. v2.2 scores are not comparable with v2.1 scores: the
honest greedy control moves from 48.95 (v2.1) to 48.66 (v2.2) out of 100 (original: 48.87).

### Score scale and score compatibility

**All four original reference points of the 0–100 scale are kept unchanged** (`baseline 6102378`, `rank30 3372655`,
`rank1 200033`, `super_anchor 100016.5`). They come from past leaderboard runs and cannot
be recomputed for the fixed version. No new reference points are invented. The only candidate that can be computed exactly
is the shipped do-nothing total: 6,108,380 on the fixed version v2.2 (6,092,622 on v2.1) against 6,092,430 on the original
(0.26% apart). The original total is just below the original `baseline` (6,102,378) and converts to 0.055 out of 100;
the v2.2 total is 0.1% above it and converts to 0.000. Replacing `baseline` would move the low end by less than 0.06
points, and it was not done.
`task.json.in` changes only `judge.image_tag` and `work.image_tag`, both to `convex-flip-v2.2`. Superseded, rebuild:
judge `convex-flip-v2.1` (package v2.1) and `convex-flip-v2` (v1.0); work `convex-flip-v2` (v1.0 and v2.1). The tags are
recorded in `source-lock.json`.

**Fixed-version scores are not comparable with original scores.** 9 of 10 hidden inputs are new instances. All
inputs are now valid triangulations of their convex hull. The set of legal moves is smaller: about 25–35% of interior
edges that the original rule allowed are forbidden. The rank-based reference points keep their original values as a fixed reference
scale only. They no longer correspond to leaderboard ranks on the fixed version.

## How it was checked

The CPU-quota addition was checked separately: the original grader, the previous fixed version (rule and inputs only) and the current fixed version ran the same fixed-work solutions at `--cpus 4` and `--cpus 8`, and the controls below were re-run against the current fixed version at `--cpus 8` and `--cpus 4` with identical results. See [`paired/results.md`](paired/results.md), section "CPU-quota parallelism".


A side-by-side run of the original and fixed graders on the same submissions. See [`paired/results.md`](paired/results.md). Summary:

- The test submission that shows the problem (a README-forbidden flip) is accepted
  by the original grader and rejected by the fixed grader.
- The shipped do-nothing solution and an independent honest greedy solution are valid under both,
  with essentially unchanged scores out of 100.
- An invalid test submission is rejected by both.
- All 13 regenerated inputs are valid triangulations under the review's exact-integer checker and cover their convex
  hull exactly (`hull_check.py`; v2.1 left gaps in 12 of 13).
- Package v2.2 was checked on a three-grader paired run (original, previous fixed version v2.1, v2.2) of all the
  controls above plus swapped inputs, run three times on fresh E2B workers with identical results
  (`evidence/runs/triangulation-v22-paired`, `-rep2`, `-rep3`); see `paired/results.md`.
- `materialize.sh` was run from a clean copy of the package on an E2B worker (`evidence/runs/triangulation-v22-materialize`,
  `status: exit=0`): all 16 originals matched the lock, `repair.patch` applied, all 16 outputs matched, and both
  Dockerfiles built images whose replaced files have the same sha256 as the images in the paired run. (A first attempt,
  `-nopatch`, stopped because the worker lacked GNU `patch`.)

## Limits

- The fixed grader reads its CPU quota from the cgroup (`cpu.max`). This was tested with `docker run --cpus` only, not inside a Kubernetes pod, which is the backend EdgeBench's leaderboard settings use.
- CPU-quota addition: single-threaded test solutions only; multi-threaded solvers were not tested. Deadline-based solvers get more CPU at 4 CPUs under the fixed version, so their scores there are not comparable with the original's. The CPU quota is rounded down (2.5 CPUs run 2 cases at once).

- Original seeds for hidden cases 0001–0009 are unknown; their K is inferred, not recovered.
- The hull completion fills each pocket by ear clipping and then applies Lawson flips; before the pre-flips the mesh
  has no edge that fails the exact in-circle test, so it is a Delaunay triangulation (up to cocircular ties). The
  coverage check covers the 13 shipped files, not every possible seed.
- CodeChef TRICOL's own statement/checker was not consulted.
- The workspace `.git` in both images is not updated, so `git status` shows the replaced files as
  modified. Only COPY is used, as the fix rules require.
- The fixed images were built and tested inside the E2B cloud machine and then removed. The image IDs in
  `source-lock.json` are local build IDs, not registry digests.

## Build and use

Git does not contain any file copied from the EdgeBench images. It holds only our diff (`repair.patch`) and the recipe for rebuilding the full files. Regenerate them, then build:

```bash
./materialize.sh && docker build -t edgebench.judge.triangulation_coloring_optimization:convex-flip-v2.2 .
docker build -f Dockerfile.work -t edgebench.work.triangulation_coloring_optimization:convex-flip-v2.2 .
```

`materialize.sh` takes the following steps:

1. Pull the pinned image(s) by digest, unless already present.
2. Extract the original files with `docker create` and `docker cp`. No container runs in this step.
3. Check each original against `source-lock.json`.
4. Apply `repair.patch` with `patch -p1`.
5. Verify the sha256 of every file under `files/` (and `orig/`) against `source-lock.json` → `materialize.outputs`. Any mismatch fails loudly.

After that, the `Dockerfile` builds without changes. Regenerated files keep the file mode they have in the image.
See `../MATERIALIZE-CHECK.md` for how each package was verified.

Build the agent's working image with `docker build -f Dockerfile.work -t edgebench.work.triangulation_coloring_optimization:convex-flip-v2.2 .`. The regenerated `cases/` and `sample_data/` and the changed `delaunay.py` are shipped as diffs against the in-image originals.
