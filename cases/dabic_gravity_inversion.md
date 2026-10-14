# D-ABIC Gravity Inversion (`dabic_gravity_inversion`)

**Outcome:** Removed. <mark>42 points come from results the submission reports about itself, which the grader cannot verify. A partial fix removes a second, undisclosed penalty on one of two allowed forms, but it does not make the task usable.</mark>

![A 100-point bar split into 35 points the checker recomputes by running the code on hidden test cases, 42 points (12 + 30) read from the submission's own results file and never verified, and 23 points from other checks (code text 3, behaviour monitor 8, report keywords 12). A box explains that a sound fix would need the checker to recompute the 42 points itself, and a note mentions a second, fixed problem: one of two allowed method forms was penalised (88.92 against 42.86 out of 100 for the same strong work).](figures/dabic_gravity_inversion.svg)

*42 of the 100 points come from numbers the submission reports about its own work, and the checker never verifies them, so the task was removed. The agent implements the D-ABIC gravity inversion method. The checker recomputes only 35 points, by running the code on hidden test cases; two parts, worth 12 and 30 points, are scored from the submission's own results file as written. A sound fix would need the checker to recompute those 42 points from hidden data itself. A second problem was fixed but did not save the task: one of two allowed, equivalent method forms carried a hidden penalty (88.92 against 42.86 out of 100 for the same strong work at C = 26, computed from the checker's own rule; the gap grows with C).*

## What the task asks

The solver implements a D-ABIC gravity inversion, a method that infers underground density from gravity measurements and picks its regularization strength (beta) with Akaike's Bayesian Information Criterion (ABIC). The method can be written in two equivalent forms. The model-space form works with matrices sized by the number of hidden model cells. The data-space form works with matrices sized by the number of data points.

The task text says, "Decide for yourself whether to use the model-space or data-space form, how to compute determinants, and in which space to optimize beta." The starting README (line 48) repeats that the choice is "to be determined by the implementer." README line 5 expands D-ABIC as "Data-space variant of Akaike's Bayesian Information Criterion". Even so, the task text leaves the choice open twice, and no text the solver can see says that the model-space form loses score. The task is in the Scientific Problems & ML category.

## What goes wrong

We removed the task because 42 points are self-reported. The grader takes components B and D (42 points together) from results the submission reports about itself and does not recompute them from hidden data. Even for a solver that reports truthfully, these components reflect what the submission reports, not what the grader verifies. The grader scores component F, the written report, by keywords.

The grader also has an undisclosed requirement to use the data-space form. It decides which form a submission uses from the shape of the square matrices passed to the log-determinant routines it monitors. It marks a model-space submission `is_data_space=false` and `structural_failure=true`. That costs the submission 3.2 points of the total before the penalty factor, at every level of quality. These are the E1 behaviour points. It also blocks the uncapped penalty factor of 1.0, so the grader caps a model-space submission at a factor of 0.5×. By Sylvester's determinant identity, both forms compute the same ABIC curve.

- On the original grader, the data and model forms give the same results on the hidden cases up to run noise (C 17.39 against 17.44), but they score 26.82 and 25.77 (`repairs/dabic_gravity_inversion-v2/paired/evidence/logs/{data,model}-v1.structured.json`). At this moderate level both received the penalty factor 0.334, so the observed gap is small.
- At a strong level (C ≥ 26, D ≥ 20, F ≥ 10), applying the grader's own penalty function gives about 89 in the data form against about 43 in the model form for the same work (88.92 against 42.86 at C = 26).

## How much it matters

- For every solver, the grader cannot verify the 42 self-reported points.
- Solvers who choose the model-space form lose 3.2 points of the pre-penalty total at every level. At the strong level the form penalty, computed from the grader's own rule, is 46.06 points at C = 26 and 48.06 at C = 30 (the gap grows with C).

## The fix

The fixed version is partial. It removes only the form penalty and does not address the reason for removal. The end of this section says what a full fix would need.

The fix changes one file, the grader `eval_dabic_v2.py`, in both places where it sits in the grader image. It adds `is_model_space`, which mirrors the existing data-space check and is true when most captured square matrices have the hidden cell count as their dimension. It then uses `uses_abic_form = is_data_space or is_model_space` for the E1 points and for the `structural_failure` term. Every threshold, the 0.334/0.5/1.0 penalty levels, the other behaviour rules, `valid_for_selection` and all other components stay as they were. The task JSON changes only `judge.image_tag`, and the work image and the files the solver sees do not change. We mirrored the check instead of removing it so that the log-determinant must still be taken on an ABIC matrix.

The tables below show raw results. The task has no `rescale` section, which would define the score scale, so EdgeBench's harness reports `score_0_100 = None` (`sforge/harness/run_evaluation.py:265`, no clipping). We keep the column label "raw=norm" from the side-by-side results file, because the raw result and the reported score are the same number here. Each score is the total before the penalty, multiplied by the penalty factor (for the data form, 80.31 × 0.334 = 26.82; `paired/evidence/summary.txt`).

| Test submission | Submission | Original grader score (raw=norm) | Fixed grader score (raw=norm) | Detail, original → fixed | Valid, original/fixed | Exit code, original/fixed |
|---|---|---|---|---|---|---|
| Shows the problem | good-faith model-space D-ABIC (`FORM="model"`) | **25.77** | **26.81** | E 4.8 → 8.0; `structural_failure` true → false; pre-penalty total 77.16 → 80.27 | true/true | 0/0 |
| Correct submission | good-faith data-space D-ABIC (`FORM="data"`) | **26.82** | **26.84** | E 8.0 / 8.0; pre-penalty total 80.31 → 80.35 (C 17.39 → 17.43, run noise) | true/true | 0/0 |
| Invalid submission | data form, log-determinant via `np.linalg.det` (`make_invalid_variant.py`) | 26.91 | 26.86 | `uses_bad_det` true, `structural_failure` true in both; E 7.2 / 7.2 | **false/false** | 0/0 |
| Shipped state | the grader image's own workspace (no `outputs/`, nothing submitted) | 0.00 | 0.00 | all components ERROR (files missing) | false/false | 0/0 |

The next table shows the cap at the strong level. These values are derived, not observed. We applied each grader image's own penalty function to that test submission's real breakdown, replacing only C. Each cell gives the penalty factor and the resulting score.

| C | Data form, original grader | Model form, original grader | Data form, fixed grader | Model form, fixed grader |
|---|---|---|---|---|
| 20 | 0.5 → 41.46 | 0.5 → 39.86 | 0.5 → 41.46 | 0.5 → 41.46 |
| 26 | 1.0 → 88.92 | **0.5 → 42.86** | 1.0 → 88.92 | **1.0 → 88.92** |
| 30 | 1.0 → 92.92 | 0.5 → 44.86 | 1.0 → 92.92 | 1.0 → 92.92 |

On the original grader, the gap between the data and model forms is 1.05. On the fixed grader it is 0.03, within the measured run noise (repeated runs vary by up to 0.15 in C).

A full fix would need the grader to recompute the B and D components (42 points) from hidden data, instead of reading them from the results the submission reports. Until then the task stays removed.

From reading the code, scores from the fixed grader equal scores from the original grader, up to run noise, for every submission classified as data-space. We measured this once, and the correct data-space submission went from 26.82 to 26.84. The same holds for submissions whose matrices match neither the hidden data count nor the hidden cell count. Scores are not comparable for model-space submissions, which gain the 3.2 E1 points and, at the strong level, the uncapped penalty factor 1.0. The score scale does not change.

## How we checked it

- We ran the original grader in the original public image, pinned by digest, using the exact evaluation command with `--network none --cpus 8 --memory 6g`. We scored one D-ABIC submission in two forms that differ only in the line `FORM = "data"` / `FORM = "model"`. Fixed input files held the self-reported components (B, D) and the keyword-scored report (F) constant in every test submission, so only the form varied. Their values are not task performance.
- We read the source of the behaviour monitor (`BehaviorMonitor.report`) and the penalty function (`structural_penalty_v34`).
- For the effect at the strong level, we applied the grader's own penalty function to each test submission's real breakdown, substituting only the hidden-case score C.
- We ran the original and fixed graders side by side on the same inputs, plus an invalid submission (log-determinant via `np.linalg.det`) and the empty shipped workspace. We repeated this three times, and no test submission changed outcome (see `data/paired-repeatability.md`).
- To check units, an independent prism gravity code (Nagy's formula) passed a check against an infinite flat slab (the Bouguer slab). We did not save its output.

## Limits

- We made no AI model or solver runs. The effects shown come only from test submissions and counterexamples that we wrote.
- We used one moderate good-faith implementation (C ≈ 17.4/35), with fixed input files for B, D and F. We computed the effect at the strong level with the grader's own penalty function; we did not observe it with a strong submission.
- The form classification still depends on matrix shapes. A correct implementation that computes the log-determinant without passing an N×N or M×M square matrix to a monitored routine (for example a low-rank or iterative estimator) is still marked `structural_failure` in both versions.
- The partial fix does not address the reason for removal. B and D (42 points) still come from results the submission reports about itself, and F is scored by keywords. The fix's README says it "does not make the task retainable on its own".
- The grader rejects the invalid submission only through the `valid` flag, and its numeric score is not low.
- The hidden cases use the same simulator to generate and to invert the data, which is acceptable for synthetic tests. We did not compare against SimPEG or verify the Xu benchmark constants.

## Reproduce

- Grader image digest: `sha256:fe3dc290…`.
- Run of the two forms on the original grader: `evidence/runs/dabic_gravity_inversion-forms/run.sh` (inputs in its `inputs/` folder).
- Side-by-side run: `repairs/dabic_gravity_inversion-v2/paired/run.sh` (the folder holding the fixed version), with `make_invalid_variant.py` and `penalty_check.py` in the same folder.
- Prism sanity check: `evidence/scripts/dabic_gravity_inversion/prism_forward_check.py`.
- Change: `repairs/dabic_gravity_inversion-v2/repair.patch`, `Dockerfile`, `task.json.in`.
- Supporting records: `repairs/dabic_gravity_inversion-v2/` (`source-lock.json` holds full hashes).
