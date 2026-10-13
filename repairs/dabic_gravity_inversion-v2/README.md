# dabic_gravity_inversion, fixed version: model-space and data-space D-ABIC scored equally

## What this fixes

This is a partial fix for a task that was removed from EdgeBench Verified. The original grader quietly penalises the model-space form of the method, although the task text lets the solver choose either form and both give the same result; the fixed version scores both forms equally. The fix does not repair the reason the task was removed: 42 points still come from results the submission reports about itself, so the task stays removed.

## The problem

Details are in the [native review](../../evidence/reviews/dabic_gravity_inversion-native.md). The task text and the starting README (line 48) leave the choice between a model-space and a data-space D-ABIC to the implementer. D-ABIC is a gravity inversion that picks its regularization with Akaike's Bayesian Information Criterion (ABIC). The model-space form works with matrices sized by the number of hidden model cells; the data-space form works with matrices sized by the number of data points.

The grader's E-behavior monitor (`BehaviorMonitor.report`) nevertheless sets `is_data_space` from the shapes of the square matrices passed to `eigh`/`slogdet`/`cho_factor`, and uses it twice:

- E1 awards 4 points (3.2 after the 0.8 scale) only to data-space shapes.
- `structural_failure = (not is_data_space) or …` blocks the 1.0 penalty branch in `structural_penalty_v34`, so any model-space submission is capped at a penalty factor of 0.5x.

An honest model-space submission that computes exactly the same ABIC curve as its data-space twin is therefore always 3.2 points lower in the total before the penalty factor is applied. At the strong level (C ≥ 26, D ≥ 20, F ≥ 10), it scores about 43 instead of about 89. No text the solver can see discloses this.

## What changes

One file changes: the grader `eval_dabic_v2.py`. It is copied to `/opt/evaluator/` (the path `eval_cmd` uses) and to `/opt/dabic_judge_files/` (a byte-identical copy in the original image), so no stale copy with the old penalty remains. The diff is `repair.patch`:

- It adds `is_model_space`, the mirror of `is_data_space`. A submission counts as model-space when most captured square matrices have a hidden *cell* count as their dimension, and more of them match that count than match the data count.
- It sets `uses_abic_form = is_data_space or is_model_space`.
- E1's 4 points and the `structural_failure` term use `uses_abic_form` instead of `is_data_space`.
- It adds `is_model_space` to the E-behavior breakdown, so the classification is visible.

Unchanged: `is_data_space` itself, every threshold, the 0.334/0.5/1.0 penalty levels, the `beta_truly_updated` and `uses_bad_det` rules, `valid_for_selection` and all other components. The task JSON changes only `judge.image_tag` (`task.json.in`). The work image and the files the solver sees are unchanged.

**Why the change is minimal.** Removing the check outright would also stop penalising a submission whose log-determinant is taken on neither ABIC matrix. Mirroring the existing data-space check keeps that requirement and only makes it neutral between the two forms, which is what the task text promises. Disclosing "data space required" instead would contradict the task text's explicit "decide for yourself" sentence. A data-space submission takes exactly the same code path as before (`uses_abic_form` is true whenever `is_data_space` is), so its score cannot change.

**Score compatibility.** Scores from the fixed grader equal scores from the original grader for every submission classified `is_data_space=true`, and for every submission whose square matrices match neither the hidden data count nor the hidden cell count. They are not comparable for model-space submissions. The fixed grader gives them the 3.2 E1 points and, when C ≥ 26, D ≥ 20, F ≥ 10 and the other checks pass, the uncapped penalty factor 1.0 instead of 0.5. The score scale is unchanged (the task has no `rescale` section).

## How it was checked

The full side-by-side run of the original and fixed graders is in [paired/results.md](paired/results.md). The fix is accepted. An honest model-space submission went from 25.77 on the original grader to 26.81 on the fixed one. The matching data-space submission went from 26.82 to 26.84, which is run noise. The invalid test submissions are marked `valid=false` by both graders.

## Build and use

Git does not contain any file copied from the EdgeBench images. It holds only our diff (`repair.patch`) and the recipe for rebuilding the full files. Regenerate them, then build:

```bash
./materialize.sh && docker build -t ebv/dabic_gravity_inversion-judge:v2 .
```

`materialize.sh` takes the following steps:

1. Pull the pinned image(s) by digest, unless already present.
2. Extract the original files with `docker create` and `docker cp`. No container runs in this step.
3. Check each original against `source-lock.json`.
4. Apply `repair.patch` with `patch -p1`.
5. Verify the sha256 of every file under `files/` (and `orig/`) against `source-lock.json` → `materialize.outputs`. Any mismatch fails loudly.

After that, the `Dockerfile` builds without changes. Regenerated files keep the file mode they have in the image.
See `../MATERIALIZE-CHECK.md` for how each package was verified.

## Limits

- The test submission that shows the problem and the correct test submission use one moderate honest implementation (C ≈ 17.4/35), with fixed audit input files for B, D and F. The removal of the cap at the strong level is shown by running each grader image's own penalty function on real breakdowns with C substituted, not by a strong submission.
- The form classification still depends on matrix shapes. A correct implementation that computes the log-determinant without passing an N×N or M×M square matrix to a monitored routine (for example a low-rank or iterative estimator) is still marked `structural_failure` in both versions.
- Other existing concerns from the review are not addressed. B and D (42 points) are self-reported. The submission runs inside the grader's own process. A's 1-point `"G @ "` source-text pattern is a check on the text of the code, not on its behaviour. This repair does not make the task retainable on its own.
- The invalid test submission is rejected only through the `valid` flag. Its numeric score is not low.
- Each test submission ran once. Repeated runs of the same submission vary by up to ~0.15 points in C.
