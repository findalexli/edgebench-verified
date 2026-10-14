# molecular_self_assembly v2: paired results

**Verdict: accepted.** At 4 grader CPUs, solutions using 16 or 28 s of CPU per case lose 48 of 50 cases to timeouts under the original grader (TOTAL 2,849,909, score 0) and pass 50/50 under the fixed version with the same TOTAL as every other valid control (69,280,072). Fast solutions, a 25 s wall-clock-deadline solution and the 8-CPU pair give the same results under both. A solution that spends 40 s per case times out on all 50 cases under both.

## Run

E2B job `evidence/runs/molecular_self_assembly-v2-paired` (`run.sh`, `arms.txt`), one worker with 8 vCPUs and 7.9 GB RAM (`result/out/env.txt`), `status: exit=0`, worker killed (`result/worker.json`). Every arm ran the task's original `eval_cmd` (`cd /home/workspace/molecules && python3 /tmp/eval_molecules.py`) with `--network none --memory 4g --cpus N`, one container at a time, with the solution bind-mounted read-only over `solution.py`. `SEBENCH_MOLECULES_WORKERS` was not set, as in the harness.

- **Original grader:** `seededge/edgebench.judge.molecular_self_assembly@sha256:8afd932d…6da5`; `/tmp/eval_molecules.py` sha256 `4faad7b9…baac`, default 8 cases at once (`result/out/eval_sha.txt`).
- **Fixed version:** built in the worker from this package's Dockerfile; `/tmp/eval_molecules.py` sha256 `1cf8f71d…9ef0`, the `materialize.outputs` value in `source-lock.json`.
- **What the fixed grader computes** (`result/out/v2_workers.txt`): `--cpus 1/2/4/8` give `cpu.max` `100000/200000/400000/800000 100000` and 1/2/4/8 cases at once.
- **Solutions** (sha256 in `result/out/solutions_sha.txt`): the same files as job `molecular_self_assembly-cpu4v8`. `baseline.py` is the shipped baseline solution (an image file; removed from the job directory after the run); `cpuN.py` is the shipped baseline preceded by a fixed N s of single-thread CPU work per case; `wall25.py` instead works until 25 s of wall-clock time; `spin40.py` spends 40 s of CPU per case (more than the 30 s limit) and must time out. Because they contain the shipped baseline's code, these files are not published; `../../../evidence/runs/molecular_self_assembly-v2-paired/sol/README.md` gives the added preamble and how to rebuild them. Each `cpuN`/`wall25`/`spin40` solution writes its start and end time to a per-arm directory (`result/out/timing/`), which does not affect grading.

## Results

Source: `evidence/runs/molecular_self_assembly-v2-paired/result/out/summary.txt`; per-case lines in `result/out/logs/<arm>.log`; per-case times in `result/out/timing/<arm>/`. Score out of 100 from the task's `piecewise_max` scale via `sforge/harness/score_rescale.py`: 69,280,072 → 0.0133; 2,849,909 and 0 → 0. A timed-out case scores 0 and the submission stays valid. The controls are weak (the shipped baseline), so the normalized difference here is small; for a strong solution, losing 48 of 50 cases costs nearly its whole score.

| Solution | CPUs | Original grader | Fixed version |
| --- | ---: | --- | --- |
| `baseline` (shipped baseline, no extra work) | 4 | 50 OK, TOTAL 69,280,072, 1.9 s | 50 OK, TOTAL 69,280,072, 1.9 s |
| `cpu12` (12 s CPU per case) | 4 | 50 OK, TOTAL 69,280,072, 158.0 s | 50 OK, TOTAL 69,280,072, 158.6 s |
| **`cpu16` (16 s CPU per case)** | 4 | **2 OK, 48 TLE, TOTAL 2,849,909**, 196.8 s | **50 OK, TOTAL 69,280,072**, 210.2 s |
| **`cpu28` (28 s CPU per case)** | 4 | **2 OK, 48 TLE, TOTAL 2,849,909**, 208.9 s | **50 OK, TOTAL 69,280,072**, 377.0 s |
| `wall25` (works until 25 s wall clock) | 4 | 50 OK, TOTAL 69,280,072, 177.2 s | 50 OK, TOTAL 69,280,072, 327.3 s |
| `spin40` (bad control, 40 s CPU per case) | 4 | 0 OK, 50 TLE, TOTAL 0, 210.8 s | 0 OK, 50 TLE, TOTAL 0, 390.9 s |
| `cpu20` (20 s CPU per case) | 8 | 50 OK, TOTAL 69,280,072, 141.2 s | 50 OK, TOTAL 69,280,072, 141.4 s |

Times are the wall time of the whole grading run.

**Per-case times** (`result/out/timing/`): under the fixed version at 4 CPUs the slowest `cpu28` case took 29.08 s from start of work to end (`cpu16`: 16.07 s), inside the 30 s limit but with under 1 s to spare, so the usable budget per case is a little under 30 s of CPU once interpreter start-up is counted. Under the original, `cpu12` cases took up to 24.07 s for 12 s of CPU, the half-CPU share. The `wall25` solution got a mean of 13.01 s of CPU per case under the original grader and 24.91 s under the fixed version (min 12.22 vs 24.62 s), with the same output, because this control's output does not depend on the work done. A real deadline-based solver gets about twice the computation under the fixed version.

**Grading time** at 4 CPUs: the bad control, which hits the 30 s limit on every case, took 390.9 s under the fixed version (13 rounds × 30 s), inside the task's 600 s `eval_timeout`; 210.8 s under the original (7 rounds).

**Repeat of the original-grader rows.** The original-grader rows for `cpu12`, `cpu16`, `cpu28` and `wall25` at 4 CPUs and `cpu20` at 8 CPUs match the earlier job `evidence/runs/molecular_self_assembly-cpu4v8` (same counts and TOTAL; wall times within 0.8 s).

**Verdict: accepted.**

## Repeatability (2026-10-13)

The job was run three times on fresh E2B workers (`evidence/runs/molecular_self_assembly-v2-paired`, `-rep2`, `-rep3`) with the same `run.sh`, `arms.txt` and package. Every run has `status: exit=0`, and its worker was killed. All 14 arm × grader results give the same OK/TLE/WA/RE counts and the same TOTAL in all three runs (`result/out/summary.txt`). The `cpu16`/`cpu28` triggers score 2 OK, 48 TLE, TOTAL 2,849,909 under the original and 50 OK, TOTAL 69,280,072 under the fixed version every time. The solutions contain the shipped baseline, so they are not kept in the repository (`sol/README.md`). For the reruns they were restored from the internal copies, and `baseline.py` was cut out of `cpu12.py`. All seven sha256 equal run 1's `solutions_sha.txt`. They were removed again after collection, as was the staged `pkg/files/eval_molecules.py` (sha256 `1cf8f71d…`).
