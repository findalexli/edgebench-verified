# Molecular Self Assembly (`molecular_self_assembly`)

Status: reviewed by the coordinator, 2026-10-12

- **Domain:** Combinatorial Optimization
- **Decision:** Retain with note. The evaluator does not enforce the per-solution memory limit; memory is bounded only by one aggregate container limit. We found no mechanism by which extra memory would raise scores.

## What the task promises

The solver writes a `solution.py` that reads stdin, writes stdout, and is "scored on **50 fixed test cases**". The README's "Runtime Limits" table states `| Time limit | 30 seconds / test case |` and `| Memory limit | 1 GB |`. It does not say which memory metric is meant (RSS or address space), which unit (10^9 bytes or GiB), or what happens when the limit is exceeded.

## What we checked and how

- **Source reading.** We read the helper `run_case`. It starts `python3 solution.py` with a 30 s timeout and sets no memory limit. Up to 8 cases run concurrently by default.
- **Harness and configuration audit.** The task JSON sets no memory limit. The published leaderboard configuration sets `judge_mem_limit: "8g"` and `judge_cpu_limit: 4` for the whole judge container. That limit is shared by up to 8 concurrent solution processes and their testers.
- **Native runs.** We ran the original helper on all 50 official cases in the pinned judge image (`--network none --memory 2g --memory-swap 2g --cpus 2`). The test solution allocates N MiB, touches it, then prints the baseline output.
- **Probe of the proposed RLIMIT_AS repair.** We ran a threaded pure-Python program (1 to 64 threads) under `RLIMIT_AS=1e9`.
- **Original identity.**
  - Judge image `seededge/edgebench.judge.molecular_self_assembly@sha256:8afd932de7e54bacee44bcc33ceb4dab1125ad563aa81c1141717f1fc25c6da5`
  - Work image `seededge/edgebench.work.molecular_self_assembly@sha256:1de53ae49b30a46eed70cb5abb8e9a0a9de039cc07eb76ffe5c73b3f0b4ff1c3`
  - `/tmp/eval_molecules.py` sha256 `4faad7b93a842cf17cab13f3ae8b3e67c4c7504a34cb02062a06cdbab985baac`
  - `tools/bin/tester` sha256 `a8fc78c4eaa14af0e9e8750fc053f9661ded504c3c404711d50748f4badfb7e8`
  - `README.md` sha256 `290ee7a37f39522e3b1fd3e6882e8d91e756d89081797f5d6d765c1fe6cad5b9`
  - Task JSON sha256 `e8569e3a…1717`

## What we found

**Confirmed, narrower.** The helper does not enforce the README's 1 GB per-solution limit. The original evaluator gave the following results on all 50 official cases:

| Run | Allocation | Workers | Peak RSS per case | Result |
|---|---|---|---|---|
| R1 (good control) | 0 | 1 | 12.6 MB | 50/50 OK, TOTAL 69,280,072 |
| R2 (trigger) | 1300 MiB | 1 | 1,370,013,696 to 1,370,697,728 B (> 10^9 and > 2^30) | **50/50 OK, TOTAL 69,280,072** (identical) |
| R4 (below-limit control, scaled) | 700 MiB | 2 | 0.74 GB | 50/50 OK, 69,280,072 |
| R3 (scaled aggregate cap, 2 GiB / 2 workers ≈ official 8 GiB / 8) | 1300 MiB | 2 | 1.37 GB | **46/50 OK, 4 RE (OOM-killed), TOTAL 63,747,304** |

- **Expected vs observed (R2).** A solution using about 1.37 GB RSS on every case should be rejected or penalized under a 1 GB limit. Instead it received full credit on all 50 cases, the same total as the good control.
- **What the aggregate cap does (R3).** A container cap partially penalizes a solution that is uniformly over the limit. It lost 4 of 50 cases in this single run. Which cases are lost is expected to depend on timing, but repeats were not run. This is not per-solution enforcement.
- **Maximum score effect.** We found no score mechanism. The task is pure Python (the judge image has no numpy) with a 30 s limit per case. A full pairwise-distance-over-time table fits in about 180 MB, and the time limit binds long before memory does. The hidden cases are not visible to the solution. This conclusion is reasoning; it was not measured.
- **Honest solutions.** The defect is a missing rejection. It does not reject valid submissions.
- **Earlier withholding.** An earlier audit withheld this task because the memory limit is unenforced. Re-checking showed that the unenforced limit has no demonstrated or plausible score effect. The time limit, validity checking and scoring were not challenged. This does not meet the release's bar for exclusion, which is a specific, evidenced reason.
- **RLIMIT_AS repair probe.** All threaded runs succeeded with about 11 MB RSS, so the suspected false rejection from address-space accounting was not reproduced.

## Note for users

No repair. Treat the README's 1 GB memory figure as advisory. Memory is bounded only by the judge container: in the published setting, 8 GiB shared by 8 concurrent cases. That cap penalizes uniformly heavy solutions unpredictably. We found no evidence that extra memory improves scores.

A per-solution limit could be added in a separately versioned variant, using either `RLIMIT_AS` or a post-hoc peak-RSS check. Its scores must not be merged with original scores.

## Limits and what was not run

- No model or solver was re-run. Effects are shown on authored controls and counterexamples only. No leaderboard impact is estimated.
- Runs used a 2 GiB container with 1 to 2 workers, not the official 8 GiB / 8 workers / 4 CPU pod. R3 is a ratio-scaled emulation, and its OOM count depends on timing.
- Each configuration ran once. There are no repeatability statistics for R3.
- Historical deployment overrides are unknown, so a different past memory policy cannot be excluded.
- The no-advantage conclusion is reasoning, not a measured experiment. No strong solver was built.

## Reproduce

- Memory probe on all 50 official cases: `evidence/scripts/molecular_self_assembly/run_memory_probe.sh <MiB> <workers>` with `hog_solution.py`. Outputs are `r1_base_w1.out`, `r2_hog1300_w1.out`, `r3_hog1300_w2.out` and `r4_hog700_w2.out`.
- RLIMIT_AS thread probe: `evidence/scripts/molecular_self_assembly/as_limit_threads_probe.py`, with output in `as_limit_threads_probe.out`.

Supporting records: `evidence/reviews/molecular_self_assembly.md`.

