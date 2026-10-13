# K-12 Math Recommendation (`k12_math_recommendation`)

**Outcome:** Kept, with a note. <mark>The original grader gives valid positive scores to both shipped reference solutions, but the shipped example reports are out of date and the grader fails under a tight memory limit.</mark>

## What the task asks

The solver builds a system that recommends math learning content to school students (grades K-12). The task text points to a workspace instruction file: "Read the complete task instructions in `/home/workspace/task_instruction.md`, and complete the task according to those requirements." The score comes from `cd /home/workspace && python3 scoring/score.py`. It reports a `TOTAL_SCORE` built from five weighted measures (M1-M5) over 100 scenarios. Category: Professional Knowledge Work.

## What we checked

No scoring defect was found. The grader works on both shipped reference solutions:

| Test submission | Resource limits | Outcome | total_score (the reported score; the task has no 0–100 score scale) | M1 / M2 / M3 / M4 / M5 | Peak memory of the container (cgroup memory.peak) | Out-of-memory events |
|---|---|---|---|---|---|---|
| stage2_advanced | 6 GiB, 4 CPU, 900 s | valid, `TOTAL_SCORE 24.699` | **24.699** | 9.81 / 39.75 / 14.93 / 96.6 / 100 | 544,985,088 B (≈520 MiB) | 0 |
| stage1_baseline | 6 GiB, 4 CPU, 900 s | valid, `TOTAL_SCORE 17.598` | **17.598** | 10.86 / 25.79 / 3.69 / 98.8 / 100 | 561,098,752 B (≈535 MiB) | 0 |
| stage2_advanced | 1 GiB, 1 CPU, `prlimit --as=536870912 --cpu=120:120`, 178 s | `OpenBLAS blas_thread_init: pthread_create failed for thread 7 of 8`, then `KeyboardInterrupt` while importing scipy/sklearn. evaluate.py rc=-2; score.py prints `SCORER_INFRA_ERROR missing parseable score; rc=-2`, `TOTAL_SCORE 0` | 0 (infrastructure error) | none | 108,732,416 B | 0 |

- All 100 of 100 scenarios matched. The weights were M1 .35, M2 .30, M3 .30, M4 .04, M5 .01. The order (stage2 24.7 > stage1 17.6) matches the authors' description of the two stages. Each run took about 8 s from start to finish.

Two notes ship with the task.

**Out-of-date shipped reports.** The shipped `evaluation_report.json` files report 45.292 (stage1) and 50.4 (stage2). The current grader gives 17.6 and 24.7 for the same reference solutions. Most of the gap is in M1: 44.3/43.6 in the shipped reports against 10.9/9.8 now. The shipped reports appear to come from an older, more lenient grader. A reader who compares against those numbers would be misled.

**Memory limit.** Under a 512 MiB address-space limit with 8 visible cores, the OpenBLAS maths library cannot create its threads, one per core. The grader then dies while importing numpy/scipy, before any inference or scoring (third row above). Under sound limits, the peak memory of the whole container, page cache included, was about 520 to 535 MiB. The address space the grader needs was not measured.

## How much it matters

- Out-of-date reports: documentation only; no score changes.
- Memory limit: affects only graders run under a tight address-space limit. There the grader reports `TOTAL_SCORE 0` with an infrastructure error for every submission.

No change is made; the note above ships with the task.

## How we checked it

- **Original grader in the original public image, pinned by digest** (pulled by digest, image ID verified). The exact `eval_cmd` ran on a host with 8 vCPU and 7.9 GB. Each test submission ran in a fresh `docker run --rm --network none` container.
- **Correct test submissions.** The two shipped reference solutions (`scoring/reference_implementation/<stage>/`, that is `train.py`, `infer.py`, `requirements.txt`, `README.md` and `models/`) were copied into `/home/workspace` and scored.
- **Memory.** Read from cgroup v2 `memory.peak` and `memory.events`, plus samples of `memory.current` taken every 1 s.

## Limits

- No AI model or solver runs were made. Effects are shown only on the shipped reference solutions and one run under tight limits.
- Each test submission ran once. Scoring is deterministic given the `infer` output.
- Memory figures are cgroup totals that include page cache, not the memory of each process (RSS).
- Behaviour under other tight-limit setups (other core counts or wrappers) was not tested. A container memory (cgroup) limit near 512 MiB was not tested; the failing run used an address-space limit.
- Published leaderboard averages for this task (44.3 for Opus 4.8 and 44.0 for GPT-5.5, `evidence/impact/leaderboard_12h.json`) are well above the authors' advanced reference solution, which scores 24.7 under this grader. Where that gap comes from was not examined.

## Reproduce

- Grader image digest: `sha256:6489d4ea0e48…`.
- `evidence/runs/k12_math_recommendation-positive/run.sh`. It needs a Docker host that can pull the pinned image. Outputs are in `result/out/<arm>/`.
- The tight-limit arm (`stage2_audit_envelope`, `prlimit --as=536870912 --cpu=120:120`) is in the same `run.sh`.
- `evidence/scripts/k12_math_recommendation/measure_evaluate.sh` is an earlier measurement script. It needs stub libraries that are not published and uses older directory names, so it does not run as published.
- Review: `evidence/reviews/k12_math_recommendation-native.md`.
