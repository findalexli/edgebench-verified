# Triangulation Coloring Optimization (`triangulation_coloring_optimization`)

**Outcome:** Fixed. <mark>The grader's rule for legal edge flips leaves out the README's convexity condition; the same rule generated all ten hidden inputs, which contain overlapping or folded triangles, and it also decides which submitted moves the grader accepts. Separately, on the publisher's 4-CPU grader a valid solution using more than about 15 s of CPU per case times out, although the README promises 30 s per case, and one timeout leaves the submission without a score; the fixed version also runs at most as many cases at once as the grader has CPUs.</mark>

The fixed version is at package v2.2. Its regenerated inputs cover their convex hull exactly, as a triangulation of the points must, and an exact census finds 0 gaps and 0 overlaps in all 13 files. The previous fixed version (v2.1) left 1 to 3 hull triangles missing in 12 of 13 regenerated files; the paired runs found no wrong or unrepeatable score from that gap, and v2.1 and v2.2 grade the same inputs identically.

![Sketch of a dart-shaped four-sided shape with a dent, where flipping its inner edge makes the two new triangles overlap; the original grader accepts the flip and scores it (41 on the four-point test input) and the fixed version rejects it as an invalid flip. On real hidden case 0009 one forbidden flip lowers (improves) the score from 644,809 to 641,611.](figures/triangulation_coloring_optimization.svg)

*The original grader accepts flips the rules forbid, and one even improves the score (lower is better: 644,809 to 641,611 on hidden case 0009); the fixed version rejects them.*

## What the task asks

The input is "a **triangulation**" of N = 512 points, meaning a mesh of triangles with corners at the points that covers their convex hull (the smallest convex region containing them) without gaps or overlaps. The agent recolours points and flips edges to lower a score. The README defines the move as follows: "if an edge is a diagonal of a **convex quadrilateral** formed by two adjacent triangles, replace it with the other diagonal. The result remains a valid triangulation."

The prompt says "The local `tester` applies flips exactly like the judge". The score is counted "on the **final** triangulation after all flips". Category: Combinatorial Optimization.

## What goes wrong

A flip is legal only for a diagonal of a convex quadrilateral. The shared library's `Triangulation.is_flippable` checks only that the two apexes (the far corners of the two triangles) lie on opposite sides of the shared edge. It never checks that the shared edge's endpoints lie on opposite sides of the new diagonal. It therefore accepts flips of non-convex quadrilaterals, and those flips fold the mesh.

The rule also shaped the inputs. `gen.py` applies K random flips with this rule to build every case. All ten hidden inputs contain overlapping triangles, with 17 to 583 overlapping triangle pairs per case. Six of them also contain duplicate triangles and non-manifold edges (edges shared by more than two triangles). Plain generator output with no flips (K=0) has no overlaps.

The same rule is the official grader's move rule, which affects scoring.

- On every hidden case, 317 to 379 interior edges pass the official rule but are not diagonals of a convex quadrilateral. The README forbids flipping these edges.
- The official rule rejects no convex-quadrilateral flip. It allows everything the documented rule allows, and more.
- On case 0009 under the original grader, the shipped do-nothing output scores `Score = 644809` (U=803). The grader accepts the same output plus one README-forbidden non-convex flip of edge (39,52), which scores `Score = 641611` (U=801). The forbidden move improves the official score (lower is better).
- In a minimal example (N=4), the input is a valid two-triangle mesh whose quadrilateral has a reflex (inward-pointing) corner. The original tester accepts the forbidden flip (`Score = 41`), and the resulting two triangles overlap. The problem does not depend on a bad input.

On a 4-CPU grader, the promised 30 s per case shrinks to about 15 s of CPU. The README says "Time limit: **30 seconds per case**" (line 50). The grader `/tmp/eval_triangulation_coloring.py` runs 8 cases at once (`max_workers=min(8, len(case_files))`, line 44) under a 30 s wall-clock limit (`TIME_LIMIT = 30`, line 9); a timed-out case scores `float('inf')` (line 36), which leaves the submission without a score out of 100 (`sforge/harness/score_rescale.py:75-76`). The task sets no CPU count. In EdgeBench's leaderboard configuration `examples/all-tasks-k8s/experiment.yaml` (quoted in [`evidence/impact/edgebench-leaderboard-config.md`](../evidence/impact/edgebench-leaderboard-config.md)) (sha256 `d9d299794ba946cae8d2b7f68a7879a35bb8565d95e78107edf79802993643be`), the grader inherits `judge_cpu_limit: 4`, so each of the first 8 cases gets about half a CPU. We measured this on the original grader at `--cpus 4` (`evidence/runs/triangulation_coloring_optimization-cpu4v8-a/result/out/summary.txt`, `-b`) with the plain `greedy.py` control followed by fixed CPU work. With 12 or 14 s per case it passes 10/10; with 20 s per case it gives 2 OK, 8 TLE and `TOTAL_SCORE inf` on both workers. At `--cpus 8` the 20 s solution passes 10/10 with 866,166 (48.87 out of 100). A solution that stops at a 25 s wall-clock deadline gets a mean of 15.00 s of CPU per case at 4 CPUs (median 12.62 s; 2 of 10 cases run alone at the end) and 24.97 s at 8 CPUs.

One thing limits the harm. The agent's working image ships the same `verifier.py`, `tester` and samples, so the agent's local testing sees exactly the grader's rule, and scores are consistent and repeatable. The harm is that the scored problem differs from the documented one.

## How much it matters

At the publisher's 4 CPUs, a valid solution using about 15 to 30 s of CPU per case loses its whole score under the original grader (measured with 20 and 28 s per case), and the fixed version scores it. A solution that stops at a wall-clock deadline gets about twice the CPU per case under the fixed version (mean 15.00 s → 24.91 s for a 25 s deadline); we did not measure how much that changes its score.

The flip rule changes which flips are legal for every solver, and every solver gets the folded hidden inputs. The only score effect measured is one forbidden flip on case 0009, which lowers that case from 644,809 to 641,611 (the 10-case total is about 6.09 million for a do-nothing output). The greedy test submission moves from 48.87 to 48.66 out of 100 under the fixed version v2.2 (48.95 under v2.1), on different inputs. We did not measure the size of the effect for a strong solver over a full optimization.

## The fix

The fixed version changes `is_flippable` in `tools/src/triangulation.py`, in both the grader image and the agent's working image. It now also requires `a != b`, that edge ab does not already exist, and that the two shared-edge endpoints lie strictly on opposite sides of the new diagonal. Nothing else in the file changes.

The fixed version also changes `tools/src/delaunay.py` (package v2.2). The shipped generator builds its Delaunay mesh inside a finite "super-triangle" and so drops 1 to 3 triangles next to the convex hull in most inputs, which leaves a mesh of a polygon through the points instead of a triangulation of the points. `delaunay_triangles()` now ends with `complete_hull()`, which fills each such pocket by ear clipping and then restores the Delaunay property with Lawson flips, using exact integer orientation and in-circle tests. On the 13 seeds this adds 0 to 3 triangles before any pre-flip and changes no existing triangle (`v2/complete_hull_check.jsonl`).

We then regenerated the 10 hidden cases and 3 samples with the shipped, unmodified `gen.py`, the v2.2 `delaunay.py` and the fixed rule.

- Case 0000 and the samples keep their original seeds (9000000 and 1000001 to 1000003).
- Cases 0001 to 0009 use new seeds 9000001 to 9000009, because the original seeds are unknown. We inferred K from each case's pattern of defects.
- Case 0000 had no hull gap and is byte-identical to the previous fixed version (v2.1). The other 12 files are new instances compared with v2.1.

The fixed version also changes `/tmp/eval_triangulation_coloring.py` so that it runs at most as many cases at once as the grader's CPU quota allows. A new function, `cpu_quota_workers()`, the same as in `repairs/grid_turing_robot-v2/`, reads the cgroup quota (`cpu.max`, or the cgroup v1 quota and period), rounds it down to whole CPUs, falls back to `os.cpu_count()` without a quota, and keeps the result between 1 and 8; the pool becomes `ProcessPoolExecutor(max_workers=min(cpu_quota_workers(), len(case_files)))`. With 8 or more CPUs it runs 8 cases at once, exactly as the original.

`verifier.py`, `tester`, `gen.py`, the READMEs, the prompt, the parser, the 30 s limit per case, the 1200 s `eval_timeout` and the reference points of the score scale are unchanged.

- On the 13 fixed inputs (v2.1 and v2.2), the fixed rule equals a strictly-convex-quadrilateral test on every edge. It allows only flips the old rule allowed, and it forbids no flip the README allows. The Lean proof covers every valid triangulation.
- The comparison test in `v2/rule_check.py` also contains the fixed rule's two new guards (`a != b`, and edge ab does not already exist), so on its own it cannot show that those guards reject nothing. Without them, the convexity counts in `flip_rules.jsonl` (`convex_flippable`) exceed the `rule_check.jsonl` counts on every original hidden case. On hidden cases 0000 to 0009, the fixed rule would reject 2, 1, 2, 2, 2, 19, 17, 24, 20 and 23 strictly convex flips whose other diagonal already exists in the folded mesh (for example case 0009, edge (79,156) with apexes 15 and 497). Such edges cannot occur in a valid triangulation, and the fixed version ships regenerated, valid inputs, so this does not affect the fixed version. The rule fix alone, applied to the original inputs, would therefore forbid a few flips of strictly convex quadrilaterals, whose result would duplicate an existing edge.
- On the original inputs the rule fix removes 319 to 398 flippable edges per hidden case (original minus fixed counts in `rule_check.jsonl`). That is slightly more than the 317 to 379 non-convex edges above, by the guarded convex edges just described.

The next table is the full grader (`eval_cmd`, 10 hidden cases) against fixed version v2.2 (`evidence/runs/triangulation-v22-paired`, identical at `--cpus 8` and `--cpus 4` and in three runs). Lower raw results are better. The previous fixed version v2.1 gave 6,092,622 (0.054) and 863,058 (48.95) for the first two rows (`paired/results.md`).

| Submission | Role | Original grader, raw | Original grader, cases OK | Original grader, out of 100 | Fixed grader, raw | Fixed grader, cases OK | Fixed grader, out of 100 |
|---|---|---:|---|---:|---:|---|---:|
| shipped `solution.py` (do nothing) | correct test submission | 6,092,430 | 10/10 | 0.055 | 6,108,380 | 10/10 | 0.000 |
| `greedy.py` (greedy recolour + greedy README-legal convex flips) | independent good-faith test submission | 866,166 | 10/10 | 48.87 | 874,742 | 10/10 | 48.66 |
| `nonconvex_flip.py` (do nothing + one README-forbidden non-convex flip per case) | **shows the problem** | 6,093,050 | 10/10 accepted | 0.052 | inf | 0/10 (WA "Invalid flip") | none (raw inf) |
| `wrong_count.py` (recolours vertex 1, claims C=0) | invalid test submission | inf | 0/10 (WA) | none (raw inf) | inf | 0/10 (WA) | none (raw inf) |

On the same inputs, the rule alone gives these results.

| Input | Original tester | Fixed tester |
|---|---|---|
| N=4 valid 2-triangle input with reflex quadrilateral, flip of edge (1,2) (test submission from the review) | accepted, `Score = 41` (result overlaps) | `wrong answer: Invalid flip (1,2)` |
| each fixed (v2.2) hidden case + its first non-convex edge that the original rule allows (10 inputs) | 10/10 accepted | 10/10 `Invalid flip` |

The agent's local testing loop (working image) gives these totals.

| Submission | Original SAMPLE_TOTAL | Fixed SAMPLE_TOTAL |
|---|---:|---:|
| do nothing | 1,780,251 | 1,817,733 |
| greedy | 263,500 | 237,515 |
| nonconvex_flip | 1,780,471 (accepted) | all 3 `wrong answer: Invalid flip` |

The saved case-0009 output with the score-improving forbidden flip scores `Score: 641611` under the original verifier and gives `INVALID: Invalid flip (39,52)` with the fixed `triangulation.py`. All 13 regenerated inputs have 0 overlapping pairs, 0 crossings, 0 folds, 0 duplicate or degenerate triangles and 0 non-manifold edges.

We checked convex-hull coverage with an exact census (`evidence/scripts/triangulation_coloring_optimization/v2/hull_check.py`; integer orientation tests and exact rational areas). A file covers its hull when no two triangle interiors overlap and the triangle areas add up exactly to the hull area.

| Inputs | Files with a hull gap | Missing triangles per file | Files covering their hull exactly |
|---|---:|---|---:|
| original | 12 of 13 (all 13 also overlap) | 0 to 4 | 0 of 13 |
| previous fixed version v2.1 | 12 of 13 | 0 to 3 (area gap 3,042 to 93,674.5) | 1 of 13 |
| fixed version v2.2 | 0 of 13 | 0 | 13 of 13 |

On the same inputs the v2.1 and v2.2 graders give identical results (for example both score 874,742 for `greedy.py` on the v2.2 cases and 863,058 on the v2.1 cases), and the original grader still accepts the forbidden flip on the v2.2 cases (`paired/results.md`, "Convex-hull coverage, package v2.2").

For the CPU share, we made paired runs at `--cpus 4` (one row at `--cpus 8`) on the same solutions with four graders: the original grader; the fixed rule and inputs without the CPU change (package v1.0); the CPU change added (v2.1) (all three: `evidence/runs/triangulation-v2-paired-cpu/result/out/summary.txt`); and the fixed version v2.2 (`evidence/runs/triangulation-v22-paired/result/out/B/summary.txt`, which also reruns the original and v2.1 with identical results). The original grader scores the original cases and the fixed versions their regenerated ones, so valid totals differ (866,166, 863,058 and 874,742).

| Solution (`greedy.py` output, preceded by fixed work) | CPUs | Original grader | Without the CPU change (v1.0) | v2.1 | Fixed version v2.2 |
| --- | ---: | --- | --- | --- | --- |
| no extra work | 4 | 10 OK, 866,166 | 10 OK, 863,058 | 10 OK, 863,058 | 10 OK, 874,742 |
| **20 s of CPU per case** | 4 | **2 OK, 8 TLE, `inf` (no score)** | **2 OK, 8 TLE, `inf`** | 10 OK, 863,058 (48.95) | **10 OK, 874,742 (48.66)** |
| **28 s of CPU per case** | 4 | **2 OK, 8 TLE, `inf`** | **2 OK, 8 TLE, `inf`** | 10 OK, 863,058 | **10 OK, 874,742** |
| works until a 25 s wall-clock deadline | 4 | 10 OK, 866,166; mean 15.00 s CPU per case | 10 OK, 863,058; mean 15.00 s | 10 OK, 863,058; mean 24.91 s | 10 OK, 874,742; mean 24.93 to 24.98 s (three runs) |
| 40 s of CPU per case (bad control) | 4 | 10 TLE, `inf` | 10 TLE, `inf` | 10 TLE, `inf` | 10 TLE, `inf` |
| 20 s of CPU per case | 8 | 10 OK, 866,166 | 10 OK, 863,058 | 10 OK, 863,058 | 10 OK, 874,742 |

The v1.0 package fails the 20 s and 28 s solutions exactly as the original does, so the parallelism change, not the flip rule, restores them. Under v2.1 the slowest 28 s case took 28.03 s; the bad control took 90.5 s to grade (3 rounds × 30 s), inside the 1200 s `eval_timeout`; v2.2 gives the same OK/TLE counts and times (90.6 s for the bad control). All earlier controls reproduce exactly against v2.1 at `--cpus 8` and `--cpus 4` (`evidence/runs/triangulation-v2-paired-cpu-controls`).

Fixed-version scores are not comparable with original scores, for four reasons:

- 9 of 10 hidden inputs are new instances (and v2.2 instances differ from v2.1 ones, so v2.2 scores are not comparable with v2.1 scores either).
- All inputs are now valid triangulations of their convex hull.
- The set of legal moves is smaller.
- At fewer than 8 grader CPUs a solution that searches until a wall-clock deadline gets more CPU per case (about twice at 4 CPUs).

The fix keeps all four original reference points of the score scale unchanged, as a fixed reference scale only. They no longer correspond to leaderboard ranks on the fixed version. The v2.2 do-nothing total (6,108,380) lies 0.1% above the original `baseline` (6,102,378), so it scores 0.000 instead of 0.055.

## How we checked it

- We ran the original `tools/bin/tester` and the full original `eval_cmd` in the original public image, pinned by digest, with `--network none`, for the original and fixed versions.
- For an independent check, we ran exact integer geometry, with no floating point, on all 10 hidden cases and all 3 samples. It covers an exact separating-axis overlap test for each triangle pair; proper edge crossings; vertices inside triangles; duplicate, degenerate and non-manifold triangles and edges; Euler characteristic and vertex links (two standard checks that a mesh is a proper surface); area excess against the convex hull; and collinear triples. On every interior edge, we compared the official rule with an independent exact convex-quadrilateral test.
- The shipped `gen.py` with seed 9000000 reproduces hidden case 0000 byte for byte, and seeds 1000001 to 1000003 reproduce all three samples byte for byte. (We swapped the O(N³) collinearity check for an exactly equivalent faster test.)
- For convex-hull coverage, `v2/hull_check.py` checks each input with integer orientation and in-circle tests and exact rational (`fractions.Fraction`) areas. It requires no overlapping interiors, total triangle area equal to the hull area, boundary edges equal to hull edges, and 2N−2−h triangles. It ran locally and, with each image's own Python, on the files inside the original, v2.1 and v2.2 images (`evidence/runs/triangulation-v22-geom`, `status: exit=0`); the records are identical. `v2/complete_hull_check.jsonl` checks the generator change before any pre-flip.
- We repeated the side-by-side run of the original and fixed graders three times, and no verdict changed (`data/paired-repeatability.md`). The v2.2 paired run of the original grader, v2.1 and v2.2 (`evidence/runs/triangulation-v22-paired`, `-rep2`, `-rep3`) ran three times on fresh E2B workers, each `status: exit=0`, with identical counts and totals.
- For the CPU runs and paired run on E2B, fixed-work solutions (12 to 28 s per case), a 25 s wall-clock-deadline solution and a 40 s bad control ran on the original grader at `--cpus 4` and `--cpus 8` (`evidence/runs/triangulation_coloring_optimization-cpu4v8-a`, `-b`) and side by side on the original grader, the previous fixed version and the fixed version (`evidence/runs/triangulation-v2-paired-cpu`, `-cpu-controls`), each job `status: exit=0`, with `--network none --memory 4g`. Each solution logs its own start, end and CPU time per case (`result/out/timing/`).

## Limits

- The fixed grader reads its CPU quota from the cgroup (`cpu.max`). We tested this with `docker run --cpus` only, not inside a Kubernetes pod, which is the backend EdgeBench's leaderboard settings use.
- We ran no AI model or solver. The score effects shown come only from test submissions we wrote.
- The original seeds for hidden cases 0001 to 0009 are unknown. We inferred their K and did not recover it.
- The hull completion is one valid choice. It fills each gap by ear clipping and then applies Lawson flips, so the mesh before the pre-flips is a Delaunay triangulation (up to cocircular ties). The coverage census covers the 13 shipped files, not every seed.
- The previous fixed version v2.1 shipped inputs with hull gaps in 12 of 13 files. The paired runs showed no wrong or unrepeatable score from them, but its scores are not comparable with v2.2 scores.
- We did not consult the CodeChef TRICOL statement and checker.
- We did not measure the gain a strong solver gets from non-convex flips over a full optimization.
- We measured the CPU dependence at 4 and 8 CPUs with single-threaded fixed-work and deadline test solutions, and did not test multi-threaded solvers. Deadline-based solvers get more CPU per case under the fixed version at 4 CPUs, so their scores are not comparable; we did not measure how much they change. The quota is rounded down, so 2.5 CPUs run 2 cases at once.
- We built and tested the fixed images locally for the run and then removed them. They are not registry digests.

## Reproduce

- Geometry and rule analysis: `evidence/scripts/triangulation_coloring_optimization/check_geometry.py`, `flip_rule_analysis.py`, `regen_compare.py`, `run_gen.py`
- Regeneration for the fixed version and rule check: `evidence/scripts/triangulation_coloring_optimization/v2/regen_v2.py` (v2.2 hashes in `v2/regen_v22.out`), `v2/rule_check.py`
- Convex-hull census: `v2/hull_check.py` (`v2/hull_v21.jsonl`, `v2/hull_v22.jsonl`), `v2/complete_hull_check.py`; v2.2 paired run: `evidence/runs/triangulation-v22-paired/run.sh`
- Side-by-side run: `repairs/triangulation_coloring_optimization-v2/paired/run.sh` (results in `paired/results.md`); CPU share: `paired/run-cpu4.sh` (as run: `evidence/runs/triangulation-v2-paired-cpu/run.sh`); CPU runs on the original grader: `evidence/runs/triangulation_coloring_optimization-cpu4v8-a/run.sh`, `-b`
- Fixed grader `/tmp/eval_triangulation_coloring.py`: sha256 `082d72b2…acb1` (original `1c5100f5…c009`); fixed `delaunay.py` `ef137c0a…` (original `2681c12e…`); image tags `convex-flip-v2.2` (superseded: judge `convex-flip-v2.1`)
- Patch: `repairs/triangulation_coloring_optimization-v2/repair.patch`
- Pinned identity: grader image `seededge/edgebench.judge.triangulation_coloring_optimization@sha256:beeea763…dcf671`; `triangulation.py` sha256 `32862fe5…`; `verifier.py` `1f0c714a…`; `gen.py` `67201f1e…`; `tools/bin/tester` `01b6e17b…`; hidden case 0000 `8e0c5efc…`.

Supporting records: `repairs/triangulation_coloring_optimization-v2/` (the folder holding the fixed version: source-lock.json, logs of the side-by-side run).
