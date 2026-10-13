# Paired v1/v2 results: dabic_gravity_inversion

- **Job:** one E2B worker (8 CPU), job `dabic_gravity_inversion-v2-paired`, sandbox
  `i5cc6dgdxgdtcuuv4jl5u`. It exited 0 after 343 s and was killed after collection
  (`evidence/worker.json`).
- **Images:** v1 is the pinned `seededge/edgebench.judge.dabic_gravity_inversion@sha256:fe3dc290…731d`.
  v2 was built in the worker from `../Dockerfile`, image ID `sha256:9c01fcfc…353b`.
- **Evaluator hashes in the containers** (`evidence/eval_sha.txt`): v1 `71ca4da8…2409` (both copies),
  v2 `c8cc7430…cabe` (both copies).
- **Command:** every arm ran the original `eval_cmd`
  `cd /home/workspace/dabic_gravity_vinton && PYTHONPATH=/opt/evaluator python /opt/evaluator/eval_dabic_v2.py /home/workspace/dabic_gravity_vinton/outputs/`
  with `--network none --cpus 8 --memory 6g`, one container at a time. Each arm's submission was
  copied fresh into its own directory and bind-mounted over `outputs/`.
- **Inputs** are reused unchanged from `evidence/runs/dabic_gravity_inversion-forms/inputs/`
  (see [the native review](../../../evidence/reviews/dabic_gravity_inversion-native.md)). `data` and `model`
  are the same D-ABIC directive, differing only in `FORM = "data"` / `"model"`. B, D and F are
  driven by the same audit fixtures (`results_fixture.json`, `report_fixture.md`) in every arm,
  so their values are not task performance.
- **Scores:** raw = structured-result `score` (`structured_json` parser). The task JSON has no
  `rescale` section; EdgeBench's harness then reports `score_0_100 = None` (`sforge/harness/run_evaluation.py:265`, no clipping), so raw scores are reported here. There are no pass/fail test units;
  the pass column is the evaluator's `valid` flag (`valid_for_selection`, used by
  `selection: valid_then_score`). All containers exited 0.

| Arm | Submission | v1 score (raw=norm) | v2 score (raw=norm) | v1 → v2 detail | valid v1/v2 | Exit v1/v2 |
|---|---|---|---|---|---|---|
| Trigger | honest model-space D-ABIC (`FORM="model"`) | **25.77** | **26.81** | E 4.8 → 8.0; `structural_failure` true → false; pre-penalty total 77.16 → 80.27 | true/true | 0/0 |
| Valid control | honest data-space D-ABIC (`FORM="data"`) | **26.82** | **26.84** | E 8.0 / 8.0; pre-penalty total 80.31 → 80.35 (C 17.39 → 17.43, run noise) | true/true | 0/0 |
| Invalid control | data form, log-det via `np.linalg.det` (`make_invalid_variant.py`) | 26.91 | 26.86 | `uses_bad_det` true, `structural_failure` true in both; E 7.2 / 7.2 | **false/false** | 0/0 |
| Shipped state | judge image's own workspace (no `outputs/`, nothing submitted) | 0.00 | 0.00 | all components ERROR (files missing) | false/false | 0/0 |

**Two-form equality.** v1: data 26.82 vs model 25.77 (gap 1.05 = 3.2 pre-penalty points × 0.334 plus noise).
v2: data 26.84 vs model 26.81 (gap 0.03). Repeated runs of the *same* submission vary by up to
0.15 in C (e.g. invalid 17.45 vs 17.30), so the v2 forms are equal within measured noise.

**Strong-tier cap (derived, `evidence/penalty_check.txt`).** Each image's own
`structural_penalty_v34` was applied to that arm's native breakdown with only C replaced:

| C | data v1 | model v1 | data v2 | model v2 |
|---|---|---|---|---|
| 20 | 0.5 → 41.46 | 0.5 → 39.86 | 0.5 → 41.46 | 0.5 → 41.46 |
| 26 | 1.0 → 88.92 | **0.5 → 42.86** | 1.0 → 88.92 | **1.0 → 88.92** |
| 30 | 1.0 → 92.92 | 0.5 → 44.86 | 1.0 → 92.92 | 1.0 → 92.92 |

This executes the evaluator's own penalty code in both images, but the C values are substituted,
not produced by a strong submission.

**Verdict: accepted.**
1. Trigger: the model-space form loses 3.2 pre-penalty points and the uncapped tier in v1 and is treated
   like the data-space form in v2 (observed end to end at the immature tier; strong-tier cap
   removal shown with the evaluator's own penalty function).
2. Valid control: the data-space form is unchanged (E, flags and penalty identical; score differs
   only by run noise in C).
3. Invalid controls: the `np.linalg.det` directive is `valid=false` with `structural_failure` in
   both versions, and the empty shipped state scores 0 / invalid in both.

**Limits of this evaluation.** The invalid control's numeric score is not low (fixture-driven B/D/F,
and `det` of these diagonal matrices did not overflow here); it is rejected only by the
`valid` flag, identically in both versions. There is no shipped reference solution in the
judge image, so the "shipped" arm is the empty workspace. One run per arm.

**Evidence** (`evidence/`): `summary.txt`, `penalty_check.txt`, `eval_sha.txt`, `v2_image_id.txt`,
`submissions_sha.txt`, `shipped_workspace_ls.txt`, `build.log`, `env.txt`, `worker.json`,
`logs/*.structured.json` (each arm's structured result), `logs/*.tail.txt` (last 3 KB of each log).
Full logs and `eval_result.json` files are in `evidence/runs/dabic_gravity_inversion-v2-paired/result/out/logs/`.


**Coordinator disposition (2026-10-12):** this partial repair fixes the form gate only. Because 42 points remain self-reported and unverifiable, the task is **excluded** from this release; a full v2 would need the judge to recompute those components from hidden data.
