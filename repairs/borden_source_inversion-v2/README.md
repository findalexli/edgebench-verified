# borden_source_inversion, fixed version: disclose the grader's forward model and add a score scale

Review: [`../../evidence/reviews/borden_source_inversion.md`](../../evidence/reviews/borden_source_inversion.md).

## What this fixes

The grader predicts well readings with a hidden forward model whose conventions are unstated and not textbook physics. A one-shot honest fit to the public data that follows the documentation therefore scores at the baseline level (7.03), while the same fit with the grader's convention scores 31.2. An agent that submits repeatedly sees the grader's error on the hidden wells after each submission: a third-party Claude Opus 5.5 run on the original grader climbed from 7.01 to 60.10 raw over 36 submissions (see the case page); how it used that feedback was not verified. The fixed version gives solvers the grader's own forward-model code and an exact description of its conventions, and adds a score scale from 0 to 109.

### The problem in detail

The grader scores `answer.json` by running a hidden forward model (a model that predicts well readings from a proposed source). `public_problem_config.json` gives the ingredients (q, a factor of 1000, a 5×5×1 sub-point grid, 9 release steps) but not how the model combines them. The convention is not textbook physics:
- each of 225 pulses has amplitude `C0·q·1000/225`;
- porosity is not used;
- total mass does not depend on `duration`;
- mg/m³ is reported as mg/L;
- with `nz=1` the source plane sits at `z_center − half_length_z`.

An honest solver builds a textbook ADE (advection–dispersion equation) model from the documentation. It fits the public data as well as the grader's own model does (RMS 0.0079 for both). It still scores 7.03, the baseline level. The same least-squares fit run with the grader's convention scores 31.2. The public data cannot tell the two conventions apart, so the solver cannot recover the convention from the data.

Separately, the task had no score scale (`rescale`):
- `score_0_100` was `None`;
- the raw result (before conversion to 0–100) ran 0–109.

## What changes

The answer key, the grader and the grader image are unchanged.

1. **Agent working image** (`Dockerfile`, `FROM` the pinned working-image digest, `COPY` only):
   - **adds `forward_model.py`**: the grader's forward model, function bodies byte-identical, with
     only the 2-line header comment replaced. That comment mentioned `scoring/`, a keyword the
     grader flags in submissions.
   - **adds a README section** stating the convention exactly: sub-points and the
     `z_center − half_length_z` plane, release offsets, pulse amplitude, no porosity, no
     dependence on duration, units as reported.
   - The same section is inserted into `task.json.in` → `work.agent_query`.
   - *Revision (2026-10-12).* The first published fixed prompt kept the scoring step "Use a hidden
     Borden-ADE region-source forward model" and the rule "Do not read or reference hidden scoring files"
     without saying that `forward_model.py` may be used. Three lines now say it, in both the README and
     `work.agent_query`: the file list ("You may read, run and import it freely."), scoring step 3 ("the
     Borden-ADE region-source forward model shipped as `forward_model.py`") and the rule ("`forward_model.py`
     is not one of them: it is an exact copy of the judge's model and may be used freely."). Scores are
     unchanged (`paired/results.md`, revision section).
2. **`task.json.in`** adds `judge.rescale = {"kind": "linear", "lower": 0, "upper": 109}`.
   109 is the grader's theoretical maximum (1+1+2+1+2 easy points, 92 metric, 10 region),
   and the true source reaches it. The map is strictly increasing, so it preserves ordering,
   including above 100. A cap at 100 would have tied every score in 100–109. `work.image_tag`
   becomes `f389fcf94240-ebv-v2.1`; `judge.image_tag` stays `cc54d4fd7006`. Tag `f389fcf94240-ebv-v2`
   (v1.0 package) is superseded; rebuild.

**Why ship the function rather than only document it.** Prose can be misread, and the
`linspace(num=1)` plane quirk alone costs about 18 points (12.9 against 31.2 in the review). A
byte-identical function removes any ambiguity. The side-by-side run shows it reproduces the
grader's output with diff 0.0. The README text is kept as well, for solvers that write their own
model. The function holds no secret: no answer key, no true source, no hidden wells. The grader
never imports the solver's copy.

**Why minimal.** There is no change to the answer key, the grader, the grader image or the scoring
rule. Fixing the z-plane quirk or making the model physical would require regenerating the answer
key, so it is out of scope for this version.

### Score compatibility

For any given `answer.json`, raw results are identical under the original and fixed versions, because the grader is unchanged. The fixed version
reports `score_0_100 = raw·100/109`, which the original version did not define. Agent runs on the fixed version are **not comparable**
with agent runs on the original version: fixed-version solvers are told the convention, so the same agent can
score higher (one-shot honest fit 7.0 → about 31 raw). Fixed-version scores are out of 100; original raw
results are on 0–109.

## How it was checked

A side-by-side run of the original and fixed graders on the same test submissions: **accepted**. See `paired/results.md`.

The prompt revision was checked by rebuilding the fixed work image and grading the same seven submissions in the original, first fixed and revised working directories: every `score.json` is byte-identical (`evidence/runs/borden_source_inversion-v2-paired-r3`).

## Limits

- The inverse problem is still weakly determined by the data. The best public-data fit with the exact model
  reaches 31.2 raw (28.6 out of 100). The fix removes the penalty for the hidden convention, not the
  difficulty.
- `C0` remains an "effective intensity" in a non-physical convention. The fixed version documents this rather
  than fixing it.
- One fitting method was used (multi-start least squares, log/hinge loss), with one textbook model variant.
- The original grader does not reject the out-of-bounds test submission outright: it gets 4 raw and is
  capped at 15. That is unchanged and reported as observed.
- `orig/` holds copies of the original README, task JSON and grader forward model, used to
  generate `repair.patch`. They come from the public images.

## Build and use

Git does not contain any file copied from the EdgeBench images. It holds only our diff (`repair.patch`) and the recipe for rebuilding the full files. Regenerate them, then build:

```bash
./materialize.sh && docker build -t edgebench.work.borden_source_inversion:f389fcf94240-ebv-v2.1 .
```

`materialize.sh` takes the following steps:

1. Pull the pinned image(s) by digest, unless already present.
2. Extract the original files with `docker create` and `docker cp`. No container runs in this step.
3. Check each original against `source-lock.json`.
4. Apply `repair.patch` with `patch -p1`.
5. Verify the sha256 of every file under `files/` (and `orig/`) against `source-lock.json` → `materialize.outputs`. Any mismatch fails loudly.

After that, the `Dockerfile` builds without changes. Regenerated files keep the file mode they have in the image.
See `../MATERIALIZE-CHECK.md` for how each package was verified.

This Dockerfile builds the fixed **working** image (the image the agent works in). `files/forward_model.py` is produced from the grader image's `/opt/borden_scoring/hidden_forward_model.py` plus the header change in `repair.patch`. `orig/` is regenerated too: `orig/borden_source_inversion.json` comes from the EdgeBench repo's `tasks/` (set `EDGEBENCH_ROOT` if the package is not inside the EdgeBench checkout). The task JSON change is in `task-json.diff`.
