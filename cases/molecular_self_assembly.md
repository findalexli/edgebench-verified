# Molecular Self Assembly (`molecular_self_assembly`)

**Decision:** Retain with note. The evaluator does not enforce the README's per-solution memory limit, but no mechanism was found by which extra memory would raise scores.

## What the task asks for

The solver writes a `solution.py` that reads stdin, writes stdout, and is "scored on **50 fixed test cases**". The README's "Runtime Limits" table states `| Time limit | 30 seconds / test case |` and `| Memory limit | 1 GB |`. It does not say which memory metric is meant (RSS or address space), which unit (10^9 bytes or GiB), or what happens when the limit is exceeded. Category: Combinatorial Optimization.

## What goes wrong

**The 1 GB per-solution limit is not enforced.** The helper `run_case` starts `python3 solution.py` with a 30 s timeout and sets no memory limit. Up to 8 cases run concurrently by default. The task JSON sets no memory limit. The published leaderboard configuration sets `judge_mem_limit: "8g"` and `judge_cpu_limit: 4` for the whole judge container, shared by up to 8 concurrent solution processes and their testers.

Results under the original evaluator on all 50 official cases (the test solution allocates N MiB, touches it, then prints the baseline output):

| Run | Allocation | Workers | Peak RSS per case | Result |
|---|---|---|---|---|
| R1 (good control) | 0 | 1 | 12.6 MB | 50/50 OK, TOTAL 69,280,072 |
| R2 (trigger) | 1300 MiB | 1 | 1,370,013,696 to 1,370,697,728 B (> 10^9 and > 2^30) | **50/50 OK, TOTAL 69,280,072** (identical) |
| R4 (below-limit control, scaled) | 700 MiB | 2 | 0.74 GB | 50/50 OK, 69,280,072 |
| R3 (scaled aggregate cap, 2 GiB / 2 workers ≈ official 8 GiB / 8) | 1300 MiB | 2 | 1.37 GB | **46/50 OK, 4 RE (OOM-killed), TOTAL 63,747,304** |

- **Expected vs observed (R2).** A solution using about 1.37 GB RSS on every case should be rejected or penalized under a 1 GB limit. Instead it received full credit on all 50 cases, the same total as the good control.
- **What the container cap does (R3).** It partially penalizes a solution that is uniformly over the limit: 4 of 50 cases lost in this single run. Which cases are lost is expected to depend on timing. This is not per-solution enforcement.

The note that ships with the task: treat the README's 1 GB memory figure as advisory. Memory is bounded only by the judge container: in the published setting, 8 GiB shared by 8 concurrent cases. That cap penalizes uniformly heavy solutions unpredictably. No evidence was found that extra memory improves scores.

## Impact

No score mechanism was found. The task is pure Python (the judge image has no numpy) with a 30 s limit per case. A full pairwise-distance-over-time table fits in about 180 MB, and the time limit binds long before memory does. The hidden cases are not visible to the solution. This conclusion is reasoning; it was not measured. The defect is a missing rejection, so it never rejects valid submissions. Only solutions that use more than the stated limit are affected, and the container cap may penalize them unpredictably.

## Fix (v2)

No change; the note above ships with the task. A per-solution limit could be added in a separately versioned variant, using either `RLIMIT_AS` or a post-hoc peak-RSS check. Its scores must not be merged with original scores. A threaded pure-Python program (1 to 64 threads) ran successfully under `RLIMIT_AS=1e9` with about 11 MB RSS, so an address-space limit would not falsely reject such programs.

## How we know

- **Original evaluator in the pinned image.** The original helper ran on all 50 official cases in the judge image (`sha256:8afd932de7e5…`) with `--network none --memory 2g --memory-swap 2g --cpus 2`, giving the table above.
- **Source and configuration.** The helper, task JSON and published leaderboard configuration were read to establish where memory is and is not limited.

## Limits

- No model or solver runs. Effects are shown on authored controls and counterexamples only. No leaderboard impact is estimated.
- Runs used a 2 GiB container with 1 to 2 workers, not the official 8 GiB / 8 workers / 4 CPU pod. R3 is a ratio-scaled emulation, and its OOM count depends on timing.
- Each configuration ran once. There are no repeatability statistics for R3.
- Historical deployment overrides are unknown, so a different past memory policy cannot be excluded.
- The no-advantage conclusion is reasoning, not a measured experiment. No strong solver was built.

## Reproduce

- Memory probe on all 50 official cases: `evidence/scripts/molecular_self_assembly/run_memory_probe.sh <MiB> <workers>` with `hog_solution.py`. Outputs are `r1_base_w1.out`, `r2_hog1300_w1.out`, `r3_hog1300_w2.out` and `r4_hog700_w2.out`.
- RLIMIT_AS thread probe: `evidence/scripts/molecular_self_assembly/as_limit_threads_probe.py`, with output in `as_limit_threads_probe.out`.
- Supporting records: `evidence/reviews/molecular_self_assembly.md`.
