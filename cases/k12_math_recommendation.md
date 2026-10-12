# K-12 Math Recommendation (`k12_math_recommendation`)

**Decision:** Retain with note. The original scorer gives valid positive scores to both shipped reference solutions, but the shipped reference reports are stale and the scorer fails under a tight memory limit.

## What the task asks for

The prompt points to a workspace instruction file: "Read the complete task instructions in `/home/workspace/task_instruction.md`, and complete the task according to those requirements." The score comes from `cd /home/workspace && python3 scoring/score.py`, which reports a `TOTAL_SCORE` built from five weighted metrics (M1-M5) over 100 scenarios. Category: Professional Knowledge Work.

## What goes wrong

No scoring defect was found. The scorer works on both shipped reference solutions:

| arm | envelope | outcome | total_score (the reported score; no rescale) | M1 / M2 / M3 / M4 / M5 | cgroup memory.peak | OOM events |
|---|---|---|---|---|---|---|
| stage2_advanced | 6 GiB, 4 CPU, 900 s | valid, `TOTAL_SCORE 24.699` | **24.699** | 9.81 / 39.75 / 14.93 / 96.6 / 100 | 544,985,088 B (≈520 MiB) | 0 |
| stage1_baseline | 6 GiB, 4 CPU, 900 s | valid, `TOTAL_SCORE 17.598` | **17.598** | 10.86 / 25.79 / 3.69 / 98.8 / 100 | 561,098,752 B (≈535 MiB) | 0 |
| stage2_advanced | 1 GiB, 1 CPU, `prlimit --as=536870912 --cpu=120:120`, 178 s | `OpenBLAS blas_thread_init: pthread_create failed for thread 7 of 8`, then `KeyboardInterrupt` while importing scipy/sklearn. evaluate.py rc=-2; score.py prints `SCORER_INFRA_ERROR missing parseable score; rc=-2`, `TOTAL_SCORE 0` | 0 (infra error) | none | 108,732,416 B | 0 |

- All 100 of 100 scenarios matched. The weights were M1 .35, M2 .30, M3 .30, M4 .04, M5 .01. The order (stage2 24.7 > stage1 17.6) matches the authors' description of the two stages. Each run took about 8 s end to end.

Two notes ship with the task.

**Stale shipped reports.** The shipped `evaluation_report.json` files report 45.292 (stage1) and 50.4 (stage2). The current evaluator gives 17.6 and 24.7 for the same references. Most of the gap is M1: 44.3/43.6 shipped versus 10.9/9.8 now. The shipped reports appear to come from an older, looser evaluator. A reader comparing against those numbers would be misled.

**Memory limit.** Under a 512 MiB address-space limit with 8 visible cores, OpenBLAS cannot create its per-core threads, and the scorer dies while importing numpy/scipy, before inference or scoring (third row above). Under sound limits the whole-container cgroup peak, page cache included, was about 520 to 535 MiB. The address space it needs was not measured.

## Impact

- Stale reports: documentation only; no score changes.
- Memory limit: affects only judges run under a tight address-space limit. There the scorer reports `TOTAL_SCORE 0` with an infrastructure error for every submission.

## Fix (v2)

No change; the note above ships with the task.

## How we know

- **Original evaluator in the pinned image.** The verbatim eval_cmd ran in the judge image (`sha256:6489d4ea0e48…`, pulled by digest, image ID verified) on an 8 vCPU, 7.9 GB host. Each arm ran in a fresh `docker run --rm --network none` container.
- **Positive controls.** The two shipped reference solutions (`scoring/reference_implementation/<stage>/`, that is `train.py`, `infer.py`, `requirements.txt`, `README.md` and `models/`) were copied into `/home/workspace` and scored.
- **Memory.** Read from cgroup v2 `memory.peak` and `memory.events`, plus 1 s samples of `memory.current`.

## Limits

- No model or solver runs. Effects are shown on the shipped reference solutions and one constrained run only.
- One run per arm. Scoring is deterministic given the `infer` output.
- Memory figures are cgroup totals that include page cache, not per-process RSS.
- Behaviour under other tight-limit setups (other core counts or wrappers) was not tested.

## Reproduce

- `evidence/runs/k12_math_recommendation-positive/run.sh`. It needs a Docker host that can pull the pinned image. Outputs are in `result/out/<arm>/`.
- `evidence/scripts/k12_math_recommendation/measure_evaluate.sh` and `measure_evaluate_limited.sh`.
- Review: `evidence/reviews/k12_math_recommendation-native.md`.
