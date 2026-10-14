# Molecular Self Assembly (`molecular_self_assembly`)

**Outcome:** Fixed. <mark>On the publisher's 4-CPU grader, a valid solution using more than about 15 s of CPU per case times out, although the README promises 30 s per case, and each timed-out case scores 0. The fixed version runs at most as many cases at once as the grader has CPUs. The grader still does not enforce the 1 GB memory limit stated in the README, but we found no way for extra memory to raise scores.</mark>

## What the task asks

The solver writes a `solution.py` that reads standard input, writes standard output, and is "scored on **50 fixed test cases**". The README's "Runtime Limits" table states `| Time limit | 30 seconds / test case |` and `| Memory limit | 1 GB |`. It does not say which memory measure is meant (resident memory, RSS, or address space), which unit (10^9 bytes or GiB), or what happens when a solution exceeds the limit. The task is in the Combinatorial Optimization category.

## What goes wrong

The grader does not enforce the 1 GB per-solution limit, which we treat as a note. The helper `run_case` starts `python3 solution.py` with a 30 s timeout and sets no memory limit, and by default it runs up to 8 cases at the same time. The task JSON sets no memory limit either. The published leaderboard configuration sets `judge_mem_limit: "8g"` and `judge_cpu_limit: 4` for the whole grader container, and up to 8 solution processes running at once share that limit with their testers.

We ran the original grader on all 50 official cases. The test solution allocates N MiB, touches it, then prints the baseline output. OK means a case scored normally; RE means a runtime error.

| Run | Memory allocated | Cases at once | Peak RSS per case | Result |
|---|---|---|---|---|
| R1 (correct test submission) | 0 | 1 | 12.6 MB | 50/50 OK, TOTAL 69,280,072 |
| R2 (shows the problem) | 1300 MiB | 1 | 1,370,013,696 to 1,370,697,728 B (> 10^9 and > 2^30) | **50/50 OK, TOTAL 69,280,072** (identical) |
| R4 (below the limit, scaled down) | 700 MiB | 2 | 0.74 GB | 50/50 OK, 69,280,072 |
| R3 (container cap scaled down, 2 GiB / 2 cases ≈ official 8 GiB / 8) | 1300 MiB | 2 | 1.37 GB | **46/50 OK, 4 RE (killed for running out of memory), TOTAL 63,747,304** |

- In R2, a solution using about 1.37 GB RSS on every case should be rejected or penalized under a 1 GB limit. Instead it received full credit on all 50 cases, the same total as the correct test submission.
- R3 shows that the container cap partly penalizes a solution that is over the limit on every case, which lost 4 of 50 cases in this single run. We expect the lost cases to depend on timing. The container cap is not a per-solution limit.

On a 4-CPU grader the 30 s per case shrinks to about 15 s of CPU, and the fixed version removes this. The 30 s limit is wall-clock time, and the grader runs up to 8 cases at once (`eval_molecules.py`: `TIME_LIMIT = 30`, `SEBENCH_MOLECULES_WORKERS` default 8). The task sets no `cpu_limit`. In EdgeBench's leaderboard configuration `examples/all-tasks-k8s/experiment.yaml` (quoted in [`evidence/impact/edgebench-leaderboard-config.md`](../evidence/impact/edgebench-leaderboard-config.md)) (sha256 `d9d299794ba946cae8d2b7f68a7879a35bb8565d95e78107edf79802993643be`, headed "OFFICIAL EDGEBENCH LEADERBOARD SETTING") the grader gets `judge_cpu_limit: 4`, so each of 8 running cases gets about half a CPU. A single-threaded solution that needs more than about 15 s of CPU per case then times out, and a timed-out case scores 0 while the submission stays valid (the same path as R3's RE cases).

We measured this on the original grader on all 50 official cases (`evidence/runs/molecular_self_assembly-cpu4v8/result/out/summary.txt`, repeated in `molecular_self_assembly-v2-paired`). Each test solution is the shipped baseline preceded by fixed work:

| Work before the shipped baseline | 4 CPUs | 8 CPUs |
|---|---|---|
| 12 s of CPU per case | 50 OK, TOTAL 69,280,072 | 50 OK, TOTAL 69,280,072 |
| 16, 20 or 28 s of CPU per case | **2 OK, 48 TLE, TOTAL 2,849,909 (score 0)** | 50 OK, TOTAL 69,280,072 |
| work until a 25 s wall-clock deadline | 50 OK, TOTAL 69,280,072; mean 13.01 s of CPU per case | not run |

A solution that searches until a wall-clock deadline gets about half the computation it would get with a whole CPU per case (CPU per case: `molecular_self_assembly-v2-paired/result/out/timing/c4-wall25-v1/`).

The note that ships with the fixed version says to treat the README's 1 GB memory figure as advice only. Only the grader container limits memory, and in the published setting that means 8 GiB shared by 8 cases running at once. The cap penalizes solutions that are heavy on every case, and it does so unpredictably. We found no evidence that extra memory improves scores.

## How much it matters

We found no way to gain score from memory. The task is pure Python (the grader image has no numpy) with a 30 s limit per case. A full table of pairwise distances over time fits in about 180 MB, and a solution reaches the time limit long before memory runs out. The solution cannot see the hidden cases. This conclusion is reasoning, and we did not measure it. The problem is a missing rejection, so it never rejects valid submissions. It affects only solutions that use more than the stated limit, and the container cap may penalize them unpredictably.

Under the original grader at 4 CPUs, a solution using more than about 15 s of CPU per case loses every such case (score 0 each, about 6.5 million of a 326 million total per case in the real run below), and losing 48 of 50 cases costs nearly the whole score. The fixed version scores these cases. For solutions that stop at a wall-clock deadline, the score depends on the search quality reached with half a CPU. Under the fixed version such a solver gets about twice the CPU per case (mean 13.01 s → 24.91 s for the 25 s control), and we did not measure the effect on its score. A third-party Claude Opus 5.5 run (4 hours, published on Hugging Face as `adafadaq/edgebench-opus-5-5-xhigh-rollouts`) on this grader with 4 grader CPUs (`run_config.json`: `"judge_cpu_limit": 4`) had all 13 submissions valid with 50/50 cases OK. Its best submission (agent-6) totals 326,392,210, above the reference point for 100 (322,991,707.7), so it scores 100. Its grading took 178.7 s (`report.json` `runtime_seconds`), about 7 rounds of 8 cases at 25.5 s each, which is what a solution that stops at a deadline of about 25 s per case would give; we did not inspect its source. Its best submission already scores 100, so for this run the fixed version would change only the CPU per case available to a deadline-based solver.

## The fix

The fixed version (`repairs/molecular_self_assembly-v2/`) changes how many cases the grader `/tmp/eval_molecules.py` runs at once. A new function `cpu_quota_workers()` reads the grader's CPU quota from the cgroup (`cpu.max`, or the cgroup v1 quota and period) and rounds it down to whole CPUs. It falls back to `os.cpu_count()` when there is no quota and keeps the result between 1 and 8. The pool size becomes `min(SEBENCH_MOLECULES_WORKERS or 8, cpu_quota_workers(), len(case_files))`. At `--cpus 1/2/4/8` the fixed grader runs 1/2/4/8 cases at once (`molecular_self_assembly-v2-paired/result/out/v2_workers.txt`). The task JSON changes only `judge.image_tag`. The 30 s limit, the README, the tester, the cases and the score scale stay as they were. With 8 or more CPUs the fixed grader runs 8 cases at once, exactly as the original does. The memory note above still ships with the fixed version.

We ran the same solutions on both graders at `--cpus 4`, with one pair at `--cpus 8` (`evidence/runs/molecular_self_assembly-v2-paired/result/out/summary.txt`; `repairs/molecular_self_assembly-v2/paired/results.md`):

| Solution | CPUs | Original grader | Fixed version |
| --- | ---: | --- | --- |
| shipped baseline, no extra work | 4 | 50 OK, TOTAL 69,280,072 | 50 OK, TOTAL 69,280,072 |
| 12 s of CPU per case | 4 | 50 OK, TOTAL 69,280,072 | 50 OK, TOTAL 69,280,072 |
| **16 s of CPU per case** | 4 | **2 OK, 48 TLE, TOTAL 2,849,909 (score 0)** | **50 OK, TOTAL 69,280,072** |
| **28 s of CPU per case** | 4 | **2 OK, 48 TLE, TOTAL 2,849,909 (score 0)** | **50 OK, TOTAL 69,280,072** |
| works until a 25 s wall-clock deadline | 4 | 50 OK, TOTAL 69,280,072; mean 13.01 s CPU per case | 50 OK, TOTAL 69,280,072; mean 24.91 s CPU per case |
| 40 s of CPU per case (bad control) | 4 | 50 TLE, TOTAL 0 | 50 TLE, TOTAL 0 |
| 20 s of CPU per case | 8 | 50 OK, TOTAL 69,280,072 | 50 OK, TOTAL 69,280,072 |

These controls build on the shipped baseline, so their own scores out of 100 are near 0 (69,280,072 → 0.0133; 2,849,909 → 0; `sforge/harness/score_rescale.py`). For a strong solution, losing 48 of 50 cases costs nearly its whole score. Under the fixed version the slowest 28 s case took 29.08 s from start to end (`result/out/timing/c4-cpu28-v2/`), less than 1 s inside the limit. Grading at 4 CPUs takes at most ⌈50/4⌉ = 13 rounds of 30 s. The bad control took 390.9 s (original: 210.8 s), inside the task's 600 s `eval_timeout`.

At 8 or more grader CPUs the two versions are the same grader, so their scores are comparable. At 4 CPUs a deterministic solution that finished every case in time under the original gets the same output and score under the fixed version, and cases needing about 15 to 30 s of CPU are scored instead of 0. A solution that searches until a wall-clock deadline gets about twice the CPU per case, so its score under the two graders is not comparable. Per-case CPU never decreases under the fixed version.

A per-solution memory limit could be added in a separate, newly versioned variant, using either `RLIMIT_AS` (an address-space limit) or a check of peak RSS after the run. Its scores must not be merged with scores from the original version. A threaded pure-Python program (1 to 64 threads) ran successfully under `RLIMIT_AS=1e9` with about 11 MB RSS, so an address-space limit would not wrongly reject such programs.

## How we checked it

- We ran the original helper of the original grader, in the original image pinned by digest, on all 50 official cases with `--network none --memory 2g --memory-swap 2g --cpus 2`, giving the table above.
- We read the helper, the task JSON and the published leaderboard configuration to establish where memory is and is not limited.
- We made the CPU runs and the paired run on E2B. The shipped baseline preceded by 12 to 28 s of CPU work per case, by work until a 25 s wall-clock deadline, or by 40 s of work (bad control) ran on the original grader at `--cpus 4` and `--cpus 8` (`evidence/runs/molecular_self_assembly-cpu4v8`) and side by side on the original and fixed graders (`evidence/runs/molecular_self_assembly-v2-paired`), and each job ended with `status: exit=0`. Each solution logs its own start, end and CPU time per case (`result/out/timing/`), which does not affect grading. The solution files contain the shipped baseline, so the repository does not store them; each job's `sol/README.md` says how we made them.

## Limits

- The fixed grader reads its CPU quota from the cgroup (`cpu.max`). We tested this with `docker run --cpus` only, not inside a Kubernetes pod, which is the backend EdgeBench's leaderboard settings use.
- Without a cgroup quota the fixed grader falls back to `os.cpu_count()`, which counts all of the host's CPUs and not only the ones the grader may use (`os.sched_getaffinity`). Under a CPU-set limit with no quota (for example `docker run --cpuset-cpus`), or where the pod cannot see its own `cpu.max`, it can still run more cases at once than it has CPUs, as the original does. Using the affinity count would need a new paired run, so we did not change it.
- We ran no AI model or solver. The effects shown come from test submissions and counterexamples we wrote. We also regraded the third-party run above at 4 CPUs, where 8 of its 13 submissions each score 3–4% higher in raw terms under the fixed version, and the run's score stays 100 because it was already above the top of the scale (`evidence/runs/opus55-regrade2-summary/summary.json`). We have not estimated an effect on the leaderboard.
- We measured the CPU dependence at 4 and 8 CPUs with single-threaded test solutions. We did not test multi-threaded solvers, or 3, 5, 6 or 7 CPUs.
- At 4 CPUs the fixed version leaves less than 1 s of margin for a solution that uses 28 s of CPU per case (slowest case 29.08 s), so the usable budget is a little under 30 s of CPU once interpreter start-up is counted.
- Deadline-based solvers get about twice the CPU per case under the fixed version at 4 CPUs, so their scores under the two graders are not comparable. We did not measure how much their scores change.
- With fewer than 3 grader CPUs the 600 s `eval_timeout` binds before the 30 s per case. At 2 CPUs, 25 rounds × 30 s = 750 s, so only about 24 s per case is usable (the original gives about 7.5 s of CPU per case there). The grader rounds the quota down, so 2.5 CPUs run 2 cases at once.
- The memory runs used a 2 GiB container with 1 to 2 cases at once, not the official setup of 8 GiB, 8 cases at once and 4 CPUs. R3 imitates the official setup by scaling the ratio, and how many cases it loses to memory depends on timing.
- Each memory configuration ran once, so there are no repeatability statistics for R3. We ran the CPU rows of the original grader four times (`molecular_self_assembly-cpu4v8` once, `-v2-paired` with `-rep2` and `-rep3`) with the same counts and totals.
- We do not know past deployment overrides, so we cannot exclude a different memory policy in the past.
- The conclusion that extra memory gives no advantage is reasoning, not a measured experiment. We built no strong solver.

## Reproduce

- Original grader image: `sha256:8afd932de7e5…`.
- Fixed version: `repairs/molecular_self_assembly-v2/` (`materialize.sh`, `repair.patch`, `source-lock.json`; fixed grader sha256 `1cf8f71d…9ef0`). Paired run: `repairs/molecular_self_assembly-v2/paired/run.sh` (as run: `evidence/runs/molecular_self_assembly-v2-paired/run.sh`); CPU runs on the original grader: `evidence/runs/molecular_self_assembly-cpu4v8/run.sh`.
- Memory probe on all 50 official cases: `evidence/scripts/molecular_self_assembly/run_memory_probe.sh <MiB> <workers>` with `hog_solution.py`. Outputs are `r1_base_w1.out`, `r2_hog1300_w1.out`, `r3_hog1300_w2.out` and `r4_hog700_w2.out`.
- RLIMIT_AS thread probe: `evidence/scripts/molecular_self_assembly/as_limit_threads_probe.py`, with output in `as_limit_threads_probe.out`.
- Third-party run: `evidence/runs/opus55-rollouts-meta/result/meta/opus-16x4h-1009-0036-w4/molecular_self_assembly/` (`final_result.json`, `run_config.json`, `submissions/*/report.json`).
- Supporting records: `evidence/reviews/molecular_self_assembly.md`.
