# Grid Turing Robot (`grid_turing_robot`)

**Outcome:** Fixed. <mark>On the publisher's 4-CPU grader, a valid solution using more than about 15 s of CPU per case times out, although the README promises 30 s per case, and one timeout voids the whole submission. The fixed version runs at most as many cases at once as the grader has CPUs. Two notes remain: an offset in the score scale's starting point (2.84 points) and the unstated rule that one failed case voids the submission (about 20 points).</mark>

![Line chart of clock time per test case against computing time per case. At 8 CPUs clock time equals computing time from 12 to 28 s. At 4 CPUs 12 s of computing takes 24 s and 14 s takes 28 s; 16, 20, 24 and 28 s are marked as timed out at the 30 s limit, with 48 of 50 cases timed out and no score. A note says the fixed checker passes the 16 s and 28 s solutions on all 50 cases with 19.80 out of 100.](figures/grid_turing_robot.svg)

*On EdgeBench's official 4-CPU setting, a valid Grid Turing Robot solution that needs more than about 15 s of computing per test case gets no score, although the instructions promise 30 s per case. The agent writes a rule table that steers a robot over a grid; the checker runs 8 cases at once, so on 4 CPUs each case gets half a CPU and takes twice as long by the clock, and one timed-out case voids the whole submission. Test solutions needing 16 s and 28 s per case timed out on 48 of 50 cases under the original checker and scored 19.80 out of 100 under the fixed one, which runs no more cases at once than it has CPUs.*

## What the task asks

The solver writes a rule table, like the transition table of a Turing machine, that drives a robot over a grid. The task text says: "Your solution is scored on **50 fixed test cases**. Final score = sum of individual case scores. **Lower is better.**" The README gives the score for one case as "If V = K: Score = C + Q", with the penalty "If V < K: Score = 2N^4 + (K − V) × N^2", and a "Time limit | 30 seconds / test case". Category: Combinatorial Optimization.

## What goes wrong

The scoring rules are implemented correctly. The issues are about edge conditions; (c) is fixed in a new version, (a) and (b) ship as a note.

**(a) One failed case voids the submission.** The task text does not say this. If a single case crashes, times out or prints malformed output, that case gets an infinite score, so `TOTAL_SCORE` is `inf`. EdgeBench's harness keeps such a result (`valid: true`) with raw score `inf`, gives it no score out of 100 (`rescale_score` returns None for a non-finite total, `sforge/harness/score_rescale.py:75-76`), and prefers any finished submission to it under `minimize`.

| Solution (all honest) | Grader result per case | TOTAL_SCORE | Scored by the harness | Score out of 100 |
|---|---|---|---|---|
| `good_stepstate` (known to be good) | 50 OK | 94,092 | yes | 19.80 |
| `fail_partial` (well-formed; route cut in half on case 0000) | 50 OK | 202,310 | yes | 19.56 |
| `fail_crash` (raises an error on case 0000 only) | 0000 RE score=inf | inf | **no** (raw `inf`) | None |
| `fail_tle` (sleeps 40 s on case 0000) | 0000 TLE score=inf | inf | no (raw `inf`) | None |

A failure never helps a solver, because lower is better. A failed case is not dropped and is not counted as 0.

**(b) Offset in the starting point of the score scale.** The configured reference point for 0 (the baseline) is 9,025,986. The shipped do-nothing starting solution actually totals 7,744,909 on the 50 grading cases. It therefore scores **2.84** out of 100 instead of 0.

**(c) The 30 s per case shrinks to about 15 s of CPU on a 4-CPU grader (fixed).** Cases run eight at a time (`ProcessPoolExecutor(max_workers=min(8, len(case_files)))`) under a 30 s wall-clock limit, and the task sets no `cpu_limit`. In EdgeBench's leaderboard configuration `examples/all-tasks-k8s/experiment.yaml` (quoted in [`evidence/impact/edgebench-leaderboard-config.md`](../evidence/impact/edgebench-leaderboard-config.md)) (sha256 `d9d299794ba946cae8d2b7f68a7879a35bb8565d95e78107edf79802993643be`, headed "OFFICIAL EDGEBENCH LEADERBOARD SETTING"), `grid_turing_robot: {}` inherits `judge_cpu_limit: 4`. The k8s backend sets this as the grader pod's CPU request and limit (`sforge/harness/backend/k8s_backend.py:214-224`). Eight cases on 4 CPUs get about half a CPU each, so a single-threaded solution that needs more than about 15 s of CPU per case exceeds the 30 s wall-clock limit, although the README promises "30 seconds / test case", and by (a) one such case voids the submission.

Measured on the original grader at `--cpus 4` (`evidence/runs/grid_turing_robot-cpu4v8-a/result/out/summary.txt`, repeated in `grid_turing_robot-v2-paired`):

| Valid solution (known-good output, preceded by fixed work) | 4 CPUs | 8 CPUs |
|---|---|---|
| 12 or 14 s of CPU per case | 50 OK, TOTAL 94,092 | 50 OK, TOTAL 94,092 |
| 16, 20, 24 or 28 s of CPU per case | **2 OK, 48 TLE, TOTAL `inf` (no score)** | 50 OK, TOTAL 94,092 |
| works until a 25 s wall-clock deadline | 50 OK, TOTAL 94,092; mean 13.03 s of CPU per case | 50 OK, TOTAL 94,092 |

(8-CPU column: `evidence/runs/grid_turing_robot-cpu4v8-b/result/out/summary.txt`. CPU per case: `grid_turing_robot-v2-paired/result/out/timing/c4-wall25-v1/`.) An earlier local run at `--cpus 2` gave 48 TLE already for 12 s per case (`evidence/scripts/grid_turing_robot/native_cpus2/`).

## How much it matters

- (a) At most about 20 points out of 100 for the affected submission, compared with charging that case its smallest penalty. The effect is 0 if an earlier submission in the run was valid, because the run keeps its best valid submission.
- (b) At most 2.84005 points (≈ 2.84; the exact maximum, proved in Lean), and only between the reference point for 0 and the reference point for the 30th-ranked level (rank30), that is, the 0–20 band.
- (c) Up to the full score for a valid solution using between about 15 and 30 s of CPU per case on the publisher's 4-CPU grader: 16 and 28 s per case void the submission under the original grader and pass under the fixed version (`evidence/runs/grid_turing_robot-v2-paired/result/out/summary.txt`). A solution that stops at a wall-clock deadline gets about twice the CPU per case under the fixed version (mean 13.03 s → 24.91 s for the 25 s control); how much that changes its score is not measured. A solver sees the per-case TLE results after each submission, and the run keeps its best valid submission, so a run loses its score only if it never submits a faster valid solution.

## The fix

The fixed version (`repairs/grid_turing_robot-v2/`) changes how many cases the grader `/tmp/eval_grid_turing_robot.py` runs at once. A new function `cpu_quota_workers()` reads the grader's CPU quota from the cgroup (`cpu.max`, or the cgroup v1 quota and period), rounds it down to whole CPUs, falls back to `os.cpu_count()` when there is no quota, and keeps the result between 1 and 8. The pool becomes `ProcessPoolExecutor(max_workers=min(cpu_quota_workers(), len(case_files)))`. `docker run --cpus N` and the publisher's k8s backend both set this quota; at `--cpus 1/2/4/8` the fixed grader runs 1/2/4/8 cases at once (`grid_turing_robot-v2-paired/result/out/v2_workers.txt`). The task JSON changes only `judge.image_tag`. The 30 s limit, the README, the tester, the cases, the parser and the score scale are unchanged, and so is the rule in (a). With 8 or more CPUs the fixed grader runs 8 cases at once, exactly as the original.

These notes still ship with the fixed version:

1. The configured baseline (9,025,986) is higher than the shipped baseline's actual 7,744,909, so the shipped baseline earns 2.84 points instead of 0.
2. One crashed, timed-out or malformed case makes the total `inf`, so the whole submission gets no score.

Paired run at `--cpus 4` (one pair at `--cpus 8`), same solutions on both graders (`evidence/runs/grid_turing_robot-v2-paired/result/out/summary.txt`; `repairs/grid_turing_robot-v2/paired/results.md`):

| Solution | CPUs | Original grader | Fixed version |
| --- | ---: | --- | --- |
| known-good, no extra work | 4 | 50 OK, TOTAL 94,092 (19.80) | 50 OK, TOTAL 94,092 (19.80) |
| 12 s of CPU per case | 4 | 50 OK, TOTAL 94,092 | 50 OK, TOTAL 94,092 |
| **16 s of CPU per case** | 4 | **2 OK, 48 TLE, TOTAL `inf` (no score)** | **50 OK, TOTAL 94,092 (19.80)** |
| **28 s of CPU per case** | 4 | **2 OK, 48 TLE, TOTAL `inf` (no score)** | **50 OK, TOTAL 94,092 (19.80)** |
| works until a 25 s wall-clock deadline | 4 | 50 OK, TOTAL 94,092; mean 13.03 s CPU per case | 50 OK, TOTAL 94,092; mean 24.91 s CPU per case |
| 40 s of CPU per case (bad control) | 4 | 50 TLE, TOTAL `inf` | 50 TLE, TOTAL `inf` |
| 20 s of CPU per case | 8 | 50 OK, TOTAL 94,092 | 50 OK, TOTAL 94,092 |

Under the fixed version the slowest 28 s case took 28.34 s from start to end (`result/out/timing/c4-cpu28-v2/`). Grading at 4 CPUs takes at most ⌈50/4⌉ = 13 rounds of 30 s; the bad control took 390.9 s (original: 210.8 s), inside the task's 600 s `eval_timeout`.

**Are scores comparable?** At 8 or more grader CPUs the two versions are the same grader. At 4 CPUs a deterministic solution that finished every case in time under the original gets the same output and score under the fixed version, and a solution needing about 15 to 30 s of CPU per case is scored instead of voided. A solution that searches until a wall-clock deadline gets about twice the CPU per case, so its score under the two graders is not comparable. Per-case CPU never decreases under the fixed version.

## How we checked it

- **Original grader in the original public image, pinned by digest.** The unchanged grader ran in the grader image with `docker run --network none --memory 2g --cpus 4`, and the repository harness graded the logs. The solution with fixed CPU work was also run at `--cpus 2` and `--cpus 8`.
- **CPU runs and paired run on E2B.** Valid solutions doing 12 to 28 s of CPU work per case, a 25 s wall-clock-deadline solution and a 40 s bad control ran on the original grader at `--cpus 4` and `--cpus 8` (`evidence/runs/grid_turing_robot-cpu4v8-a`, `-b`) and side by side on the original and fixed graders (`evidence/runs/grid_turing_robot-v2-paired`), each job `status: exit=0`. Each solution logs its own start, end and CPU time per case (`result/out/timing/`), which does not affect grading.
- **Independent implementation.** A parser, simulator and scorer were written from the README text alone, without importing the task's verifier. A comparison over 3,000 random rule tables on the 50 grading cases found 0 disagreements. Both implementations give a sum of 94,092 for the known-good solution on all 50 cases.
- **Exhaustive search.** Every rule table with C+Q ≤ 5 was searched on tiny boards to confirm the bound on the minimum cost.
- **Data checks.** All 50 cases are valid: N and K are in range, walls are well-formed, the grid is fully connected, targets are distinct, and X ≤ T ≤ 2X by an independent breadth-first search (BFS).
- **Seed search.** No grading case matches generator output for seeds 0..60,000. The cases are therefore not in the 0..10000 range that solvers may use locally.
- **Formal check (Lean 4).** `GridTuringBaseline.lean` proves that the do-nothing solution scores exactly 6405385/2255374 ≈ 2.84005 under the configured scale, and that the extra credit from the misplaced reference point is between 0 and 2.84005 for every raw total, and 0 below rank30. The 50 per-case scores are taken from the saved grader log. Note: `evidence/formal/notes/grid_turing_robot.md`.

## Limits

- The fixed grader reads its CPU quota from the cgroup (`cpu.max`). This was tested with `docker run --cpus` only, not inside a Kubernetes pod, which is the backend EdgeBench's leaderboard settings use.
- Without a cgroup quota the fixed grader falls back to `os.cpu_count()`, which counts all of the host's CPUs, not the ones the grader may use (`os.sched_getaffinity`). Under a CPU-set limit with no quota (for example `docker run --cpuset-cpus`), or where the pod cannot see its own `cpu.max`, it can still run more cases at once than it has CPUs, as the original does. Using the affinity count would need a new paired run, so it is not changed here.
- No AI model or solver runs were made. Score effects are shown only on test submissions and counterexamples that we wrote.
- Runs of the original grader used local Docker at `--cpus 4`, `--cpus 2` and `--cpus 8`, with `--memory 2g`; the CPU runs and the paired run used E2B workers with 8 vCPUs, `--memory 4g` and `--cpus 4` or `--cpus 8`. 3, 5, 6 and 7 CPUs were not tested.
- The CPU test solutions are single-threaded: fixed CPU work, or work until a 25 s wall-clock deadline. Multi-threaded solvers were not tested.
- Deadline-based solvers get about twice the CPU per case under the fixed version at 4 CPUs, so their scores under the two graders are not comparable. How much their scores change is not measured.
- With fewer than 3 grader CPUs the 600 s `eval_timeout` binds before the 30 s per case: at 2 CPUs, 25 rounds × 30 s = 750 s, so only about 24 s per case is usable (the original gives about 7.5 s of CPU per case there). The quota is rounded down: 2.5 CPUs run 2 cases at once.
- Only simple honest solutions were tested. Whether the reference point for 100 (rank1 = 1,575) is achievable was not checked, and the sources of the rank1 and rank30 reference points were not traced.
- The random tables in the comparison produced only partial routes. Agreement on full routes rests on the known-good solution and one half-route case.
- The seed search covered gen.py seeds 0..60,000 only.

## Reproduce

- Grader image digest: `sha256:f67864ad75a3…`.
- Fixed version: `repairs/grid_turing_robot-v2/` (`materialize.sh`, `repair.patch`, `source-lock.json`; fixed grader sha256 `285229ee…3a22`). Paired run: `repairs/grid_turing_robot-v2/paired/run.sh` (as run: `evidence/runs/grid_turing_robot-v2-paired/run.sh`); CPU runs on the original grader: `evidence/runs/grid_turing_robot-cpu4v8-a/run.sh`, `-b`.
- Runs of the original grader: `evidence/scripts/grid_turing_robot/run_native.sh`, then `grade.py` (output in `native/grade_out.txt`; CPU runs in `native_cpus2/` and `native_cpus8/`). `native_cpus8/grade_out.txt` holds two `cpu12.log` lines: the first (`valid=True`, raw `inf`, no normalized score) grades the 2-CPU log, the second (`valid=True`, 19.8014) the 8-CPU log.
- Independent implementation, data checks and tiny-board search: `evidence/scripts/grid_turing_robot/oracle.py` (outputs `data_out.txt` and `brute_out.txt`).
- Comparison over random rule tables: `evidence/scripts/grid_turing_robot/fuzz_agree.py` (output `fuzz_out.txt`).
- Seed search: `evidence/scripts/grid_turing_robot/seeds_header.py` (output `seeds_header_out.txt`).
