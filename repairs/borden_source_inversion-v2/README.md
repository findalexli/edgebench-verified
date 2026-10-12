# borden_source_inversion v2: disclose the judge's forward model; add a rescale

Review: [`../../evidence/reviews/borden_source_inversion.md`](../../evidence/reviews/borden_source_inversion.md).

## Defect

The judge scores `answer.json` by running a hidden forward model whose parameter convention is
not disclosed and is not textbook physics:
- each of 225 pulses has amplitude `C0·q·1000/225`;
- porosity is not used;
- total mass does not depend on `duration`;
- mg/m³ is reported as mg/L;
- with `nz=1` the source plane sits at `z_center − half_length_z`.

An honest solver that builds a textbook ADE model from the docs fits the public data as well as
the judge's own model does (RMS 0.0079 for both). It still scores 7.03, the baseline level. The
same least squares run with the judge's convention scores 31.2. The public data cannot tell the
two conventions apart, so the solver cannot recover the convention from the data.

Separately, the task had no `rescale`:
- `score_0_100` was `None`;
- the raw scale ran 0–109.

## Change (labels, evaluator and judge image unchanged)

1. **Work image** (`Dockerfile`, `FROM` the pinned work digest, `COPY` only):
   - **adds `forward_model.py`**: the judge's forward model, function bodies byte-identical, with
     only the 2-line header comment replaced. That comment mentioned `scoring/`, a keyword the
     evaluator flags in submissions.
   - **adds a README section** stating the convention exactly: sub-points and the
     `z_center − half_length_z` plane, release offsets, pulse amplitude, no porosity, no duration
     dependence, units as reported.
   - The same section is inserted into `task.json.in` → `work.agent_query`.
2. **`task.json.in`** adds `judge.rescale = {"kind": "linear", "lower": 0, "upper": 109}`.
   109 is the evaluator's theoretical maximum (1+1+2+1+2 easy points, 92 metric, 10 region),
   and the true source reaches it. The map is strictly increasing, so it preserves ordering,
   including above 100. A clamp at 100 would have tied every score in 100–109. `work.image_tag`
   becomes `f389fcf94240-ebv-v2`; `judge.image_tag` stays `cc54d4fd7006`.

**Why ship the function rather than only document it.** Prose can be misread, and the
`linspace(num=1)` plane quirk alone costs about 18 points (12.9 versus 31.2 in the review). A
byte-identical function removes any ambiguity, and the paired run shows it reproduces the
judge's output with diff 0.0. The README text is kept as well, for solvers that write their own
model. The function holds no secret: no labels, no truth, no hidden wells. The judge never
imports the solver's copy.

**Why minimal.** No label, evaluator, judge-image or scoring-rule change. Fixing the z-plane
quirk or making the model physical would require regenerating the labels, so it is out of scope
for this version.

## Score compatibility

Raw scores are identical v1 → v2 for any given `answer.json`, because the judge is unchanged. v2
reports `score_0_100 = raw·100/109`, which v1 did not define. v2 scores are **not comparable**
with v1 *solver runs*: v2 solvers are told the convention, so a v2 run of the same agent can
score higher (honest fit 7.0 → about 31 raw). Normalised v2 scores are on a 0–100 scale; v1 raw
scores are on 0–109.

## Status

Paired evaluation: **accepted**. See `paired/results.md`.

## Limits

- The inverse problem stays weakly identified. The best public-data fit with the exact model
  reaches 31.2 raw (28.6 normalised). The repair removes the hidden-convention penalty, not the
  difficulty.
- `C0` remains an "effective intensity" in an unphysical convention. v2 documents this rather
  than fixing it.
- One fitting method was used (multi-start least squares, log/hinge loss).
- The out-of-bounds control is not hard-rejected by the original evaluator: it gets 4 raw and is
  capped at 15. That is unchanged and reported as observed.
- `orig/` holds copies of the original README, task JSON and judge forward model, used to
  generate `repair.patch`. They come from the public images.

## Build

Git does not contain any file copied from the EdgeBench images. It holds only our diff (`repair.patch`) and the recipe for rebuilding the full files. Regenerate them, then build:

```bash
./materialize.sh && docker build -t ebv/borden_source_inversion-work:v2 .
```

`materialize.sh` takes the following steps:

1. Pull the pinned image(s) by digest, unless already present.
2. Extract the original files with `docker create` and `docker cp`. No container runs in this step.
3. Check each original against `source-lock.json`.
4. Apply `repair.patch` with `patch -p1`.
5. Verify the sha256 of every file under `files/` (and `orig/`) against `source-lock.json` → `materialize.outputs`. Any mismatch fails loudly.

After that, the `Dockerfile` builds without changes. Regenerated files keep the file mode they have in the image.
See `../MATERIALIZE-CHECK.md` for how each package was verified.

This Dockerfile builds the v2 **work** image. `files/forward_model.py` is produced from the judge image's `/opt/borden_scoring/hidden_forward_model.py` plus the header change in `repair.patch`. `orig/` is regenerated too: `orig/borden_source_inversion.json` comes from the EdgeBench repo's `tasks/` (set `EDGEBENCH_ROOT` if the package is not inside the EdgeBench checkout). The task JSON change is in `task-json.diff`.
