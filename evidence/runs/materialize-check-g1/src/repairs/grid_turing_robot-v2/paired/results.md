# grid_turing_robot v2: paired results

**Verdict: accepted.** At 4 grader CPUs, valid solutions using 16 or 28 s of CPU per case time out on 48 of 50 cases under the original grader (submission invalid) and pass 50/50 under the fixed version with the same TOTAL as every other valid control. Fast solutions, a 25 s wall-clock-deadline solution and the 8-CPU pair give the same results under both. A solution that spends 40 s per case times out on all 50 cases under both.

## Run

E2B job `evidence/runs/grid_turing_robot-v2-paired` (`run.sh`, `arms.txt`), one worker with 8 vCPUs and 7.9 GB RAM (`result/out/env.txt`), `status: exit=0`, worker killed (`result/worker.json`). Every arm ran the task's original `eval_cmd` (`cd /home/workspace/grid_turing_robot && python3 /tmp/eval_grid_turing_robot.py`) with `--network none --memory 4g --cpus N`, one container at a time, with the solution bind-mounted read-only over `solution.py`.

- **Original grader:** `seededge/edgebench.judge.grid_turing_robot@sha256:f67864ad…96c3`; `/tmp/eval_grid_turing_robot.py` sha256 `99c9c55d…17d6`, `max_workers=min(8, len(case_files))` (`result/out/eval_sha.txt`).
- **Fixed version:** built in the worker from this package's Dockerfile; `/tmp/eval_grid_turing_robot.py` sha256 `285229ee…3a22`, the `materialize.outputs` value in `source-lock.json`.
- **What the fixed grader computes** (`result/out/v2_workers.txt`): `--cpus 1/2/4/8` give `cpu.max` `100000/200000/400000/800000 100000` and 1/2/4/8 cases at once.
- **Solutions** (`sol/`, sha256 in `result/out/solutions_sha.txt`): the same files as jobs `grid_turing_robot-cpu4v8-a`/`-b`. `cpuN.py` is the known-good valid control (one state per step of a BFS route) preceded by a fixed N s of single-thread CPU work per case; `wall25.py` instead works until 25 s of wall-clock time; `baseline_good.py` is the known-good control with no extra work; `spin40.py` spends 40 s of CPU per case (more than the 30 s limit) and must time out. Each `cpuN`/`wall25`/`spin40` solution writes its start and end time to a per-arm directory (`result/out/timing/`), which does not affect grading.

## Results

Source: `evidence/runs/grid_turing_robot-v2-paired/result/out/summary.txt`; per-case lines in `result/out/logs/<arm>.log`; per-case times in `result/out/timing/<arm>/`. Score out of 100 from the task's `piecewise_min` scale via `sforge/harness/score_rescale.py` (TOTAL 94,092 → 19.80); `inf` makes the submission invalid.

| Solution | CPUs | Original grader | Fixed version |
| --- | ---: | --- | --- |
| `baseline_good` (no extra work) | 4 | 50 OK, TOTAL 94,092 (19.80), 1.3 s | 50 OK, TOTAL 94,092 (19.80), 1.2 s |
| `cpu12` (12 s CPU per case) | 4 | 50 OK, TOTAL 94,092, 157.2 s | 50 OK, TOTAL 94,092, 157.6 s |
| **`cpu16` (16 s CPU per case)** | 4 | **2 OK, 48 TLE, TOTAL inf (invalid)**, 196.8 s | **50 OK, TOTAL 94,092 (19.80)**, 213.6 s |
| **`cpu28` (28 s CPU per case)** | 4 | **2 OK, 48 TLE, TOTAL inf (invalid)**, 208.8 s | **50 OK, TOTAL 94,092 (19.80)**, 365.9 s |
| `wall25` (works until 25 s wall clock) | 4 | 50 OK, TOTAL 94,092, 176.3 s | 50 OK, TOTAL 94,092, 326.3 s |
| `spin40` (bad control, 40 s CPU per case) | 4 | 0 OK, 50 TLE, TOTAL inf, 210.8 s | 0 OK, 50 TLE, TOTAL inf, 390.9 s |
| `cpu20` (20 s CPU per case) | 8 | 50 OK, TOTAL 94,092, 140.9 s | 50 OK, TOTAL 94,092, 140.9 s |

Times are the wall time of the whole grading run.

**Per-case times** (`result/out/timing/`): under the fixed version at 4 CPUs the slowest `cpu28` case took 28.34 s from start of work to end (`cpu16`: 16.63 s), inside the 30 s limit. Under the original, `cpu12` cases took up to 24.18 s for 12 s of CPU, which is the half-CPU share. The `wall25` solution got a mean of 13.03 s of CPU per case under the original grader and 24.91 s under the fixed version (min 12.21 vs 23.95 s), with the same output, because this control's output does not depend on the work done. A real deadline-based solver gets about twice the computation under the fixed version.

**Grading time** at 4 CPUs: the bad control, which hits the 30 s limit on every case, took 390.9 s under the fixed version (13 rounds × 30 s), inside the task's 600 s `eval_timeout`; 210.8 s under the original (7 rounds).

**Repeat of the original-grader rows.** The original-grader rows for `cpu12`, `cpu16`, `cpu28` and `wall25` at 4 CPUs and `cpu20` at 8 CPUs match the earlier jobs `evidence/runs/grid_turing_robot-cpu4v8-a` and `-b` (same counts and TOTAL; wall times within 0.1 s).

**Verdict: accepted.**

## Repeatability (2026-10-13)

The job was run three times on fresh E2B workers (`evidence/runs/grid_turing_robot-v2-paired`, `-rep2`, `-rep3`) with the same `run.sh`, `arms.txt`, solutions and package. Every run has `status: exit=0`, and its worker was killed. All 14 arm × grader results (the 7 rows above, each under both graders) give the same OK/TLE/WA/RE counts and the same TOTAL in all three runs (`result/out/summary.txt`). The `cpu16` and `cpu28` triggers time out on 48 of 50 cases under the original grader and pass 50/50 under the fixed version every time. Only wall times differ. The fixed evaluator `files/eval_grid_turing_robot.py` was put in each rerun's `pkg/files/` from the materialized package (sha256 `285229ee…`, as in `result/out/eval_sha.txt`) and removed after collection.
