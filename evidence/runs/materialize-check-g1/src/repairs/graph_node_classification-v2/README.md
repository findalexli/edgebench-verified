# graph_node_classification, fixed version: every test node needs an integer class prediction

## What this fixes

The original grader silently drops predictions that are not whole numbers, scores only the rest, and still marks the run valid. A submission can therefore be scored on as few as one test node. The fixed grader requires a whole-number class for every test node and marks the run invalid otherwise.

### The problem in detail

In the original `verifier.evaluate`:

- `_to_int_labels` silently **drops** every prediction value that `int()` cannot convert, such
  as the string `"x"`, `None` or NaN. It then shortens `y_true` (the answer list) to the length of the shorter
  list.
- Predictions for IDs that are not test nodes are ignored, because `evaluate` only uses the
  IDs present in both lists.
- `judge_eval.py`'s coverage check compares only dictionary sizes.

So a submission can be scored on a subset of the test nodes, for example on one node, while
the run is still reported `valid: true`. This contradicts the contract ("`predictions` must
cover all test nodes", "Class IDs must be integers"). Review:
`evidence/reviews/graph_node_classification.md` (side observation).

## What changes

The exact change is `repair.patch`, generated with `diff -u`.

Only `verifier.py` changes. Its UTF-8 BOM (byte-order mark) is kept. In `evaluate`:

1. Every node ID in the answer key must be a key of `predictions`. Otherwise a `ValueError` is
   raised.
2. Each prediction is converted with the new `_strict_class_id`. It accepts int-like values
   (including numpy integers, via `operator.index`), whole-valued finite floats such as `3.0`, and
   decimal-integer strings such as `"3"`. It rejects bool, non-whole or non-finite floats,
   non-numeric strings, `None` and other types with a `ValueError`.
3. Answers and predictions are paired by node ID, with no filtering or shortening.

The `ValueError` passes through the unchanged `runner.py`, which exits non-zero. The
unchanged `judge_eval.py` then emits its existing failure result (`valid: false`, score 0).

Left unchanged on purpose:

- Confidence handling. Out-of-range values, and NaN, are still clipped into [0, 1] in `_ece`.
  The review shows this does not change scores: every such submission scores exactly as the
  matching in-range one.
- Out-of-class integers such as `7`. They still count as wrong predictions, as in the original version.
- Metric formulas, penalties, data, splits and the baseline.

`task.json.in` changes only `judge.image_tag` (`f2ddd52992ae` to `f2ddd52992ae-ebv-v2`). The
Dockerfile is `FROM` the pinned original grader digest plus one `COPY`. The agent's working image is
unchanged.

An earlier overlay (`$W/overlays/graph_node_classification/`) was not
reused. It targets a much broader tightening of the contract:

- strict JSON readers;
- ID canonicalization;
- rejection of out-of-range confidences;
- class-set checks.

This package fixes only the reviewed problem.

### Score compatibility

Some submissions give an integer class id (int, whole-valued float, or decimal-integer string) for every
test node. These score identically under the original and fixed versions (measured on 3 correct test submissions), except strings padded with the ASCII separators U+001C to U+001F, which the original drops and the fixed version scores. The fixed version newly rejects bools and
non-whole floats such as `3.5`, which the original version accepted. Fixed-version scores are not comparable with original scores when a submission:

- omits test nodes, or keys them by non-string IDs. The original count
  check already rejected this unless the count happened to match;
- gives a non-integer or non-whole value for any test node. The original grader silently dropped those
  nodes.

All of these are invalid in the fixed version.

## How it was checked

A side-by-side run of the original and fixed graders on the same test submissions. See `paired/results.md`. Correct test submissions keep the same quality metrics; the one-real-prediction submission, marked valid by the original grader, is rejected by the fixed grader.

## Limits

- Only the shipped baseline, a weak honest neighbour-vote solver and simple contract-breaking
  variants were run. Stronger solvers were not.
- The `final_score` time penalty (`0.01·log(time)`) depends on wall time and differs slightly
  between runs. The quality metrics are deterministic and are what the comparison uses.

## Build and use

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
