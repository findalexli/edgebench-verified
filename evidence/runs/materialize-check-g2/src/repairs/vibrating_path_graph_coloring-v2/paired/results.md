# vibrating_path_graph_coloring v2: paired results

**Verdict: accepted.** At 4 grader CPUs, valid solutions using 20 or 28 s of CPU per case time out on 48 of 50 cases under the original grader (total `inf`, no score) and pass 50/50 under the fixed version with the same total as every other valid control (24,650,014, 2.06 out of 100). The honest control alone and the 8-CPU pair give the same totals under both. A solution that spends 40 s per case times out on all 50 cases under both. A solution that stops at a 25 s wall-clock deadline passed 50/50 under the fixed version in both runs; under the original it passed in three of four runs and once lost 14 cases (below).

## Runs

Three E2B jobs, each one worker with 8 vCPUs and 7.9 GB RAM, `status: exit=0`, worker killed (`result/worker.json`, ledger `evidence/runs/ledger.jsonl`):

| job | arms | elapsed |
| --- | --- | ---: |
| `evidence/runs/vibrating_path_graph_coloring-v2-paired-a` | control, `cpu20`, `cpu28` at 4 CPUs; tester time per case | 2569 s |
| `evidence/runs/vibrating_path_graph_coloring-v2-paired-b` | `wall25`, `spin40` at 4 CPUs; `cpu20` at 8 CPUs | 2149 s |
| `evidence/runs/vibrating_path_graph_coloring-v2-paired-c` | `wall25` again (original twice, fixed once), with tester-start logging | 1245 s |

`run.sh` (jobs `-a`, `-b`), `run-tester-log.sh` (job `-c`), `arms.txt` and `tester_time.sh` in this directory are copies of the job files. Every arm ran the task's original `eval_cmd` (`cd /home/workspace/vibrating_path && python3 /tmp/eval_vibrating_path.py`) with `--network none --memory 4g --cpus N`, one container at a time, with the solution bind-mounted read-only over `solution.py`.

- **Original grader:** `seededge/edgebench.judge.vibrating_path_graph_coloring@sha256:db8a9741…084e`; `/tmp/eval_vibrating_path.py` sha256 `934a2b9d…9350`, `max_workers=min(8, len(case_files))` (`result/out/eval_sha.txt`).
- **Fixed version:** built in the worker from this package's Dockerfile; `/tmp/eval_vibrating_path.py` sha256 `3b72b9ed…bd23`, the `materialize.outputs` value in `source-lock.json`. At `--cpus 1/2/3/4/8` it runs 1/2/3/4/8 cases at once (`result/out/v2_workers.txt`).
- **Solutions** (`sol/`, `base/`; sha256 in `result/out/solutions_sha.txt`). `base/base.py` is our honest control (greedy K-colouring, then hits simulated by the shipped tester's rule), the same file as in `vibrating_path_graph_coloring-cpu4v8-a`/`-b`. Each `sol/*.py` runs the control, then works until the process has used W CPU-seconds in total (`cpuW`) or until W seconds of wall clock (`wall25`), then prints the control's answer, so every arm prints the same valid answer. `cpu0.py` is the control alone; `spin40.py` spends 40 s of CPU, more than the 30 s limit, and must time out. Each wrapper writes its start and end time and CPU used to `result/out/timing/<arm>/`; a process killed by the grader leaves no end line (`timing_summary.txt`; in job `-c` the extra file `tester_starts.txt` is counted as one "killed" process).
- **Job `-c` only:** inside the container, before grading, `tools/bin/tester` is renamed and replaced by a two-line shell wrapper that records the start of each tester call and then `exec`s the real tester with the same arguments. The evaluator is unchanged.

## Results

Sources: `result/out/summary.txt` of each job; per-case lines in `result/out/logs/<arm>.log`. Score out of 100 from the task's `piecewise_log_min` scale via `sforge/harness/score_rescale.py`; `inf` has no score.

| Solution | CPUs | Original grader | Fixed version | job |
| --- | ---: | --- | --- | --- |
| `cpu0` (honest control alone) | 4 | 50 OK, TOTAL 24,650,014 (2.06), 207.6 s | 50 OK, TOTAL 24,650,014 (2.06), 191.0 s | `-a` |
| **`cpu20` (20 s CPU per case)** | 4 | **2 OK, 48 TLE, TOTAL inf (no score)**, 218.1 s | **50 OK, TOTAL 24,650,014 (2.06)**, 438.4 s | `-a` |
| **`cpu28` (28 s CPU per case)** | 4 | **2 OK, 48 TLE, TOTAL inf (no score)**, 224.7 s | **50 OK, TOTAL 24,650,014 (2.06)**, 508.6 s | `-a` |
| `wall25` (works until 25 s wall clock) | 4 | **36 OK, 14 TLE, TOTAL inf**, 438.5 s | 50 OK, TOTAL 24,650,014, 558.0 s | `-b` |
| `wall25`, repeat 1 / repeat 2 | 4 | 50 OK, 24,650,014, 372.5 s / 50 OK, 24,650,014, 362.2 s | 50 OK, 24,650,014, 473.1 s | `-c` |
| `spin40` (bad control, 40 s CPU per case) | 4 | 0 OK, 50 TLE, TOTAL inf, 210.7 s | 0 OK, 50 TLE, TOTAL inf, 390.9 s | `-b` |
| `cpu20` (20 s CPU per case) | 8 | 50 OK, TOTAL 24,650,014, 263.9 s | 50 OK, TOTAL 24,650,014, 265.4 s | `-b` |

Times are the wall time of the whole grading run.

**Per-case times** (`timing_summary.txt`): under the fixed version at 4 CPUs every `cpu28` case finished in at most 28.12 s of wall time (`cpu20`: 20.77 s). Under the original only 2 of 50 processes finished. The `wall25` solution got a mean of 12.84 s of CPU per case under the original grader in job `-b` (12.77 and 12.81 s in the repeats) and 24.98 s under the fixed version (24.92 s in `-c`), with the same output, because this control's output does not depend on the work done. A real deadline-based solver gets about twice the computation under the fixed version.

**The 14 TLE of `wall25` under the original grader in job `-b`.** Every `wall25` solution process in that arm wrote its end line, at most 27.14 s after its own start (`timing/c4-wall25-v1/`), and all 14 timed-out cases are among the 25 cases whose tester is slowest (16.4–19.0 s each at 1 CPU, `tester_time.out`). The evaluator reports a timeout of the tester (`timeout=60`) with the same label `TLE` as a timeout of the solution (both are `subprocess.TimeoutExpired`, line 36–37). The likely cause is therefore the tester running with about half a CPU, or less, next to 7 other busy cases on a slower worker (the same worker's 8-CPU arm took 263.9 s against 223.6–229.2 s on the measurement workers). This is an inference: job `-b` did not log tester starts, and job `-c`, which did, passed 50/50 twice on another worker, so the mechanism was not observed directly. Under the fixed version each tester gets a whole CPU (at most 19.0 s against its 60 s timeout). The earlier measurement jobs (`vibrating_path_graph_coloring-cpu4v8-a`, `-b`) also passed `wall25` at 4 CPUs.

**Tester time** (`tester_time.out`, job `-a`, original image, one case at a time at `--cpus 1`, honest control's output): 5.56–18.99 s per case, 579.6 s in total; the control itself took 1.7–5.5 s per case.

**Grading time** at 4 CPUs under the fixed version: at most 558.0 s in these runs (`wall25`, job `-b`), 508.6 s for `cpu28`; the bad control, which hits the 30 s limit on every case, took 390.9 s (13 rounds × 30 s; no tester runs after a timeout). The fixed version sets `eval_timeout` to 900 s; see the README for the bound (557 s for solutions near 30 s per case with the measured tester times). The original's 600 s would have held in every run here, but with 7% margin in the bound.

**Repeat of the original-grader rows.** The `cpu20` row at 4 CPUs (2 OK, 48 TLE, `inf`) and the 8-CPU `cpu20` row (50 OK, 24,650,014) match the measurement jobs `vibrating_path_graph_coloring-cpu4v8-a` and `-b`.

## Limits

- Single-threaded test solutions only; multi-threaded solvers were not tested.
- The deadline solution's output is fixed, so the run shows the CPU it receives, not a score change. Deadline-based solvers' scores at 4 CPUs are not comparable between the original and the fixed version.
- Tester times are for the honest control's outputs only.
- Below 3 grader CPUs `eval_timeout` can bind before the 30 s per case (README).
- The cause of the 14 `wall25` timeouts in job `-b` is inferred, not observed (above).

**Verdict: accepted.**

## Repeatability (2026-10-13)

| job | arms | runs | identical? |
| --- | --- | --- | --- |
| `evidence/runs/vibrating_path_graph_coloring-v2-paired-a`, `-rep2`, `-rep3` | `cpu0`, `cpu20`, `cpu28` at 4 CPUs, both graders | 3 | yes |
| `…-paired-b`, `-rep2`, `-rep3` | `wall25`, `spin40` at 4 CPUs; `cpu20` at 8 CPUs; both graders | 3 | **no: `wall25` under the original grader** |
| `…-paired-c`, `-rep2`, `-rep3` | `wall25` at 4 CPUs (original twice, fixed once per run) | 3 | yes |

Each rerun used the job's `run.sh`, `arms.txt`, `base/` and `sol/` unchanged, on a fresh E2B worker. Every rerun has `status: exit=0`, and its worker was killed. The staged fixed evaluator (`pkg/files/eval_vibrating_path.py`, sha256 `3b72b9ed…`) was removed after collection.

**Identical.** Every arm under the fixed version gives the same result in all runs. The triggers `cpu20` and `cpu28` pass 50/50 (24,650,014), `spin40` times out on 50/50, and `wall25` passes 50/50 in all 6 fixed-version gradings (`-b` and `-c`, three runs each). Under the original grader, `cpu20`/`cpu28` at 4 CPUs give 2 OK, 48 TLE in all three runs, and `cpu0`, `spin40` and the 8-CPU `cpu20` are also identical.

**Outcome change: `wall25` under the original grader at 4 CPUs.** It lost 14 cases (36 OK, 14 TLE, total `inf`) in run 1 of `-b` and passed 50/50 in both reruns of `-b` (412.3 s, 360.7 s) and in all six original-grader gradings of `-c` and its reruns. That is 1 timeout run out of 9 original-grader gradings of this solution. This valid control's verdict under the original grader is therefore not repeatable. Under the fixed version it never changed. This is consistent with the inference above (testers starved of CPU next to 7 busy cases on a slower worker), and it is itself the defect the fix removes. It does not change the fix's acceptance: the trigger arms flip in every run, and no fixed-version verdict moved.
