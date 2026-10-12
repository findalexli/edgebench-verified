# k12_math_recommendation: native addendum (positive control and the earlier failure)

**Question.** Does the original scorer give a finite positive score to the shipped
reference solution when it runs with sound resources? Was the earlier native failure
caused by the audit's own 512 MiB address-space limit?

**Verdict.** CONFIRMED. The original scorer works. Both shipped reference stages score
positively and validly with sound resources. Under the audit's earlier envelope, the
same scorer fails at import time, before any scoring happens. The earlier "setup stopped"
result was caused by the audit infrastructure, not by a task defect. One detail differs:
the failure reproduced here is SIGINT (rc=-2) from OpenBLAS thread creation, not the
SIGKILL recorded earlier.

## Pinned artifacts

- Judge image: `seededge/edgebench.judge.k12_math_recommendation@sha256:6489d4ea0e486d4c2421261c452a3abf099ba4099b587572de149c2fd7be4f72`. The worker pulled it by digest and its image ID was verified.
- Task JSON: `tasks/k12_math_recommendation.json` sha256 `550851358d3cab943dc0cf8ccfd7047afe11c923666855aecf434d3a0d2760ea`. eval_cmd: `cd /home/workspace && python3 scoring/score.py`.
- In the image:
  - `scoring/score.py` `46d0574d…0bea`
  - `eval_resources/evaluate.py` `19f065f9…9df2`
  - `test_ground_truth.json` `5500901a…4d66`
  - stage2 `infer.py` `fc79c36c…0b1c`, `models/advanced.pkl` `878c7d2b…56f6`
  - stage1 `infer.py` `3eac0a1d…0323`, `models/baseline.pkl` `0d3c8663…9b37`

## Commands

- Job: `evidence/runs/k12_math_recommendation-positive/run.sh`.
- E2B worker: `iiq8o1q7zipjmqdanrtly` (8 vCPU, 7.9 GB). It exited 0 after 41 s and was killed, as recorded in `e2b/ledger.jsonl`.
- Each arm ran in a fresh container started with `docker run --rm --network none --cpus C --memory M <image@digest>`. Inside it, the arm copied the shipped `scoring/reference_implementation/<stage>/{train.py,infer.py,requirements.txt,README.md,models/}` into `/home/workspace`, then ran the verbatim `cd /home/workspace && [wrap] timeout T python3 scoring/score.py`.
- Memory was measured from cgroup v2 `memory.peak` and `memory.events`, plus 1 s samples of `memory.current`.

## Results (raw output in `result/out/<arm>/`)

| arm | envelope | outcome | total_score (the reported score; no rescale) | M1 / M2 / M3 / M4 / M5 | cgroup memory.peak | OOM events |
|---|---|---|---|---|---|---|
| stage2_advanced | 6 GiB, 4 CPU, 900 s | valid, `TOTAL_SCORE 24.699` | **24.699** | 9.81 / 39.75 / 14.93 / 96.6 / 100 | 544,985,088 B (≈520 MiB) | 0 |
| stage1_baseline | 6 GiB, 4 CPU, 900 s | valid, `TOTAL_SCORE 17.598` | **17.598** | 10.86 / 25.79 / 3.69 / 98.8 / 100 | 561,098,752 B (≈535 MiB) | 0 |
| stage2_advanced | earlier audit envelope: 1 GiB, 1 CPU, `prlimit --as=536870912 --cpu=120:120`, 178 s | `OpenBLAS blas_thread_init: pthread_create failed for thread 7 of 8`, then `KeyboardInterrupt` while importing scipy/sklearn. evaluate.py rc=-2; score.py prints `SCORER_INFRA_ERROR missing parseable score; rc=-2`, `TOTAL_SCORE 0` | 0 (infra error) | none | 108,732,416 B | 0 |

- Each sound-envelope run took about 8 s end to end; infer took 1.0 to 1.7 s.
- All 100 of 100 scenarios matched. The weights used were M1 .35, M2 .30, M3 .30, M4 .04, M5 .01.

## What this establishes

- **First positive control.** The original evaluator path produces finite, valid, positive scores. The score order (stage2 24.7 > stage1 17.6) matches the authors' description of the two stages.
- The stage1 value, 17.598, reproduces the triage estimate of "≈17.6" exactly. The triage made that estimate with stand-in libraries.
- **The authors' reported scores do not reproduce under the current evaluator.** The shipped `evaluation_report.json` files report 45.292 (stage1) and 50.4 (stage2). The current evaluator gives 17.6 and 24.7. Most of the gap is M1: shipped 44.3/43.6, current 10.9/9.8. This confirms the triage statement that the shipped reports came from an older, looser evaluator. A reader comparing against the published reference numbers would be misled.
- **Memory.** A whole-container peak of about 520 to 535 MiB (page cache included) exceeds a 512 MiB address-space limit. Beyond that, with RLIMIT_AS set to 512 MiB, OpenBLAS cannot create its per-core threads (8 visible cores), and the scorer dies while importing numpy/scipy, before it runs inference or scoring.
- **The earlier native failure.** The earlier failure is therefore explained by the audit's own limits, not by the task. The exact signal differs: SIGINT (rc=-2) here versus the earlier recorded SIGKILL. The earlier host's core count and wrapper may have produced a different failure path. That the audit infrastructure caused it is confirmed; the exact SIGKILL mechanism is not reproduced.

## Change to disposition

- The "setup stopped / pending" blocker is resolved. The task's scorer runs and gives valid positive controls.
- The recommended disposition stays **repair-v2 (withhold original)**, for the reasons recorded in the triage: hidden ground truth is copied into the workspace before `infer.py` runs, and GT is loaded after inference. This run did not test those reasons.
- Add a note: the shipped reference reports (45.3/50.4) are stale relative to the current evaluator (17.6/24.7).

## Limits

- This is one run per arm, but scoring is deterministic given infer output.
- Memory figures are cgroup totals and include page cache. They are not per-process RSS.
- The ground-truth exposure probe (`[internal probe]`) was not re-run here. It is a tamper-style probe and outside the good-faith scope.
