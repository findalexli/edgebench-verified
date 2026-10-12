# graph_node_classification v2: every test node needs an integer class prediction

## Defect

In the original `verifier.evaluate`:

- `_to_int_labels` silently **drops** every prediction value that `int()` cannot convert, such
  as the string `"x"`, `None` or NaN. It then truncates `y_true` to the length of the shorter
  list.
- Predictions for IDs that are not test nodes are ignored, because `evaluate` only uses the
  intersection of IDs.
- `judge_eval.py`'s coverage check compares only dictionary sizes.

So a submission can be scored on a subset of the test nodes, for example on one node, while
the run is still reported `valid: true`. This contradicts the contract ("`predictions` must
cover all test nodes", "Class IDs must be integers"). Review:
`evidence/reviews/graph_node_classification.md` (side observation).

## Exact change (`repair.patch`, generated with `diff -u`)

Only `verifier.py` changes. Its UTF-8 BOM is kept. In `evaluate`:

1. Every ground-truth node ID must be a key of `predictions`. Otherwise a `ValueError` is
   raised.
2. Each prediction is converted with the new `_strict_class_id`. It accepts int-like values
   (including numpy integers, via `operator.index`), integral finite floats such as `3.0`, and
   decimal-integer strings such as `"3"`. It rejects bool, non-integral or non-finite floats,
   non-numeric strings, `None` and other types with a `ValueError`.
3. Ground truth and predictions are paired by node ID, with no filtering or truncation.

The `ValueError` propagates through the unchanged `runner.py`, which exits non-zero. The
unchanged `judge_eval.py` then emits its existing failure result (`valid: false`, score 0).

Left unchanged on purpose:

- Confidence handling. Out-of-range values, and NaN, are still clipped into [0, 1] in `_ece`.
  The review shows this is score-neutral: every such submission scores exactly as the
  corresponding in-range one.
- Out-of-class integers such as `7`. They still count as wrong predictions, as in v1.
- Metric formulas, penalties, data, splits and the baseline.

`task.json.in` changes only `judge.image_tag` (`f2ddd52992ae` to `f2ddd52992ae-ebv-v2`). The
Dockerfile is `FROM` the pinned original judge digest plus one `COPY`. The work image is
unchanged.

The earlier overlay (`$W/overlays/graph_node_classification/`) was not
reused. It targets a much broader contract tightening:

- strict JSON readers;
- ID canonicalization;
- rejection of out-of-range confidences;
- class-set checks.

This package fixes only the reviewed defect.

## Score compatibility

Submissions that give an integer-convertible prediction for every test node score identically
in v1 and v2. v2 scores are not comparable with v1 when a submission:

- omits test nodes, or keys them by non-string IDs. This was already rejected by v1's count
  check unless the count happened to match;
- gives a non-integer or non-integral value for any test node. v1 silently dropped those
  nodes.

All of these are invalid in v2.

## Paired evaluation

See `paired/results.md`.

## Limits

- Only the shipped baseline, a weak honest neighbour-vote solver and simple contract-violating
  variants were run. Stronger solvers were not.
- The `final_score` time penalty (`0.01·log(time)`) depends on wall time and differs slightly
  between runs. The quality metrics are deterministic and are the comparison target.

## Build

Git does not contain any file copied from the EdgeBench images. It holds only our diff (`repair.patch`) and the recipe for rebuilding the full files. Regenerate them, then build:

```bash
./materialize.sh && docker build -t ebv/graph_node_classification-judge:v2 .
```

`materialize.sh` takes the following steps:

1. Pull the pinned image(s) by digest, unless already present.
2. Extract the original files with `docker create` and `docker cp`. No container runs in this step.
3. Check each original against `source-lock.json`.
4. Apply `repair.patch` with `patch -p1`.
5. Verify the sha256 of every file under `files/` (and `orig/`) against `source-lock.json` → `materialize.outputs`. Any mismatch fails loudly.

After that, the `Dockerfile` builds without changes. Regenerated files keep the file mode they have in the image.
See `../MATERIALIZE-CHECK.md` for how each package was verified.

The task JSON change is in `task-json.diff`.
