# Graph Node Classification (`graph_node_classification`)

**Decision:** Repair (v2). The original evaluator silently drops predictions that are not integers and still marks the run valid.

## What the task asks for

The solver predicts a class for every test node of a graph. The contract says: "`predictions` values must be integer class ids … should cover all test nodes of the current split", and "`confidences` is optional; if provided, values must be in `[0, 1]`." The score is `overall = 0.4·macro_f1 + 0.3·micro_f1 + 0.2·balanced_accuracy + 0.1·one_minus_ece`, minus time and memory penalties, averaged over 10 splits. Category: Scientific Problems & ML.

## What goes wrong

**Incomplete predictions are accepted as valid.**

- `_to_int_labels` silently drops prediction values that `int()` cannot convert, such as `"x"`, `None` or NaN.
- `evaluate()` then truncates the ground-truth list to the length of the shorter list.
- The coverage check in `judge_eval.py` compares only dictionary sizes, so it still passes.

So a run can be scored on a subset of the test nodes, down to a single node, while it is reported `valid: true`.

- **Small example:** 1000 nodes, where the first prediction is correct and the rest are `"x"`. Result: macro_f1 = micro_f1 = balanced accuracy = 1.0 and ECE 0.
- **Real judge example:** the shipped baseline with all but one prediction replaced by `"x"`.
  - Expected: rejected, because the predictions are not integer class ids.
  - Observed: `valid: true`, with every split scored on one node. The first-node guess was right in 2 of 10 splits, giving overall 0.20, below the honest 0.333 for this weak baseline.

Why it matters: a submission that breaks the contract gets a valid score computed on the wrong set of nodes.

**Checked and found harmless: NaN or out-of-range confidences.** `_ece()` clips each confidence with `min(1.0, max(0.0, c))`. NaN or a negative value becomes 0, and a value above 1 becomes 1. The score then depends only on the clipped, legal value, so no out-of-range value can score better than a legal one. This is left unchanged.

## Impact

The effect is added variance, with no expected gain shown. The per-split expected value of the one-node gamble depends on accuracy on one fixed node. Whether it inflates scores, for example under best-of-several selection, was not established. Only submissions that send non-integer or missing predictions are affected.

## Fix (v2)

v2 changes only `verifier.py`, in `evaluate`:

1. Every ground-truth node ID must have a prediction.
2. Each prediction is converted strictly. Integers, integral finite floats such as `3.0` and decimal-integer strings such as `"3"` are accepted. Bools, non-integral or non-finite floats, non-numeric strings, `None` and other types are rejected.
3. Ground truth and predictions are paired by node ID, with no filtering or truncation.

A violation raises an error, which the unchanged runner and `judge_eval.py` turn into their existing failure result (`valid: false`). Confidence clipping, out-of-class integers (still counted as wrong), metrics, penalties, data, splits and baseline are unchanged. The task JSON changes only `judge.image_tag`.

| Submission | Role | Image | Harness valid | final score | Normalized 0–100 | overall (quality) | macro_f1 | one_minus_ece |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| baseline (shipped solution.py) | valid control | v1 | true | 0.292783 | 29.278 | 0.332624 | 0.238512 | 0.925034 |
| baseline | valid control | v2 | true | 0.292702 | 29.270 | 0.332624 | 0.238512 | 0.925034 |
| neighbor (honest neighbour-vote solver, int ids) | valid control | v1 | true | 0.241002 | 24.100 | 0.281108 | 0.221556 | 0.758336 |
| neighbor | valid control | v2 | true | 0.241044 | 24.104 | 0.281108 | 0.221556 | 0.758336 |
| nanconf (baseline predictions, NaN confidences) | clipping left unchanged | v1 | true | 0.271465 | 27.147 | 0.311437 | 0.238512 | 0.713160 |
| nanconf | clipping left unchanged | v2 | true | 0.271431 | 27.143 | 0.311437 | 0.238512 | 0.713160 |
| shrink (one real prediction, rest `"x"`) | **trigger** | v1 | **true** | 0.160264 | 16.026 | 0.200000 (each split scored on 1 node) | 0.2 | 0.2 |
| shrink | **trigger** | v2 | **false** | – | – | runner error: `prediction for node '9' is not an integer class id: 'x'` | | |
| missing_half (half the test nodes) | invalid control | v1 | false | – | – | coverage check: `predictions=520 expected=1041` | | |
| missing_half | invalid control | v2 | false | – | – | runner error: `predictions missing for 521 test node(s)` | | |

For every valid submission, the quality metrics are identical between v1 and v2 to all printed digits. Final scores differ by at most 8e-5, about 0.008 normalized points. That difference comes only from the wall-time penalty `0.01·log(time)`.

**Score compatibility:** submissions that give an integer class id (an int, an integral finite float or a decimal-integer string, not a bool) for every test node score identically in v1 and v2, apart from run-to-run timing noise. Bools and non-integral floats, which v1 converted with `int()`, are invalid in v2. Submissions that omit test nodes, or give non-integer values for any test node, are invalid in v2 and are not comparable with their v1 scores.

## How we know

- **Original evaluator in the pinned image.** The real judge command (`python judge_eval.py`) ran in the judge image (`sha256:518c105e…`) under `--network none`, with the shipped baseline and variants of it (NaN, 0.0, 7.5 and 1.0 confidences, and the "shrink" case).
- **Independent check of the scoring function.** `verifier.py` was tested as a pure function with point probes, 20,000 random confidence vectors with 40% special values, and an exhaustive search of all binary cases with n ≤ 3 (84 label/prediction pairs) over a 21-point legal grid plus 5 illegal values. The random vectors gave 0 mismatches against their clipped images, and the exhaustive search found 0 cases where an illegal value beat the best legal one. In the real judge, all-NaN matched all-0.0 (overall 0.31144) and all-7.5 matched all-1.0 (overall 0.26880), and both scored below the baseline's own legal confidences (0.33262).
- **Paired evaluation.** The full 10-split run through the TaskSpec `eval.sh` (`--network none`, 4 CPUs, 6 GB) gave the table above. It was repeated three times with no verdict change ([`paired-repeatability.md`](../paired-repeatability.md)).

## Limits

- No model or solver runs. Effects are shown only on authored controls and counterexamples.
- Only the shipped baseline, a weak honest neighbour-vote solver and simple contract-breaking variants were run. Stronger solvers were not.
- The expected-value analysis of the shrink case is analytic, backed by one 10-split run. The interaction of `selection: valid_then_score` with the added variance was not checked.
- No submission with non-string node-ID keys was run. Such a submission becomes invalid in v2.
- The prompt text was read from the judge image's English copy and the Chinese source copy, which agree on the contract sentences. The work image was not pulled.

## Reproduce

- Scoring-function checks: `evidence/scripts/graph_node_classification/check_confidence_mapping.py`, `check_invalid_prediction_shrink.py`, and `run_judge_variants.sh` (with `wrapper_solution.py`).
- Paired evaluation: `repairs/graph_node_classification-v2/paired/run.sh` (results in `paired/results.md`).
- Patch: `repairs/graph_node_classification-v2/repair.patch`.
- Supporting records: `repairs/graph_node_classification-v2/` (source-lock.json, paired captures).
