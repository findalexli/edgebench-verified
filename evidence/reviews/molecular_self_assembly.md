# Review: `molecular_self_assembly` (memory-limit enforcement)

> **Note (2026-10-12).** Not covered below: the dependence of scores on the grader's CPU count (8 cases at once under a 30 s wall-clock limit on the published 4 grader CPUs). See `cases/molecular_self_assembly.md`.

> **Note (2026-10-12, later).** The CPU dependence is now measured and fixed in a new version (`repairs/molecular_self_assembly-v2/`): the grader runs at most as many cases at once as its CPU quota. Measured at 4 and 8 CPUs (`evidence/runs/molecular_self_assembly-cpu4v8`, `molecular_self_assembly-v2-paired`). The memory findings below are unchanged and still ship as a note. See `cases/molecular_self_assembly.md`.

Reviewer: Claude (critical re-verification pass), 2026-10-11. Independent rerun from the original image bytes; no E2B or cloud.

## Claim under review

Earlier claim (docs/FINDINGS.md, TASKS.md row): "The original helper and published configuration do not enforce the stated per-solution memory limit. Above-limit acceptance was measured under our explicit 2 GiB regime. Historical host policy and score gain remain unknown."
Earlier disposition: **Withhold original** (`ADOPT_EXACT_ORIGINAL_WITHHOLDING`, evidence/selected/molecular-original-exclusion.json). The proposed repair (proposedrepairs/molecular-memory/) adds a per-process `RLIMIT_AS` of 1,000,000,000 bytes plus README text.

## Pinned artifacts

| Item | Identity |
|---|---|
| Task JSON `tasks/molecular_self_assembly.json` | sha256 `e8569e3a…1717` (repo HEAD `92be4bf`) |
| Judge image | `seededge/edgebench.judge.molecular_self_assembly@sha256:8afd932de7e54bacee44bcc33ceb4dab1125ad563aa81c1141717f1fc25c6da5` (pulled) |
| Work image | `seededge/edgebench.work.molecular_self_assembly@sha256:1de53ae49b30a46eed70cb5abb8e9a0a9de039cc07eb76ffe5c73b3f0b4ff1c3` (pulled) |
| `/tmp/eval_molecules.py` (helper) | `4faad7b93a842cf17cab13f3ae8b3e67c4c7504a34cb02062a06cdbab985baac` |
| `tools/bin/tester` | `a8fc78c4eaa14af0e9e8750fc053f9661ded504c3c404711d50748f4badfb7e8` |
| `README.md`, same in judge and work images | `290ee7a37f39522e3b1fd3e6882e8d91e756d89081797f5d6d765c1fe6cad5b9` |
| `cases/*`, aggregate sha256 of the `sha256sum` listing | `f9cacbc6…60cd` (image matches `$W/work/task-sources/merged` copy) |
| `tasks/BENCHMARK.yaml` | `143838b7…e918`, which has no memory or CPU keys |
| Published leaderboard config `$W/work/edgebench-source/examples/all-tasks-k8s/experiment.yaml` | `d9d29979…43be` |
| harness `sforge/harness/run_evaluation.py`, `backend/docker_backend.py`, `backend/k8s_backend.py`, `backend/e2b_backend.py` | `cbc6cd92…`, `e56e6a71…`, `30eceb51…`, `716b6474…` |

## Contract

README "Runtime Limits" table: `| Time limit | 30 seconds / test case |`, `| Memory limit | 1 GB |`, `| GPU | Not available |`. "Python 3.10+. Your solution should be a single file `solution.py`". The README does not define the memory metric (RSS or address space), the unit (10^9 bytes or GiB), or say what happens when the limit is exceeded. The work-image `tools/README.md` (sha `744aad45…`) says nothing about memory. The judge image has no numpy, so solutions are pure Python 3.10.20.

Evaluator: `run_case` calls `subprocess.run(["python3","solution.py"], …, timeout=30)` and sets no memory limit. Up to `SEBENCH_MOLECULES_WORKERS` (default 8, and the harness never sets it) cases run at once in a `ProcessPoolExecutor`.

## Is the limit enforced at container level? (the main skeptical question)

- Task JSON has no `work.mem_limit` or `judge.mem_limit`. `task_spec.py:231-232` reads them as `None`. `BENCHMARK.yaml` has no limits.
- Judge limits resolve as config over task (`run_evaluation.py:164-165`, `judge_server.py:595-600`). Docker forwards `mem_limit` only when it is not None (`docker_backend.py:124-125`). K8s turns it into one pod container request and limit (`k8s_backend.py:214-224`). E2B ignores per-container limits (`e2b_backend.py:265-270`).
- The published "OFFICIAL EDGEBENCH LEADERBOARD SETTING" (`experiment.yaml`) sets `judge_cpu_limit: 4` and `judge_mem_limit: "8g"`, with `molecular_self_assembly: {}`, meaning no override.

So the harness does apply a container-level limit, but it is **one aggregate 8 GiB limit for 8 concurrent solution processes plus their testers**. It is not a 1 GB limit per solution. That works out to about 1 GiB per worker on average. It can bite a solution that is over the limit on every case, but it does so nondeterministically, and it allows any single process up to almost 8 GiB. I confirm the earlier source finding, and I add the scaled measurement below.

## Independent reproduction

Scripts are in `evidence/scripts/molecular_self_assembly/`. `run_memory_probe.sh <MiB> <workers>` runs the **original helper on all 50 official cases** in the pinned judge image with `--network none --memory 2g --memory-swap 2g --cpus 2`. In-container `memory.max` = 2147483648. The solution (`hog_solution.py`) allocates and touches N MiB, then prints the baseline output, and records its own peak RSS.

| Run | Allocation | Workers | Peak RSS per case | Result |
|---|---|---|---|---|
| R1 (good control) | 0 | 1 | 12.6 MB | 50/50 OK, TOTAL 69,280,072 |
| R2 (trigger) | 1300 MiB | 1 | 1,370,013,696 to 1,370,697,728 B (> 10^9 and > 2^30) | **50/50 OK, TOTAL 69,280,072** (identical) |
| R4 (below-limit control, scaled) | 700 MiB | 2 | 0.74 GB | 50/50 OK, 69,280,072 |
| R3 (scaled aggregate cap, 2 GiB / 2 workers ≈ official 8 GiB / 8) | 1300 MiB | 2 | 1.37 GB | **46/50 OK, 4 RE (OOM-killed), TOTAL 63,747,304** |

Outputs: `r1_base_w1.out`, `r2_hog1300_w1.out`, `r4_hog700_w2.out`, `r3_hog1300_w2.out`.

R2 reproduces the claim on all 50 cases, not just one: the original helper gives full credit to a solution whose every process uses 1.37 GB RSS. R3 shows how an aggregate container cap behaves. A solution that is uniformly over the limit loses an unpredictable subset of cases (4 of 50 here), depending on how the concurrent runs overlap. Neither run gives per-solution enforcement.

## Refutation attempts

1. **"The container runtime enforces it."** Refuted for the configurations available to us. No 1 GB per-solution limit exists in the task, the harness defaults or the published config. The 8 GiB aggregate cap is real and is a partial, nondeterministic deterrent (R3), not the stated contract. A historical deployment with a different override cannot be excluded.
2. **"Exceeding memory gives a score advantage."** I found no plausible mechanism, but **I did not measure this**. The input is 300 points × 1000 steps. A full pairwise-distance-over-time table has 300·299/2·1000 ≈ 4.5×10^7 entries, which is about 180 MB in a pure-Python `array('i')`, well under 1 GB. Precomputing it in pure Python would take on the order of 10^7–10^8 interpreter operations, so the 30 s CPU limit binds long before memory does. The hidden cases are not visible to the solution, so a lookup table of answers is impossible: the judge copies only `solution.py`. My inference is that above-limit memory is unlikely to give a material score advantage. It is not a measured result.
3. **Does it change the score of honest solutions?** No. The defect is a missing rejection. It does not reject valid submissions.
4. **Proposed repair false-reject risk.** I tested a threaded pure-Python program (1 to 64 threads) under `RLIMIT_AS=1e9` in the judge image. All runs succeeded with RSS of about 11 MB (`as_limit_threads_probe.out`), so I could not show the arena/stack false-reject I suspected. AS accounting still differs from RSS, and the repair's own README text says so.

## Formal check

None. This is a resource-policy question, and no mathematical uncertainty would be reduced by a formal tool.

## Verdict

**CONFIRMED-NARROWER.** The factual claim holds: the helper does not enforce the README's 1 GB per-solution limit, and a 1.37 GB-RSS solution got full credit on all 50 cases. Two qualifications are missing from the earlier wording. First, the published configuration *does* impose an aggregate 8 GiB/8-worker container cap that partially and nondeterministically penalizes solutions that are over the limit on every case. Second, no score advantage from exceeding the limit has been shown, and none is plausible for this pure-Python, 30-second task.

## Disposition assessment

**I disagree with "withhold original."** VERIFICATION.md requires an exclusion to rest on a "specific, evidenced reason". It also says not to exclude merely because a task is difficult to inspect. The evidenced reason here is an unenforced limit that has no demonstrated or plausible effect on scores. Many contest-style benchmarks state resource limits that the harness enforces only loosely. Withholding removes a sound optimization task (the time limit, validity checking and scoring were not challenged) to fix a documentation-versus-enforcement gap.

Proportionate options:
- (a) **Retain with a documented-enforcement note.** The note would say that memory is bounded only by the judge container (8 GiB for 8 concurrent cases in the published setting) and that the 1 GB figure is advisory.
- (b) **Repair as a versioned variant** with a per-solution limit.

I recommend (a) for the original. Optionally, ship (b) as a separately identified version.

## Recommended publishable wording

"The Molecular evaluator does not enforce the README's 1 GB per-solution memory limit. A solution using 1.37 GB RSS per case received full credit on all 50 cases. The published configuration only bounds memory per judge container (8 GiB shared by 8 concurrent cases), which penalizes uniformly heavy solutions unpredictably. We found no evidence that extra memory improves scores, so we retain the task and document that the limit is advisory."

## Repair note

The proposed `RLIMIT_AS = 1_000_000_000` patch is correct as a *versioned* policy. It is minimal, it keeps stricter inherited limits, and its README text honestly says AS is not RSS. A closer match to the usual contest convention (to my knowledge AtCoder measures peak RSS and AHC057 itself stated 1024 MiB; not re-verified here) would be a post-hoc check: run the child with `os.wait4` or `resource.getrusage(RUSAGE_CHILDREN)` and score the case as memory-exceeded if peak RSS exceeds the limit. That check has no address-space false rejects. Whichever check is chosen, the README should state the unit, the metric and the consequence. Scores from the new version must not be merged with original scores.

## Limits

- Runs used a 2 GiB container and 1–2 workers, not the official 8 GiB / 8 workers / 4 CPU K8s pod. R3 is a ratio-scaled emulation, and its OOM count depends on timing.
- Historical deployment overrides are unknown.
- The score-advantage conclusion is reasoning, not a measured experiment, because no strong solver was built.
- Single run per configuration; no repeatability statistics for R3.
