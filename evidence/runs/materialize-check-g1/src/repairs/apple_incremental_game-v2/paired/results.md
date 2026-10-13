# apple_incremental_game v2: paired results

**Verdict: accepted.** At 4 grader CPUs, valid solutions using 20 or 28 s of CPU per case time out on 48 of 50 cases under the original grader (total 3,955,266, 0 out of 100) and pass 50/50 under the fixed version with the same total as every other valid control (99,714,418, 5.04 out of 100). The honest control alone, a 25 s wall-clock-deadline solution and the 8-CPU pair give the same totals under both. A solution that spends 40 s per case times out on all 50 cases under both.

## Run

E2B job `evidence/runs/apple_incremental_game-v2-paired` (`run.sh`, `arms.txt`, `task.env`; copies in this directory), one worker with 8 vCPUs and 7.9 GB RAM (`result/out/env.txt`), `status: exit=0`, 2449 s, worker killed (`result/worker.json`, ledger `evidence/runs/ledger.jsonl`). Every arm ran the task's original `eval_cmd` (`cd /home/workspace/apple_incremental_game && python3 /tmp/eval_apple_incremental_game.py`) with `--network none --memory 4g --cpus N`, one container at a time, with the solution bind-mounted read-only over `solution.py`.

- **Original grader:** `seededge/edgebench.judge.apple_incremental_game@sha256:d3af7b43…3f39`; `/tmp/eval_apple_incremental_game.py` sha256 `c33f5257…d70c`, `max_workers=min(8, len(case_files))` (`result/out/eval_sha.txt`).
- **Fixed version:** built in the worker from this package's Dockerfile; `/tmp/eval_apple_incremental_game.py` sha256 `ba31e840…1931`, the `materialize.outputs` value in `source-lock.json`.
- **What the fixed grader computes** (`result/out/v2_workers.txt`): `--cpus 1/2/3/4/8` give `cpu.max` `100000/…/800000 100000` and 1/2/3/4/8 cases at once.
- **Solutions** (`sol/`, `base/`; sha256 in `result/out/solutions_sha.txt`). `base/base.py` is our honest control (a level-0 return-on-investment greedy that follows the README rules), the same file as in `apple_incremental_game-cpu4v8-a`/`-b`; the shipped baseline scores 0 on every case, which would hide the difference between OK and TLE. Each `sol/*.py` is a wrapper that runs the control, then works until the process has used W CPU-seconds in total (`cpuW`) or until W seconds of wall clock (`wall25`), then prints the control's answer, so every arm prints the same valid answer. `cpu0.py` is the control alone; `spin40.py` spends 40 s of CPU, more than the 30 s limit, and must time out. Each wrapper writes its start and end time and CPU used to a per-arm directory (`result/out/timing/`); a process killed by the grader leaves no end line.

## Results

Source: `evidence/runs/apple_incremental_game-v2-paired/result/out/summary.txt`; per-case lines in `result/out/logs/<arm>.log`; per-case times in `result/out/timing_summary.txt`. Score out of 100 from the task's `piecewise_max` scale via `sforge/harness/score_rescale.py`.

| Solution | CPUs | Original grader | Fixed version |
| --- | ---: | --- | --- |
| `cpu0` (honest control alone) | 4 | 50 OK, TOTAL 99,714,418 (5.04), 1.0 s | 50 OK, TOTAL 99,714,418 (5.04), 1.0 s |
| **`cpu20` (20 s CPU per case)** | 4 | **2 OK, 48 TLE, TOTAL 3,955,266 (0.00)**, 200.8 s | **50 OK, TOTAL 99,714,418 (5.04)**, 261.1 s |
| **`cpu28` (28 s CPU per case)** | 4 | **2 OK, 48 TLE, TOTAL 3,955,266 (0.00)**, 208.8 s | **50 OK, TOTAL 99,714,418 (5.04)**, 365.0 s |
| `wall25` (works until 25 s wall clock) | 4 | 50 OK, TOTAL 99,714,418, 175.9 s | 50 OK, TOTAL 99,714,418, 325.9 s |
| `spin40` (bad control, 40 s CPU per case) | 4 | 0 OK, 50 TLE, TOTAL 0, 210.7 s | 0 OK, 50 TLE, TOTAL 0, 390.8 s |
| `cpu20` (20 s CPU per case) | 8 | 50 OK, TOTAL 99,714,418, 140.8 s | 50 OK, TOTAL 99,714,418, 140.8 s |

Times are the wall time of the whole grading run.

**Per-case times** (`result/out/timing_summary.txt`): under the fixed version at 4 CPUs every `cpu28` case finished in at most 28.02 s of wall time (`cpu20`: 20.01 s), inside the 30 s limit. Under the original, only 2 of 50 processes finished; the other 48 were killed. The `wall25` solution got a mean of 13.00 s of CPU per case under the original grader (median 12.51 s) and 24.99 s under the fixed version, with the same output, because this control's output does not depend on the work done. A real deadline-based solver gets about twice the computation under the fixed version.

**Grading time** at 4 CPUs: the bad control, which hits the 30 s limit on every case, took 390.8 s under the fixed version (13 rounds × 30 s), inside the task's 600 s `eval_timeout`; 210.7 s under the original (7 rounds).

**Repeat of the original-grader rows.** The original-grader rows for `cpu20`, `wall25` at 4 CPUs and `cpu20` at 8 CPUs match the measurement jobs `evidence/runs/apple_incremental_game-cpu4v8-a` and `-b` (same counts and totals: 48 TLE and 3,955,266 at 4 CPUs on both workers; 50 OK and 99,714,418 at 8 CPUs).

## Limits

- Single-threaded test solutions only; multi-threaded solvers were not tested.
- The deadline solution's output is fixed, so the run shows the CPU it receives (13.00 against 24.99 s per case), not a score change. Deadline-based solvers' scores at 4 CPUs are not comparable between the original and the fixed version.
- Below 3 grader CPUs the 600 s `eval_timeout` binds before the 30 s per case (25 rounds × 30 s = 750 s at 2 CPUs).
- One run on one machine type (E2B `harbor-worker-v4`, Xeon 2.6 GHz).

**Verdict: accepted.**

## Repeatability (2026-10-13)

The job was run three times on fresh E2B workers (`evidence/runs/apple_incremental_game-v2-paired`, `-rep2`, `-rep3`) with the same `run.sh`, `arms.txt`, solutions and package. Every run has `status: exit=0`, and its worker was killed. All 12 arm × grader results (the 6 rows above under both graders) give the same OK/TLE/WA/RE counts and TOTAL in all three runs (`result/out/summary.txt`). Only wall times differ. The staged fixed evaluator (`pkg/files/eval_apple_incremental_game.py`, sha256 `ba31e840…`) was removed after collection.
