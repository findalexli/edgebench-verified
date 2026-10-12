# K-12 Math Recommendation (`k12_math_recommendation`)

Status: reviewed by the coordinator, 2026-10-12

- **Domain:** Professional Knowledge Work
- **Decision:** Retain with note — the original scorer gives valid positive scores to both shipped reference solutions. The earlier failure came from the audit's own resource limit, and the shipped reference reports are stale.

## What the task promises

The prompt points to a workspace instruction file: "Read the complete task instructions in `/home/workspace/task_instruction.md`, and complete the task according to those requirements." The score comes from `cd /home/workspace && python3 scoring/score.py`, which reports a `TOTAL_SCORE` built from five weighted metrics (M1-M5) over 100 scenarios.

## What we checked and how

- Native run of the verbatim eval_cmd in the pinned judge image (pulled by digest, image ID verified) on one E2B worker (8 vCPU, 7.9 GB). Each arm ran in a fresh `docker run --rm --network none` container.
- Positive controls: the two shipped reference solutions (`scoring/reference_implementation/<stage>/`, that is `train.py`, `infer.py`, `requirements.txt`, `README.md` and `models/`), copied into `/home/workspace` and scored under 6 GiB, 4 CPU and 900 s.
- The same stage2 arm re-run under the earlier audit's envelope: 1 GiB, 1 CPU, `prlimit --as=536870912 --cpu=120:120`, 178 s.
- Memory read from cgroup v2 `memory.peak` and `memory.events`, plus 1 s samples of `memory.current`.
- Original identity: judge image `seededge/edgebench.judge.k12_math_recommendation@sha256:6489d4ea0e48…`; task JSON sha256 `55085135…`; key files in the image: `scoring/score.py` `46d0574d…0bea`, `eval_resources/evaluate.py` `19f065f9…9df2`, `test_ground_truth.json` `5500901a…4d66`, stage2 `infer.py` `fc79c36c…0b1c` and `models/advanced.pkl` `878c7d2b…56f6`, stage1 `infer.py` `3eac0a1d…0323` and `models/baseline.pkl` `0d3c8663…9b37`.

## What we found

**An earlier audit left this task pending after a native failure. Re-checking showed that the failure was caused by the audit's own limits, not by the task.**

| arm | envelope | outcome | total_score (the reported score; no rescale) | M1 / M2 / M3 / M4 / M5 | cgroup memory.peak | OOM events |
|---|---|---|---|---|---|---|
| stage2_advanced | 6 GiB, 4 CPU, 900 s | valid, `TOTAL_SCORE 24.699` | **24.699** | 9.81 / 39.75 / 14.93 / 96.6 / 100 | 544,985,088 B (≈520 MiB) | 0 |
| stage1_baseline | 6 GiB, 4 CPU, 900 s | valid, `TOTAL_SCORE 17.598` | **17.598** | 10.86 / 25.79 / 3.69 / 98.8 / 100 | 561,098,752 B (≈535 MiB) | 0 |
| stage2_advanced | earlier audit envelope: 1 GiB, 1 CPU, `prlimit --as=536870912 --cpu=120:120`, 178 s | `OpenBLAS blas_thread_init: pthread_create failed for thread 7 of 8`, then `KeyboardInterrupt` while importing scipy/sklearn. evaluate.py rc=-2; score.py prints `SCORER_INFRA_ERROR missing parseable score; rc=-2`, `TOTAL_SCORE 0` | 0 (infra error) | none | 108,732,416 B | 0 |

- **Positive control (Confirmed).** The original evaluator path gives finite, valid, positive scores. All 100 of 100 scenarios matched. The weights were M1 .35, M2 .30, M3 .30, M4 .04, M5 .01. The order (stage2 24.7 > stage1 17.6) matches the authors' description of the two stages. Each run took about 8 s end to end.
- **The earlier failure was the audit's own limit (Confirmed, narrower).** Under sound limits the whole-container cgroup peak (page cache included, not address space) was about 520 to 535 MiB. Under a 512 MiB address-space limit, OpenBLAS cannot create its per-core threads (8 visible cores), and the scorer dies while importing numpy/scipy, before inference or scoring. One detail differs from the earlier record: this run gave SIGINT (rc=-2), not the SIGKILL recorded earlier. That the audit infrastructure caused the failure is confirmed; the exact SIGKILL path was not reproduced.
- **Stale shipped reports (Confirmed).** The shipped `evaluation_report.json` files report 45.292 (stage1) and 50.4 (stage2). The current evaluator gives 17.6 and 24.7. Most of the gap is M1: 44.3/43.6 shipped versus 10.9/9.8 now. This matches an earlier triage finding that the shipped reports came from an older, looser evaluator. A reader comparing against the published reference numbers would be misled. This affects documentation only, not scoring.
- Scorer isolation is outside this release's scope (EdgeBench design choice); no good-faith scoring defect was found.

## Note for users

No repair. The note says:

- The shipped reference reports (45.3/50.4) are stale relative to the current evaluator, which scores the same references 17.6 (stage1) and 24.7 (stage2).
- The scorer fails under a 512 MiB address-space limit with 8 visible cores, because OpenBLAS cannot start its threads. Under sound limits the whole-container cgroup peak, page cache included, was about 520 to 535 MiB. The address space it needs was not measured.

## Limits and what was not run

- No model or solver re-runs. Effects are shown on the shipped reference solutions and one constrained re-run only.
- One run per arm. Scoring is deterministic given the `infer` output.
- Memory figures are cgroup totals that include page cache, not per-process RSS.
- The earlier SIGKILL mechanism was not reproduced, since the earlier host's core count and wrapper may have differed.

## Reproduce

- `evidence/runs/k12_math_recommendation-positive/run.sh`. It needs a Docker host that can pull the pinned image. Outputs are in `result/out/<arm>/`.
- `evidence/scripts/k12_math_recommendation/measure_evaluate.sh` and `measure_evaluate_limited.sh`.
- Review: `evidence/reviews/k12_math_recommendation-native.md`.

