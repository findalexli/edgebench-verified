# Molecular Self Assembly (`molecular_self_assembly`)

**Outcome:** Kept, with a note. <mark>The grader does not enforce the per-solution memory limit stated in the README, but no way was found for extra memory to raise scores.</mark>

## What the task asks

The solver writes a `solution.py` that reads standard input, writes standard output, and is "scored on **50 fixed test cases**". The README's "Runtime Limits" table states `| Time limit | 30 seconds / test case |` and `| Memory limit | 1 GB |`. It does not say which memory measure is meant (resident memory, RSS, or address space), which unit (10^9 bytes or GiB), or what happens when the limit is exceeded. Category: Combinatorial Optimization.

## What goes wrong

**The 1 GB per-solution limit is not enforced.** The helper `run_case` starts `python3 solution.py` with a 30 s timeout and sets no memory limit. By default, up to 8 cases run at the same time. The task JSON sets no memory limit. The published leaderboard configuration sets `judge_mem_limit: "8g"` and `judge_cpu_limit: 4` for the whole grader container. That limit is shared by up to 8 solution processes running at once and their testers.

Results under the original grader on all 50 official cases. The test solution allocates N MiB, touches it, then prints the baseline output. OK means a case scored normally; RE means a runtime error.

| Run | Memory allocated | Cases at once | Peak RSS per case | Result |
|---|---|---|---|---|
| R1 (correct test submission) | 0 | 1 | 12.6 MB | 50/50 OK, TOTAL 69,280,072 |
| R2 (shows the problem) | 1300 MiB | 1 | 1,370,013,696 to 1,370,697,728 B (> 10^9 and > 2^30) | **50/50 OK, TOTAL 69,280,072** (identical) |
| R4 (below the limit, scaled down) | 700 MiB | 2 | 0.74 GB | 50/50 OK, 69,280,072 |
| R3 (container cap scaled down, 2 GiB / 2 cases ≈ official 8 GiB / 8) | 1300 MiB | 2 | 1.37 GB | **46/50 OK, 4 RE (killed for running out of memory), TOTAL 63,747,304** |

- **Expected and observed (R2).** A solution using about 1.37 GB RSS on every case should be rejected or penalized under a 1 GB limit. Instead it received full credit on all 50 cases, the same total as the correct test submission.
- **What the container cap does (R3).** It partly penalizes a solution that is over the limit on every case: 4 of 50 cases lost in this single run. Which cases are lost is expected to depend on timing. This is not a per-solution limit.

The note that ships with the task: treat the README's 1 GB memory figure as advice only. Memory is limited only by the grader container: in the published setting, 8 GiB shared by 8 cases running at once. That cap penalizes solutions that are heavy on every case, in a way that cannot be predicted. No evidence was found that extra memory improves scores.

## How much it matters

No way to gain score was found. The task is pure Python (the grader image has no numpy) with a 30 s limit per case. A full table of pairwise distances over time fits in about 180 MB, and the time limit is reached long before memory runs out. The hidden cases are not visible to the solution. This conclusion is reasoning; it was not measured. The problem is a missing rejection, so it never rejects valid submissions. Only solutions that use more than the stated limit are affected, and the container cap may penalize them unpredictably.

There is no code change. The note above ships with the task. A per-solution limit could be added in a separate, newly versioned variant, using either `RLIMIT_AS` (an address-space limit) or a check of peak RSS after the run. Its scores must not be merged with scores from the original version. A threaded pure-Python program (1 to 64 threads) ran successfully under `RLIMIT_AS=1e9` with about 11 MB RSS, so an address-space limit would not wrongly reject such programs.

## How we checked it

- **Original grader in the original image, pinned by digest.** The original helper ran on all 50 official cases in the grader image with `--network none --memory 2g --memory-swap 2g --cpus 2`, giving the table above.
- **Source and configuration.** The helper, task JSON and published leaderboard configuration were read to establish where memory is and is not limited.

## Limits

- No AI model or solver was run. Effects are shown only on test submissions and counterexamples we wrote. No effect on the leaderboard is estimated.
- Runs used a 2 GiB container with 1 to 2 cases at once, not the official setup of 8 GiB, 8 cases at once and 4 CPUs. R3 imitates the official setup by scaling the ratio, and how many cases it loses to memory depends on timing.
- Each configuration ran once. There are no repeatability statistics for R3.
- Past deployment overrides are unknown, so a different memory policy in the past cannot be excluded.
- The conclusion that extra memory gives no advantage is reasoning, not a measured experiment. No strong solver was built.

## Reproduce

- Original grader image: `sha256:8afd932de7e5…`.
- Memory probe on all 50 official cases: `evidence/scripts/molecular_self_assembly/run_memory_probe.sh <MiB> <workers>` with `hog_solution.py`. Outputs are `r1_base_w1.out`, `r2_hog1300_w1.out`, `r3_hog1300_w2.out` and `r4_hog700_w2.out`.
- RLIMIT_AS thread probe: `evidence/scripts/molecular_self_assembly/as_limit_threads_probe.py`, with output in `as_limit_threads_probe.out`.
- Supporting records: `evidence/reviews/molecular_self_assembly.md`.
