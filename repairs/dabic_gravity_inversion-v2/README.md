# dabic_gravity_inversion v2: model-space and data-space D-ABIC scored equally

**Defect** ([native review](../../evidence/reviews/dabic_gravity_inversion-native.md)). The prompt and the
starter README (line 48) leave the choice between a model-space and a data-space D-ABIC to the
implementer. The evaluator's E-behavior monitor (`BehaviorMonitor.report`) nevertheless sets
`is_data_space` from the shapes of the square matrices passed to `eigh`/`slogdet`/`cho_factor`,
and uses it twice: E1 awards 4 points (3.2 after the 0.8 scale) only to data-space shapes, and
`structural_failure = (not is_data_space) or …` blocks the 1.0 penalty branch in
`structural_penalty_v34`, capping any model-space submission at 0.5x. An honest model-space
directive that computes exactly the same ABIC curve as its data-space twin is therefore always
3.2 raw points lower and, at the strong tier (C ≥ 26, D ≥ 20, F ≥ 10), about 43 instead of
about 89. No solver-visible text discloses this.

**Change.** One file, the evaluator `eval_dabic_v2.py`, copied to `/opt/evaluator/` (the path
`eval_cmd` uses) and to `/opt/dabic_judge_files/` (a byte-identical copy in the original image),
so no stale gated copy remains (`repair.patch`):
- add `is_model_space`, the mirror of `is_data_space` (most captured square matrices have a
  hidden *cell* count as dimension, and more than match the data count);
- `uses_abic_form = is_data_space or is_model_space`;
- E1's 4 points and the `structural_failure` term use `uses_abic_form` instead of `is_data_space`;
- `is_model_space` is added to the E-behavior breakdown for transparency.

`is_data_space` itself, every threshold, the 0.334/0.5/1.0 tiers, the `beta_truly_updated` and
`uses_bad_det` rules, `valid_for_selection` and all other components are unchanged. The task
JSON changes only `judge.image_tag` (`task.json.in`). The work image and solver-visible files are
unchanged.

**Why minimal.** Removing the gate outright would also stop penalising a submission whose
log-determinant is taken on neither ABIC matrix; mirroring the existing data-space check keeps
that requirement and only makes it form-neutral, which is what the prompt promises. Disclosing
"data space required" instead would contradict the prompt's explicit "decide for yourself"
sentence. A data-space submission takes exactly the same code path as before (`uses_abic_form`
is true whenever `is_data_space` is), so its score cannot change.

**Score compatibility.** v2 scores equal v1 scores for every submission classified
`is_data_space=true` and for every submission whose square matrices match neither the hidden data
nor the hidden cell counts. They are not comparable with v1 for model-space submissions: v2 gives
them the 3.2 E1 points and, when C ≥ 26, D ≥ 20, F ≥ 10 and the other checks pass, the uncapped
1.0 penalty instead of 0.5. Rescale is unchanged (the task has no `rescale` section).

**Paired evaluation:** [paired/results.md](paired/results.md). The repair is accepted: model form
25.77 → 26.81, data form 26.82 → 26.84 (run noise), invalid controls `valid=false` in both.

**Limits.**
- The trigger and valid control use one moderate honest implementation (C ≈ 17.4/35) with audit
  fixtures for B, D and F. The strong-tier cap removal is shown by running each image's own
  penalty function on native breakdowns with C substituted, not by a strong submission.
- Classification still depends on matrix shapes: a correct implementation that computes the
  log-determinant without passing an N×N or M×M square matrix to a monitored routine (e.g. a
  low-rank or iterative estimator) is still marked `structural_failure` in both versions.
- Other pre-existing concerns from the review are not addressed: B and D (42 points) are
  self-reported, the submission runs in-process, and A's 1-point `"G @ "` source-text pattern is
  a textual heuristic. This repair does not make the task retainable on its own.
- The invalid control is rejected only through the `valid` flag; its numeric score is not low.
- One run per arm; repeated runs of the same submission vary by up to ~0.15 points in C.

## Build

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
