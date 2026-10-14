# Paired v1/v2 results — triangulation_coloring_optimization-v2

> **Package v2.2 (2026-10-13).** The current fixed version is v2.2 (judge and work tag `convex-flip-v2.2`): it also
> regenerates the inputs so that each covers its convex hull. Its results are in the section "Convex-hull coverage,
> package v2.2" below. The sections before it record the v1.0 and v2.1 packages, where "v2" means the fixed version
> of that time; they are kept as run.

One E2B job (`run.sh`; job dir `evidence/runs/triangulation-v2-paired`, worker
killed by exact ID, exit 0, ~41 s). v1 = original judge/work images pulled by digest; v2 = images
built in the worker from `../Dockerfile` and `../Dockerfile.work`. Original `eval_cmd`,
`--network none --memory 4g`. Raw logs in `result/out/`. Parsed with the maintained
`score_sum` parser rules and rescaled with `score_rescale.py` and the (unchanged) anchors
(`normalize.py` → `normalize.out.jsonl`). In-image sha256 checks (`result/out/hashes_*.txt`):
v2 differs from v1 exactly in `triangulation.py`, the 10 cases and the 3 sample inputs.

## Full judge (`eval_cmd`, 10 hidden cases)

| submission | role | v1 raw | v1 cases OK | v1 normalized | v2 raw | v2 cases OK | v2 normalized |
|---|---|---:|---|---:|---:|---|---:|
| shipped `solution.py` (do nothing) | valid control | 6,092,430 | 10/10 | 0.055 | 6,092,622 | 10/10 | 0.054 |
| `greedy.py` (greedy recolour + greedy README-legal convex flips) | independent honest control | 866,166 | 10/10 | 48.87 | 863,058 | 10/10 | 48.95 |
| `nonconvex_flip.py` (do nothing + one README-forbidden non-convex flip per case) | **trigger** | 6,093,050 | 10/10 accepted | 0.052 | inf | 0/10 (WA "Invalid flip") | none (raw inf) |
| `wrong_count.py` (recolours vertex 1, claims C=0) | invalid control | inf | 0/10 (WA) | none (raw inf) | inf | 0/10 (WA) | none (raw inf) |

Docker exit 0 for all eight runs (the evaluator always exits 0). `TOTAL_SCORE inf` gives no score
out of 100: EdgeBench's harness keeps the raw `inf`, and `rescale_score` returns None for it. Valid controls: normalized scores change by ≤0.08 points;
raw changes are fully explained by the new instances for cases 0001–0009 (same anchors).
The earlier review also showed a v1 forbidden flip that *improves* the score
(case 0009, edge 39–52: 644,809 → 641,611); re-scoring that saved output
(`scripts/triangulation_coloring_optimization/case0009_one_nonconvex_flip.out`) on the original
case 0009 locally: original verifier `Score: 641611`; verifier with v2 `triangulation.py`
`INVALID: Invalid flip (39,52)`.

## Same inputs, rule only (tester in each judge image; `rule_v1.log`, `rule_v2.log`)

| input | v1 tester | v2 tester |
|---|---|---|
| N=4 valid 2-triangle input with reflex quadrilateral, flip 1–2 (review control) | accepted, `Score = 41` (result overlaps) | `wrong answer: Invalid flip (1,2)` |
| each v2 hidden case + its first non-convex flippable-under-v1 edge (10 inputs) | 10/10 accepted | 10/10 `Invalid flip` |

## Solver-visible loop (work image `eval_sample_data.sh` + `tools/bin/tester`)

| submission | v1 SAMPLE_TOTAL | v2 SAMPLE_TOTAL |
|---|---:|---:|
| do nothing | 1,780,251 | 1,802,171 |
| greedy | 263,500 | 258,183 |
| nonconvex_flip | 1,780,471 (accepted) | all 3 `wrong answer: Invalid flip` |

So the local tester the prompt says "applies flips exactly like the judge" now enforces the
same README rule as the v2 judge.

## Input validity (review's exact-integer checker, `geometry_v2.jsonl`)

All 13 regenerated files: 0 overlapping triangle pairs, 0 crossing edge pairs, 0 folded edges,
0 duplicate/degenerate triangles, 0 non-manifold edges, 0 vertices strictly inside a triangle,
V−E+F = 1, 0 bad vertex links, 0 unused vertices, 0 collinear triples (checked during
generation). Residual: 12/13 miss 1–3 convex-hull triangles (shipped Delaunay artifact; see README).
Originals for comparison: 17–583 overlapping pairs per file (review).

`geometry_v2.jsonl` is the checker's output as written. Its `file` fields hold absolute paths on the
machine where it ran (an absolute path ending in `repairs/triangulation_coloring_optimization-v2/files/cases/<NNNN>.txt`); they are left unchanged because the file is a
recorded run output, like the TLC `.out` files. Read each path relative to the repository root.

## Flip predicate equivalence (`rule_check.jsonl`, 26 files)

On every original and v2 input: v2 predicate == the exact convex-quadrilateral test in
`rule_check.py` on every edge (0 mismatches), and v2 ⊆ v1 (0 edges allowed by v2 but not v1). That
test includes the v2 guards `a != b` and "edge ab does not exist", so it is not independent of them.
Without those guards (`convex_flippable` in `flip_rules.jsonl`), the original hidden cases have
2, 1, 2, 2, 2, 19, 17, 24, 20 and 23 on hidden cases 0000–0009 strictly convex flips that v2 rejects because ab already exists in
the folded mesh. The v2 inputs are valid triangulations and have none. v1 allows
1,250–1,503 edges per file; v2 allows 861–1,171.

## CPU-quota parallelism (added 2026-10-12)

**Runs.** Two E2B jobs, both `status: exit=0`, workers killed (`result/worker.json`, ledger `evidence/runs/ledger.jsonl`):

- `evidence/runs/triangulation-v2-paired-cpu` (904 s; `run-cpu4.sh` and `arms-cpu4.txt` in this directory are copies of its `run.sh` and `arms.txt`). Three graders on the same solutions, original `eval_cmd`, `--network none --memory 4g --cpus N`, one container at a time: the **original grader** (digest-pinned image, evaluator sha256 `1c5100f5…c009`), the **previous fixed version** (`v2prev`: flip rule and regenerated inputs, original evaluator) and the **fixed version** (`v2`: the same plus the evaluator with `cpu_quota_workers()`, sha256 `082d72b2…acb1`). The fixed version and the previous fixed version have identical cases and tools (`result/out/eval_sha.txt`). The fixed grader computes 1/2/3/4/8 cases at once at `--cpus 1/2/3/4/8` (`result/out/v2_workers.txt`). Each solution is a wrapper around the honest `greedy.py` control (mounted as `/ebvsol/base.py`): it runs the control, then works until W CPU-seconds in total (`cpuW`) or W seconds of wall clock (`wall25`), then prints the control's answer. `cpu0` is the control alone; `spin40` (40 s of CPU) must time out.
- `evidence/runs/triangulation-v2-paired-cpu-controls` (61 s): the package's own `run.sh` (above) unchanged except for `--cpus` and the output directory, run against the fixed version at `--cpus 8` (as originally) and at `--cpus 4`.

**Results** (source: `evidence/runs/triangulation-v2-paired-cpu/result/out/summary.txt`, per-case times `timing_summary.txt`; score out of 100 via `sforge/harness/score_rescale.py`). The original grader scores the original cases; both fixed graders score the regenerated cases, so valid totals differ (866,166 against 863,058; 48.87 against 48.95), as in the table at the top.

| Solution | CPUs | Original grader | Previous fixed version | Fixed version |
| --- | ---: | --- | --- | --- |
| `cpu0` (control alone) | 4 | 10 OK, 866,166 | 10 OK, 863,058 | 10 OK, 863,058 |
| **`cpu20` (20 s CPU per case)** | 4 | **2 OK, 8 TLE, inf (no score)** | **2 OK, 8 TLE, inf** | **10 OK, 863,058 (48.95)** |
| **`cpu28` (28 s CPU per case)** | 4 | **2 OK, 8 TLE, inf** | **2 OK, 8 TLE, inf** | **10 OK, 863,058** |
| `wall25` (works until 25 s wall clock) | 4 | 10 OK, 866,166 | 10 OK, 863,058 | 10 OK, 863,058 |
| `spin40` (bad control, 40 s CPU per case) | 4 | 10 TLE, inf, 60.5 s | 10 TLE, inf, 60.5 s | 10 TLE, inf, 90.5 s |
| `cpu20` | 8 | 10 OK, 866,166, 40.8 s | 10 OK, 863,058, 40.8 s | 10 OK, 863,058, 40.7 s |

The previous fixed version fails `cpu20` and `cpu28` exactly as the original does, so the cap, not the flip-rule change, is what restores them. Under the fixed version at 4 CPUs the slowest `cpu28` case finished in 28.03 s of wall time. The `wall25` solution got a mean of 15.00 s of CPU per case under the original grader (median 12.50 s; 2 of 10 cases ran alone at the end) and 24.91 s under the fixed version. Grading the bad control took 90.5 s under the fixed version (3 rounds × 30 s), inside the 1200 s `eval_timeout`.

**Existing controls re-run against the fixed version** (source: `evidence/runs/triangulation-v2-paired-cpu-controls/result/out/c8/`, `c4/`). At both `--cpus 8` and `--cpus 4`, every result in the tables above is reproduced exactly: do-nothing 6,092,430 (original) and 6,092,622 (fixed), 10/10 OK; `greedy` 866,166 and 863,058; `nonconvex_flip` 6,093,050 accepted by the original and `inf` (10 × WA "Invalid flip") under the fixed version; `wrong_count` `inf` under both; the rule-only check (`rule_v1`/`rule_v2`: 0 and 11 `Invalid flip`); and the solver-visible sample totals (1,780,251 / 1,802,171, 263,500 / 258,183, `nonconvex_flip` 1,780,471 accepted and 3 × `Invalid flip`). The in-image hashes (`hashes_judge.txt`) differ from the previous fixed version only in `/tmp/eval_triangulation_coloring.py`.

**Limits.** Single-threaded test solutions only; multi-threaded solvers were not tested. Deadline-based solvers get more CPU at 4 CPUs under the fixed version, so their scores there are not comparable with the original grader's. The previous fixed version was run only in this job; it is not shipped.

## Convex-hull coverage, package v2.2 (2026-10-13, issue #57)

**Requirement.** The README gives "a **triangulation** of those points" and says a flip leaves "a valid triangulation". A triangulation of a point set covers the convex hull of the points with triangles whose vertices are the points and whose interiors are pairwise disjoint. For N points with h on the hull it therefore has exactly 2N−2−h triangles, and its boundary edges are the hull edges. The v2.1 inputs above have no overlaps, but 12 of 13 miss 1–3 triangles next to the hull: the shipped `delaunay.py` uses a finite super-triangle and drops hull triangles whose circumcircle reaches a super-triangle corner.

**Change.** `tools/src/delaunay.py` (grader and working image; sha256 `2681c12e…` → `ef137c0a…`) now returns `complete_hull(points, result)`: each pocket between the mesh boundary and a hull edge is triangulated by ear clipping, then Lawson flips with an exact in-circle test restore the Delaunay property. Every test is an exact integer determinant. Scripts and records below are in `evidence/scripts/triangulation_coloring_optimization/v2/`. `gen.py` is unchanged; the 13 inputs were regenerated with the same seeds, K, X, Y, P and Q (`regen_v22.out`). Before any pre-flip (K=0), the change adds 0–3 triangles per seed and changes none of the Bowyer–Watson triangles (`complete_hull_check.jsonl`). Hidden case 0000, which had no gap, is byte-identical to v2.1 (`d0558565…`). With the original `triangulation.py`, the v2.2 `delaunay.py` still reproduces the original hidden case 0000 byte for byte (`8e0c5efc…`). Judge and work image tags: `convex-flip-v2.2` (superseded: judge `convex-flip-v2.1`, work `convex-flip-v2`).

**Exact census** (`hull_check.py`: integer orientations and in-circle tests, `fractions.Fraction` areas; coverage = no overlapping interiors (exact separating-axis test) and triangle area sum equal to hull area). Local files: `hull_v21.jsonl`, `hull_v22.jsonl`. The same script, run with each image's own `python3` on the files inside the original, v2.1 and v2.2 images (`evidence/runs/triangulation-v22-geom`, `status: exit=0`), gives identical records.

| file | v2.1 M / 2N−2−h | v2.1 missing triangles | v2.1 area gap | v2.1 boundary / hull edges | v2.2 M / 2N−2−h | v2.2 area gap | v2.2 boundary = hull edges |
|---|---|---:|---:|---|---|---:|---|
| cases/0000 | 1007 / 1007 | 0 | 0 | 15 / 15 | 1007 / 1007 | 0 | yes |
| cases/0001 | 1004 / 1005 | 1 | 7499 | 18 / 17 | 1005 / 1005 | 0 | yes |
| cases/0002 | 1003 / 1005 | 2 | 44206 | 19 / 17 | 1005 / 1005 | 0 | yes |
| cases/0003 | 1006 / 1009 | 3 | 31527 | 16 / 13 | 1009 / 1009 | 0 | yes |
| cases/0004 | 1002 / 1005 | 3 | 87235 | 20 / 17 | 1005 / 1005 | 0 | yes |
| cases/0005 | 1006 / 1007 | 1 | 66539/2 | 16 / 15 | 1007 / 1007 | 0 | yes |
| cases/0006 | 1006 / 1007 | 1 | 3042 | 16 / 15 | 1007 / 1007 | 0 | yes |
| cases/0007 | 1007 / 1009 | 2 | 91609 | 15 / 13 | 1009 / 1009 | 0 | yes |
| cases/0008 | 1005 / 1007 | 2 | 187349/2 | 17 / 15 | 1007 / 1007 | 0 | yes |
| cases/0009 | 1000 / 1002 | 2 | 15246 | 22 / 20 | 1002 / 1002 | 0 | yes |
| sample_data/0000 | 1005 / 1006 | 1 | 35910 | 17 / 16 | 1006 / 1006 | 0 | yes |
| sample_data/0001 | 1006 / 1007 | 1 | 18954 | 16 / 15 | 1007 / 1007 | 0 | yes |
| sample_data/0002 | 1005 / 1007 | 2 | 18575 | 17 / 15 | 1007 / 1007 | 0 | yes |

Areas are exact (units of coordinate², not doubled). **Census before: 12 of 13 files have a gap (1 of 13 covers its hull). After: 0 of 13 have a gap; all 13 cover their convex hull exactly**, with 0 overlapping pairs, crossings, folds, duplicate, degenerate or non-manifold triangles, 0 vertices inside a triangle, V−E+F = 1 and all 512 vertices used. The original inputs fail coverage on all 13 files (overlaps; 12 of 13 also have M < 2N−2−h). On the 13 v2.2 files the fixed rule still equals the exact convex-quadrilateral test on every edge and allows no edge the original rule rejects (`rule_check_v22.jsonl`; 957–1,160 flippable edges per file).

**Paired run.** Three graders on the same submissions (`evidence/runs/triangulation-v22-paired`, `-rep2`, `-rep3`; `run.sh` there): the original grader (digest-pinned), the previous fixed version (v2.1, built from the package at `0a1bf837`) and the new fixed version (v2.2), original `eval_cmd`, `--network none --memory 4g`. In-image hashes (`result/out/hashes_judge.txt`): v2.2 differs from v2.1 only in `tools/src/delaunay.py` and cases 0001–0009 (judge) and in `delaunay.py` and the 3 samples (work image). Scores out of 100 via `normalize_v22.py` (EdgeBench's `score_sum` parser and `score_rescale.py`, unchanged anchors).

Full judge, v2.2 controls (identical at `--cpus 8` and `--cpus 4`). Lower raw results are better.

| submission | role | original raw | original out of 100 | previous fixed (v2.1) raw | v2.1 out of 100 | new fixed (v2.2) raw | v2.2 cases OK | v2.2 out of 100 |
|---|---|---:|---:|---:|---:|---:|---|---:|
| shipped `solution.py` (do nothing) | valid control | 6,092,430 | 0.055 | 6,092,622 | 0.054 | 6,108,380 | 10/10 | 0.000 |
| `greedy.py` (greedy recolour + greedy README-legal convex flips) | independent honest control | 866,166 | 48.87 | 863,058 | 48.95 | 874,742 | 10/10 | 48.66 |
| `nonconvex_flip.py` (do nothing + one README-forbidden non-convex flip per case) | **trigger** | 6,093,050 (10/10 accepted) | 0.052 | inf (0/10, WA "Invalid flip") | none | inf (0/10, WA "Invalid flip") | 0/10 | none (raw inf) |
| `wrong_count.py` (recolours vertex 1, claims C=0) | invalid control | inf (0/10 WA) | none | inf (0/10 WA) | none | inf (0/10 WA) | 0/10 | none (raw inf) |

The v2.2 do-nothing total (6,108,380) is 0.1% above the original `baseline` anchor (6,102,378), so it converts to 0.000 instead of 0.054; the anchors are unchanged (see the package README).

Same graders, swapped inputs (cases bind-mounted read-only over `cases/`, `--cpus 8`; `result/out/X/`):

| grader + inputs | do nothing | greedy | nonconvex_flip | wrong_count |
|---|---:|---:|---|---|
| original grader on the v2.2 cases | 6,108,380 | 874,742 | 6,105,916, 10/10 accepted | inf (10 WA) |
| v2.1 grader on the v2.2 cases | 6,108,380 | 874,742 | inf (10 WA "Invalid flip") | inf (10 WA) |
| v2.2 grader on the v2.1 cases | 6,092,622 | 863,058 | inf (10 WA "Invalid flip") | inf (10 WA) |

So every score change from v2.1 to v2.2 comes from the inputs: the v2.1 and v2.2 grader code give identical results on the same cases, and the original grader still accepts the forbidden flip on the new inputs.

CPU-quota arms (`result/out/B/summary.txt`), honest `greedy.py` control followed by fixed work:

| Solution | CPUs | Original grader | Previous fixed (v2.1) | New fixed (v2.2) |
| --- | ---: | --- | --- | --- |
| `cpu0` (control alone) | 4 | 10 OK, 866,166 | 10 OK, 863,058 | 10 OK, 874,742 |
| **`cpu20` (20 s CPU per case)** | 4 | **2 OK, 8 TLE, inf (no score)** | 10 OK, 863,058 | **10 OK, 874,742 (48.66)** |
| **`cpu28` (28 s CPU per case)** | 4 | **2 OK, 8 TLE, inf** | 10 OK, 863,058 | **10 OK, 874,742** |
| `wall25` (works until 25 s wall clock) | 4 | 10 OK, 866,166 | 10 OK, 863,058 | 10 OK, 874,742 |
| `spin40` (bad control, 40 s CPU per case) | 4 | 10 TLE, inf | 10 TLE, inf | 10 TLE, inf |
| `cpu20` | 8 | 10 OK, 866,166 | 10 OK, 863,058 | 10 OK, 874,742 |

Solver-visible loop (work images, `result/out/W/`): SAMPLE_TOTAL do nothing 1,780,251 / 1,802,171 / 1,817,733 and greedy 263,500 / 258,183 / 237,515 (original / v2.1 / v2.2); `nonconvex_flip` 1,780,471 accepted by the original tester and 3 × `wrong answer: Invalid flip` under v2.1 and v2.2. Rule only (`result/out/R/`): on the N=4 reflex input and one non-convex flip on each v2.2 case, the original tester accepts all 11 (`Score = 41` on N=4) and the v2.1 and v2.2 testers reject all 11 (`Invalid flip`).

**Effect on a good-faith solver.** A missing hull triangle is never counted in U, and the mesh edges that border it are boundary edges, which cannot be flipped. On v2.1 inputs a solver therefore optimised a slightly different instance from the documented one, but every solver was scored by the same rule and repeatably; the paired runs show no wrong or unrepeatable score from the gap itself. The v2.2 inputs are new instances (cases 0001–0009 and the samples), so v2.2 scores are not comparable with v2.1 scores: the honest greedy control moves from 48.95 to 48.66 out of 100.

**Limits.** The ear-clipping fill is one valid choice among several; Lawson flips make the K=0 mesh exactly Delaunay (0 non-locally-Delaunay edges at K=0), so the K=0 mesh is the Delaunay triangulation up to cocircular ties. The census checks the shipped files, not every possible seed.

## Verdict

Trigger: v1 wrong (accepts forbidden flip), v2 right (rejects). Valid controls: accepted in both,
normalized score unchanged within 0.08 (v2.1) and 0.21 (v2.2, new instances), against the original. Invalid control: rejected in both. CPU-quota addition: at 4 CPUs the 20 s and 28 s fixed-work solutions go from 8 TLE (no score) to 10 OK; the control, deadline and 8-CPU arms keep their results; the 40 s bad control times out under both; all earlier controls reproduce exactly. Convex-hull coverage (v2.2): all 13 inputs now cover their convex hull exactly (before: 12 of 13 had gaps); the v2.1 and v2.2 graders give identical results on the same inputs. **Accepted.**

## Repeatability (2026-10-13)

| job | arms | runs | identical? |
| --- | --- | --- | --- |
| `…-v2-paired`, `-rep2`, `-rep3` | the four flip-rule controls (full judge) | 3 | yes (earlier) |
| `evidence/runs/triangulation-v2-paired-cpu`, `-rep2`, `-rep3` | the six CPU-quota arms × original, earlier fixed and current fixed version (18 results) | 3 | yes |
| `evidence/runs/triangulation-v2-paired-cpu-controls`, `-rep2`, `-rep3` | the four flip-rule controls against the current fixed version, at 8 and 4 CPUs (16 results) | 3 | yes |
| `evidence/runs/triangulation-v22-paired`, `-rep2`, `-rep3` (package v2.2) | the four flip-rule controls × original, v2.1 and v2.2 graders at 8 and 4 CPUs (24 results), the swapped-input arms (12), the six CPU-quota arms × three graders (18), the solver-visible loop (9) and the rule-only checks (3) | 3 | yes |

Each rerun used the job's `run.sh` and inputs unchanged, on a fresh E2B worker (for the v2.2 jobs, `-rep2` and `-rep3` add only a retry loop around `docker pull`; the first `-rep2` attempt failed its image pull with a TLS error before any arm ran and is kept as `triangulation-v22-paired-rep2-pullfail`). Every rerun has `status: exit=0`, and its worker was killed. Every arm gives the same OK/TLE/WA/RE counts and TOTAL in all three runs, and the controls give the same `cases_ok`, validity and normalized score. Only wall times differ. Staged inputs, removed after collection: the materialized `pkg/files/` and `pkgprev/files/` (evaluator sha256 `082d72b2…`, `triangulation.py` `8b5b9cbb…`, cases equal to run 1's `hashes_judge.txt`), and the shipped `donothing.py`, an image file.

**v2.2 runs in detail.** All three jobs `status: exit=0` in `evidence/runs/ledger.jsonl` (1024, 1044 and 1044 s), workers killed. `result/normalize.jsonl` (cases OK, raw total, score out of 100 for every full-judge and swapped-input arm) is byte-identical across the three runs; `result/out/B/summary.txt` agrees except for wall times; the solver-visible and rule-only logs (`W/`, `R/`) and the in-image hashes are byte-identical. Only timing varies: the `wall25` arm's mean CPU per case under v2.2 was 24.98, 24.98 and 24.93 s, and the bad control took 90.6–90.7 s to grade. The in-image census step of these jobs (`result/out/geom/`) did not run: its loop split the digest-pinned image names at `:` (`docker: invalid reference format`, exit 125); it was rerun as the separate job `evidence/runs/triangulation-v22-geom` (`status: exit=0`), whose records equal the local census. Staged inputs, removed after collection: `pkg/files/` (v2.2, sha256 equal to `../source-lock.json` `materialize.outputs`) and `pkgprev/files/` (v2.1, equal to the lock at `0a1bf837`).
