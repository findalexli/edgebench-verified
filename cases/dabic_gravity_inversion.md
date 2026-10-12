# Dabic Gravity Inversion (`dabic_gravity_inversion`)

Status: reviewed by the coordinator, 2026-10-12

- **Domain:** Scientific Problems & ML
- **Decision:** Exclude — 42 points come from self-reported results the judge cannot verify. A partial v2 fixes a second, undisclosed form gate, but does not make the task releasable.[^1]

## What the task promises

The prompt says: "Decide for yourself whether to use the model-space or data-space form, how to compute determinants, and in which space to optimize beta." The starter README (line 48) repeats that the choice is "to be determined by the implementer." A skeptic should weigh README line 5, which expands D-ABIC as "Data-space variant of Akaike's Bayesian Information Criterion"; the task text nonetheless leaves the choice open twice, and no solver-visible text says a model-space form loses score.

## What we checked and how

- Source reading of the evaluator `eval_dabic_v2.py`: the behaviour monitor (`BehaviorMonitor.report`) and the penalty function (`structural_penalty_v34`).
- A native run on one E2B worker (8 vCPU): one honest D-ABIC directive in two forms that differ only in the line `FORM = "data"` / `FORM = "model"`, each scored by the verbatim eval command in the pinned judge image with `--network none --cpus 8 --memory 6g`. By Sylvester's identity both forms compute the same ABIC curve.
- Audit fixtures held the self-reported components (B, D) and the keyword-scored report (F) constant in every arm, so only the directive form varied. Their values are not task performance.
- The evaluator's own penalty function applied to each arm's native breakdown with only the hidden-case score C substituted, to show the effect at the strong tier.
- A paired v1/v2 evaluation on one E2B worker with the same inputs, plus an invalid control (log-determinant via `np.linalg.det`) and the empty shipped workspace.
- An independent Nagy prism code passed a Bouguer-slab check (4.1931 vs 4.1934 mGal) as a units sanity check. The script is in `evidence/scripts/dabic_gravity_inversion/`; its output was not saved.
- Original identity: judge image `seededge/edgebench.judge.dabic_gravity_inversion@sha256:fe3dc290…731d`; key files `/opt/evaluator/eval_dabic_v2.py` sha256 `71ca4da8…2409`, `starter/README.md` `a81886fc…7d94`.

## What we found

**Confirmed: 42 points are self-reported (ground for exclusion).** Components B and D (42 points together) are taken from the submission's own reported results; the judge does not recompute them from hidden data. A good-faith solver's score on these components therefore reflects what it reports, not what the judge verifies. Maximum score effect: 42 points unverifiable. (F, the report component, is keyword-scored.)

**Confirmed, narrower: undisclosed data-space-only gate.** The evaluator classifies the form by the shape of the square matrices passed to its monitored log-determinant routines. A model-space directive is marked `is_data_space=false` and `structural_failure=true`. That costs it 3.2 raw points at every tier (the E1 behaviour points) and blocks the uncapped penalty of 1.0, so a model-space submission is capped at 0.5×.

- Example, original evaluator: the data and model forms give the same hidden-case results (C 17.39 vs 17.41), but score 26.82 and 25.77. At this moderate level both were penalised at 0.334, so the observed gap is small.
- Strong tier (C ≥ 26, D ≥ 20, F ≥ 10), via the evaluator's own penalty function: about 89 in data form against about 43 in model form for the same work (88.92 vs 42.86 at C = 26).
- Maximum score effect: up to ~46 points at the strong tier; 3.2 raw points at every tier.

Scorer isolation is outside this release's scope (EdgeBench design choice); the decision here rests on the good-faith findings above.

## Partial repair (not sufficient for release)

The partial v2 fixes the form gate only. It changes one file, the evaluator `eval_dabic_v2.py`, in both places it sits in the judge image so no stale copy remains. It adds `is_model_space`, the mirror of the existing data-space check (most captured square matrices have the hidden cell count as dimension), and uses `uses_abic_form = is_data_space or is_model_space` for the E1 points and the `structural_failure` term. Every threshold, the 0.334/0.5/1.0 tiers, the other behaviour rules, `valid_for_selection` and all other components are unchanged. The task JSON changes only `judge.image_tag`; the work image and solver-visible files are unchanged. Mirroring the check, rather than removing it, keeps the requirement that the log-determinant is taken on an ABIC matrix.

| Arm | Submission | v1 score (raw=norm) | v2 score (raw=norm) | v1 → v2 detail | valid v1/v2 | Exit v1/v2 |
|---|---|---|---|---|---|---|
| Trigger | honest model-space D-ABIC (`FORM="model"`) | **25.77** | **26.81** | E 4.8 → 8.0; `structural_failure` true → false; raw 77.16 → 80.27 | true/true | 0/0 |
| Valid control | honest data-space D-ABIC (`FORM="data"`) | **26.82** | **26.84** | E 8.0 / 8.0; raw 80.31 → 80.35 (C 17.39 → 17.43, run noise) | true/true | 0/0 |
| Invalid control | data form, log-det via `np.linalg.det` (`make_invalid_variant.py`) | 26.91 | 26.86 | `uses_bad_det` true, `structural_failure` true in both; E 7.2 / 7.2 | **false/false** | 0/0 |
| Shipped state | judge image's own workspace (no `outputs/`, nothing submitted) | 0.00 | 0.00 | all components ERROR (files missing) | false/false | 0/0 |

Strong-tier cap (derived; each image's own penalty function on that arm's native breakdown with only C replaced):

| C | data v1 | model v1 | data v2 | model v2 |
|---|---|---|---|---|
| 20 | 0.5 → 41.46 | 0.5 → 39.86 | 0.5 → 41.46 | 0.5 → 41.46 |
| 26 | 1.0 → 88.92 | **0.5 → 42.86** | 1.0 → 88.92 | **1.0 → 88.92** |
| 30 | 1.0 → 92.92 | 0.5 → 44.86 | 1.0 → 92.92 | 1.0 → 92.92 |

In v1 the data/model gap is 1.05; in v2 it is 0.03, within the measured run noise (repeated runs vary by up to 0.15 in C).

**What a full v2 would need.** The judge would have to recompute the B and D components (42 points) from hidden data instead of reading them from the submission's reported results. Until then the task is excluded from this release; the coordinator's disposition note in the paired results says: "a full v2 would need the judge to recompute those components from hidden data."

**Score compatibility.** By code reading, v2 scores equal v1 scores, up to run noise (measured once: the data-space control went 26.82 → 26.84), for every submission classified as data-space and for submissions whose matrices match neither the hidden data nor the hidden cell counts. They are not comparable for model-space submissions, which gain the 3.2 E1 points and, at the strong tier, the uncapped 1.0 penalty. Rescale is unchanged: the task has no `rescale` section, so the maintained harness reports `score_0_100 = None` (`sforge/harness/run_evaluation.py:265`, no clipping); the scores in the tables are raw scores.[^2]

## Limits and what was not run

- No model or solver re-runs; effects are shown on authored controls and counterexamples only.
- One moderate honest implementation (C ≈ 17.4/35) with audit fixtures for B, D and F. The strong-tier effect is computed with the evaluator's own penalty function, not observed with a strong submission. One run per arm.
- Classification still depends on matrix shapes: a correct implementation that computes the log-determinant without passing an N×N or M×M square matrix to a monitored routine (for example a low-rank or iterative estimator) is still marked `structural_failure` in both versions.
- The partial repair does not address the exclusion ground: B and D (42 points) still come from the submission's own reported results, and F is keyword-scored. The repair README says it "does not make the task retainable on its own".
- The invalid control is rejected only through the `valid` flag; its numeric score is not low.
- Hidden cases use the same simulator to generate and invert (acceptable for synthetic tests). SimPEG was not compared locally, and the Xu benchmark constants were not verified.

## Reproduce

- Native two-form run: `evidence/runs/dabic_gravity_inversion-forms/run.sh` (inputs in its `inputs/` folder).
- Paired evaluation: `repairs/dabic_gravity_inversion-v2/paired/run.sh`, with `make_invalid_variant.py` and `penalty_check.py` in the same folder.
- Prism sanity check: `evidence/scripts/dabic_gravity_inversion/prism_forward_check.py`.
- Change: `repairs/dabic_gravity_inversion-v2/repair.patch`, `Dockerfile`, `task.json.in`.
- Supporting records: `repairs/dabic_gravity_inversion-v2/` (`source-lock.json` holds full hashes).

[^1]: `decisions.json` (coordinator, updated) records **exclude**: the form-gate repair is accepted as partial, but self-reported credit remains. Earlier drafts of the decision table listed repair-v2. Separately, the native review gives the model arm as 25.76 (raw 77.13); the paired results give 25.77 (raw 77.16), used here because `decisions.json` and the later paired run agree on it.

[^2]: The paired table's column headers read "raw=norm" and are copied verbatim; per the paired results text and `run_evaluation.py:265`, no normalized score is produced for this task, so the values are raw scores.
