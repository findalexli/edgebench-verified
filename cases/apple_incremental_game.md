# Apple Incremental Game (`apple_incremental_game`)

**Outcome:** Fixed. <mark>On the publisher's 4-CPU grader, a valid solution using more than about 15 s of CPU per case times out, although the README promises 30 s per case, and each timed-out case scores 0. The fixed version runs at most as many cases at once as the grader has CPUs. The lower end of the score scale agrees with an independent simulation. We did not check the upper reference points, and the grader does not enforce the 1 GB memory limit for each solution.</mark>

## What the task asks

The task is adapted from an AtCoder Heuristic Contest problem (AHC058), a machine-production incremental game. The task text says: "Your solution is scored on **50 fixed test cases**. Final score = sum of individual case scores. **Higher is better.**" The score for one case is `round(1e5·log2 S)` (README:34-36). The task is in the Combinatorial Optimization category.

## What we checked

We found one scoring defect, the CPU dependence of the time limit, and the fixed version removes it. We checked these parts:

- The grader converts the raw result (before conversion to 0–100) with the `piecewise_max` method. Its reference point for 0 is 45,000,000 (900,000 per case, that is S = 2⁹). The rank-1 point, 282,791,094, maps to 80, and 100 corresponds to 289,952,856.4 (`tasks/apple_incremental_game.json`, `judge.rescale`; `sforge/harness/score_rescale.py`, `piecewise_max`). The shipped do-nothing starting solution has S = K = 1, so it scores a raw result of 0, which maps to 0. A simple greedy simulator that we wrote independently reaches a raw result of **237,518,875** (4.75M per case), which maps to **17.7** out of 100. That is below the reference point for the 30th-ranked level (5.25M per case), the expected order. This checks only the lower end of the scale.
- We did not check the upper reference points. The rank30, rank1 and 100 points (262,328,915.67, 282,791,094 and 289,952,856.42) are not whole numbers, but ×3 and ×12 give whole numbers (786,986,747 and 3,479,434,277), which suggests someone rescaled them from another case count. We did not check where they come from, or whether 100 can be reached on these 50 cases. The sister task Treant, which uses the same evaluator code, has a rank-1 point 3.58 times its attainable maximum (`evidence/reviews/_game-tasks-correctness.md`, section 8).
- On a 4-CPU grader the 30 s per case shrinks to about 15 s of CPU (fixed). The README promises "Time limit | 30 seconds / test case" (line 71). The limit is wall-clock time (`TIME_LIMIT = 30`, `/tmp/eval_apple_incremental_game.py` line 9), the grader runs 8 cases at once (`max_workers=min(8, len(case_files))`, line 45), and a timed-out case scores 0 (line 37). The task sets no CPU count. In EdgeBench's leaderboard configuration `examples/all-tasks-k8s/experiment.yaml` (quoted in [`evidence/impact/edgebench-leaderboard-config.md`](../evidence/impact/edgebench-leaderboard-config.md)) (sha256 `d9d299794ba946cae8d2b7f68a7879a35bb8565d95e78107edf79802993643be`), the grader inherits `judge_cpu_limit: 4`, so each of the 8 cases gets about half a CPU. We measured this on the original grader at `--cpus 4` (`evidence/runs/apple_incremental_game-cpu4v8-a/result/out/summary.txt`, `-b`; repeated in `apple_incremental_game-v2-paired`) with a plain greedy control we wrote (TOTAL 99,714,418, 5.04 out of 100). We did not use the shipped baseline, because it scores 0 on every case and would hide the difference between OK and TLE. With 12 or 14 s of extra CPU work per case the control passes 50/50. With 20 s, 48 of 50 cases time out on both workers and the total falls to 3,955,266, which is 0 out of 100. At `--cpus 8` all cases pass with 99,714,418. A solution that stops at a 25 s wall-clock deadline gets a mean of 13.00 s of CPU per case at 4 CPUs and 24.94 s at 8 CPUs.
- The evaluator code adds no randomness. The per-case score comes from the tester program `tools/bin/tester`. It scored our greedy control's outputs in the CPU runs (99,714,418 in every run), but we did not examine its code.

The task text (README) states a 1 GB memory limit, but the grader does not enforce it for each solution.

The note says that the advertised 1 GB memory policy is not enforced per solution.

The shipped note does not state the source of the upper reference points (rank30, rank1 and 100), and we did not check it.

## How much it matters

Under the original grader at the publisher's 4 CPUs, a solution using more than about 15 s of CPU per case loses those cases (0 each). Losing 48 of 50 cases takes nearly the whole score. We measured 5.04 → 0 for our control; for stronger solvers this follows from the case count, and we did not measure it. The fixed version scores these cases. A solution that stops at a wall-clock deadline gets about twice the CPU per case under the fixed version (mean 13.00 s → 24.99 s for the 25 s deadline solution). We did not measure how much that changes its score.

We found no score effect from the lower end of the scale. We did not check the upper reference points, so we cannot rule out an effect from them. The memory note had no score effect on a solution that follows the rules and concerns only users who rely on the stated limit.

## The fix

The fixed version (`repairs/apple_incremental_game-v2/`) changes how many cases `/tmp/eval_apple_incremental_game.py` runs at once. A new function `cpu_quota_workers()`, the same as in `repairs/grid_turing_robot-v2/`, reads the grader's CPU quota from the cgroup (`cpu.max`, or the cgroup v1 quota and period) and rounds it down to whole CPUs. It falls back to `os.cpu_count()` when there is no quota and keeps the result between 1 and 8. The pool becomes `ProcessPoolExecutor(max_workers=min(cpu_quota_workers(), len(case_files)))`. `docker run --cpus N` and the publisher's k8s backend both set this quota. At `--cpus 1/2/3/4/8` the fixed grader runs 1/2/3/4/8 cases at once (`apple_incremental_game-v2-paired/result/out/v2_workers.txt`). In the task JSON only `judge.image_tag` changes. The 30 s limit, the 600 s `eval_timeout`, the README, the tester, the cases and the score scale stay as they were. With 8 or more CPUs the fixed grader runs 8 cases at once, exactly as the original does.

We ran the same solutions on both graders at `--cpus 4`, with one pair at `--cpus 8` (`evidence/runs/apple_incremental_game-v2-paired/result/out/summary.txt`; `repairs/apple_incremental_game-v2/paired/results.md`):

| Solution | CPUs | Original grader | Fixed version |
| --- | ---: | --- | --- |
| greedy control, no extra work | 4 | 50 OK, TOTAL 99,714,418 (5.04) | 50 OK, TOTAL 99,714,418 (5.04) |
| **20 s of CPU per case** | 4 | **2 OK, 48 TLE, TOTAL 3,955,266 (0.00)** | **50 OK, TOTAL 99,714,418 (5.04)** |
| **28 s of CPU per case** | 4 | **2 OK, 48 TLE, TOTAL 3,955,266 (0.00)** | **50 OK, TOTAL 99,714,418 (5.04)** |
| works until a 25 s wall-clock deadline | 4 | 50 OK, TOTAL 99,714,418; mean 13.00 s CPU per case | 50 OK, TOTAL 99,714,418; mean 24.99 s CPU per case |
| 40 s of CPU per case (bad control) | 4 | 50 TLE, TOTAL 0 | 50 TLE, TOTAL 0 |
| 20 s of CPU per case | 8 | 50 OK, TOTAL 99,714,418 | 50 OK, TOTAL 99,714,418 |

Under the fixed version the slowest 28 s case took 28.02 s from start to end (`result/out/timing_summary.txt`). Grading at 4 CPUs takes at most ⌈50/4⌉ = 13 rounds of 30 s. The bad control, which times out on every case, took 390.8 s (original: 210.7 s), inside the task's 600 s `eval_timeout`. The 390.8 s is that measured run, not a computed bound.

At 8 or more grader CPUs the two versions grade the same way, so their scores are comparable there. At 4 CPUs a deterministic solution that finished every case in time under the original gets the same output and score under the fixed version, and a solution needing about 15 to 30 s of CPU per case is scored on those cases instead of getting 0. A solution that searches until a wall-clock deadline gets about twice the CPU per case, so its scores under the two graders at 4 CPUs are not comparable. Per-case CPU never decreases under the fixed version.

Two notes still ship with the fixed version. The grader does not enforce the 1 GB memory limit for each solution, and we did not check the source and reachability of the upper reference points.

## How we checked it

- We read the grader file `eval_apple_incremental_game.py` from the original public image. It uses the same code as the Treant task, with `TIME_LIMIT=30` and the `piecewise_max` score scale.
- We ran the CPU runs and the paired run on E2B. Valid solutions doing 12 to 28 s of CPU work per case, a 25 s wall-clock-deadline solution and a 40 s bad control ran on the original grader at `--cpus 4` and `--cpus 8` (`evidence/runs/apple_incremental_game-cpu4v8-a`, `-b`; ledger jobs `cpu4v8-games-a`, `-b`) and side by side on the original and fixed graders (`evidence/runs/apple_incremental_game-v2-paired`). Each job ended with `status: exit=0`, in the digest-pinned grader image with `--network none --memory 4g`. Each solution runs our greedy control (a level-0 return-on-investment greedy), does its extra work, prints the control's answer, and logs its own start, end and CPU time per case (`result/out/timing/`).
- We ran an independent greedy simulator, which looks one step ahead and follows the rules in the task text, on all 50 shipped cases. It is not the original tester program.
- We checked the arithmetic on the time budget and the score scale (`evidence/scripts/_game-tasks-correctness/check_arith.py`). The greedy total of 237,518,875 is entered there as an observed value; the simulator's own output is not saved in this repository.

## Limits

- The fixed grader reads its CPU quota from the cgroup (`cpu.max`). We tested this with `docker run --cpus` only, not inside a Kubernetes pod, which is the backend EdgeBench's leaderboard settings use.
- We made no AI model or solver runs. The effects shown come only from test submissions and counterexamples that we wrote.
- The greedy check uses an independent simulator instead of the original `tools/bin/tester`. Scoring one greedy output with the original tester would close this gap.
- We ran the original and fixed graders inside the digest-pinned grader image only for the CPU measurements and the paired run, at 4 and 8 CPUs, on E2B workers with 8 vCPUs. We did not test 3, 5, 6 or 7 CPUs.
- The CPU test solutions are single-threaded, doing either fixed CPU work or work until a 25 s wall-clock deadline. We did not test multi-threaded solvers.
- Deadline-based solvers get about twice the CPU per case under the fixed version at 4 CPUs, so their scores under the two graders are not comparable. We did not measure how much their scores change.
- With fewer than 3 grader CPUs, the 600 s `eval_timeout` becomes the binding limit instead of the 30 s per case (25 rounds × 30 s = 750 s at 2 CPUs). The grader prints its results only after every case has finished, so a submission that reaches the `eval_timeout` loses its whole output and scores 0. Below 3 CPUs the fixed version can therefore score lower than the original for a solution that times out on most cases (derived from the code, not run). The grader rounds the quota down, so 2.5 CPUs run 2 cases at once.
- Without a cgroup quota the fixed grader falls back to `os.cpu_count()`, which counts all host CPUs and not only the ones the grader may use (`os.sched_getaffinity`). Under a CPU-set limit with no quota it can still run more cases at once than it has CPUs.
- We rebuilt the package from scratch on a clean machine (`evidence/runs/materialize-check-g1`, `status: exit=0`). `materialize.sh` ran unchanged, the output matched the lock, and the built image holds the locked file.
- We did not check the origin and reachability of the upper reference points.

## Reproduce

- Grader image: `seededge/edgebench.judge.apple_incremental_game@sha256:d3af7b43331078bb3ef29fab70c502cbb72d0e08d52e59cf9bdb044105d63f39`; `/tmp/eval_apple_incremental_game.py` sha256 `c33f5257…d70c`.
- Fixed version: `repairs/apple_incremental_game-v2/` (`materialize.sh`, `repair.patch`, `source-lock.json`; fixed grader sha256 `ba31e840…1931`). Paired run: `repairs/apple_incremental_game-v2/paired/run.sh` (as run: `evidence/runs/apple_incremental_game-v2-paired/run.sh`); CPU runs on the original grader: `evidence/runs/apple_incremental_game-cpu4v8-a/run.sh`, `-b`.

- Review: `evidence/reviews/_game-tasks-correctness.md`, section 9.
- Greedy simulator: `evidence/scripts/_game-tasks-triage/apple/greedy_lookahead.py`.
- Original grader: the grader-image file `eval_apple_incremental_game.py` (sha256 in [the review](../evidence/reviews/_game-tasks-correctness.md)). No copy is published in this repository.
