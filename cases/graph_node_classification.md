# Graph Node Classification (`graph_node_classification`)

**Outcome:** Fixed. <mark>The original grader silently drops predictions that are not whole numbers and still marks the run valid.</mark>

![Original grader drops every non-integer prediction, scores the one prediction left against the first label in each of 10 rounds and calls the run valid; the fixed version rejects it.](figures/graph_node_classification.svg)

*The original grader silently dropped the non-integer predictions, scored the one left against the first label in each round and still called the run valid; the fixed version rejects it.*

## What the task asks

The agent predicts a class for every test node (a point in the network) of a graph. The contract says: "`predictions` values must be integer class ids … should cover all test nodes of the current split", and "`confidences` is optional; if provided, values must be in `[0, 1]`." On keys it says, "The keys of `predictions` must be test node IDs, which can be strings or values convertible to strings." The task gives the solver the test node IDs as a list of integers.

The score is `overall = 0.4·macro_f1 + 0.3·micro_f1 + 0.2·balanced_accuracy + 0.1·one_minus_ece`, minus time and memory penalties, averaged over 10 splits. F1 and balanced accuracy are accuracy measures. ECE (expected calibration error) measures how well the confidences match actual accuracy. The task is in the Scientific Problems & ML category.

## What goes wrong

Three steps let the grader accept incomplete predictions as valid.

- `_to_int_labels` silently drops prediction values that `int()` cannot convert, such as `"x"`, `None` or NaN.
- `evaluate()` then shortens the answer list to the length of the shorter list.
- The coverage check in `judge_eval.py` compares only dictionary sizes, so it still passes.

A run can therefore be scored on as little as a single node while the grader reports it `valid: true`. More precisely, the grader pairs the surviving predictions with the first labels in order, so one bad value early in the file shifts every later prediction onto the wrong node.

- In a small example with 1000 nodes, where the first prediction is correct and the rest are `"x"`, the result is macro_f1 = micro_f1 = balanced accuracy = 1.0 and ECE 0.
- On the real grader we replaced all but one prediction of the shipped baseline with `"x"`.
  - The grader should reject this, because the predictions are not integer class ids.
  - It reported `valid: true` and scored every split on one node. The first-node guess was right in 2 of 10 splits, giving overall 0.20, below the 0.333 this weak baseline scores with full predictions.

A submission that breaks the contract thus gets a valid score computed on the wrong set of nodes.

Complete predictions keyed by integer node IDs score 0 and are still valid. The grader looks predictions up under the answer key's string node IDs (`"5"`) and does not convert the submitted keys, so a prediction keyed by the integer `5` is never found. The coverage check still passes, because the number of keys is right. On the real grader, a plain neighbour-vote solver that keys its predictions by the integer IDs it is given (`neighbor_intkeys`) was marked `valid: true` with every quality metric 0 (overall 0.000000, normalized score 0), while the same predictions keyed by strings score overall 0.281108. Here the error pushes down the score of good-faith work that follows the prompt.

We checked NaN and out-of-range confidences and found them harmless. `_ece()` clips each confidence with `min(1.0, max(0.0, c))`. NaN or a negative value becomes 0, and a value above 1 becomes 1. The score then depends only on the clipped, legal value, so no out-of-range value can score better than a legal one. We left this unchanged.

## How much it matters

The effect adds chance to the score. For each split, the expected value of the one-node gamble depends on accuracy on one fixed node. The one measured gamble (shrink) scored overall 0.20, below the 0.333 of full predictions (`repairs/graph_node_classification-v2/paired/graded.md`). The task keeps a run's best valid submission (`selection: valid_then_score`). A general Lean lemma shows that under such max selection an added random submission never lowers the expected kept score, and raises it whenever it can beat the current best (`evidence/formal/notes/graph_node_classification.md`). We have shown no gain for a real solver. This part affects only submissions that send non-integer or missing predictions. Separately, a submission keyed by integer node IDs loses its whole score (to 0) while still counted valid. In the 112 real-solver gradings we have (see "How we checked it"), no submission was keyed that way.

## The fix

The fixed version changes only `verifier.py`, in `evaluate`:

0. It first converts the keys of the predictions and of the confidences with `str()`, so integer node IDs match as the prompt allows. It rejects two keys that give the same string, such as `5` and `"5"`, because it is not clear which prediction is meant.
1. Every node ID in the answer key must have a prediction.
2. It converts each prediction strictly. It accepts integers, whole-valued finite floats such as `3.0` and decimal-integer strings such as `"3"`, and rejects bools, non-whole or non-finite floats, non-numeric strings, `None` and other types.
3. It pairs answers and predictions by node ID, with no filtering or shortening.

A violation raises an error, and the unchanged runner and `judge_eval.py` turn it into their existing failure result (`valid: false`). Confidence clipping, out-of-class integers (still counted as wrong), metrics, penalties, data, splits and baseline stay as they were. The task JSON changes only `judge.image_tag`.

| Submission | Role | Grader | Marked valid | Final score | Score out of 100 | overall (quality) | macro_f1 | one_minus_ece |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| baseline (shipped solution.py) | correct test submission | Original | true | 0.292783 | 29.278 | 0.332624 | 0.238512 | 0.925034 |
| baseline | correct test submission | Fixed | true | 0.292702 | 29.270 | 0.332624 | 0.238512 | 0.925034 |
| neighbor (plain neighbour-vote solver, int ids) | correct test submission | Original | true | 0.241002 | 24.100 | 0.281108 | 0.221556 | 0.758336 |
| neighbor | correct test submission | Fixed | true | 0.241044 | 24.104 | 0.281108 | 0.221556 | 0.758336 |
| nanconf (baseline predictions, NaN confidences) | clipping left unchanged | Original | true | 0.271465 | 27.147 | 0.311437 | 0.238512 | 0.713160 |
| nanconf | clipping left unchanged | Fixed | true | 0.271431 | 27.143 | 0.311437 | 0.238512 | 0.713160 |
| shrink (one real prediction, rest `"x"`) | **shows the problem** | Original | **true** | 0.160264 | 16.026 | 0.200000 (each split scored on 1 node) | 0.2 | 0.2 |
| shrink | **shows the problem** | Fixed | **false** | – | – | runner error: `prediction for node '9' is not an integer class id: 'x'` | | |
| missing_half (half the test nodes) | invalid test submission | Original | false | – | – | coverage check: `predictions=520 expected=1041` | | |
| missing_half | invalid test submission | Fixed | false | – | – | runner error: `predictions missing for 521 test node(s)` | | |

"–" marks a result the grader reports as `valid: false`. EdgeBench's harness still records its score (`graded.md` shows it), and the task's `valid_then_score` selection leaves it out.

We revised the fix on 2026-10-13 (v2.1). The first fixed version did not convert keys, so it rejected a complete integer-keyed submission as "predictions missing". The fixed version now converts them (step 0). A side-by-side run of the original grader, the first fixed version and v2.1 on seven submissions, repeated three times, gave the same verdicts and quality metrics for the five submissions above under the first fixed version and v2.1. The two new submissions scored as follows:

| Submission | Role | Original | First fixed version | Revised fixed version (v2.1) |
| --- | --- | --- | --- | --- |
| neighbor_intkeys (neighbor, keyed by integer node IDs) | correct test submission | valid, overall 0.000000 (score 0) | invalid: `predictions missing for 1041 test node(s)` | valid, overall 0.281108, the same as neighbor |
| dupkeys_after_str (neighbor_intkeys, last node dropped, first node repeated as a string key) | invalid test submission | valid, overall 0.239264 | invalid: `predictions missing for 1040 test node(s)` | invalid: `duplicate node id after str()` |

For every valid submission keyed by string node IDs, the quality metrics are identical between the original and fixed graders to all printed digits. Final scores differ by at most 8.1e-5 in the first-fix run (baseline 0.292783 against 0.292702), about 0.008 points out of 100, and by at most 2.9e-4 in the v2.1 runs (baseline, run 3: 0.291900 against 0.292185), under 0.03 points. That difference comes only from the wall-time penalty `0.01·log(time)`.

Some submissions give an integer class id for every test node, as an int, a whole-valued finite float or a decimal-integer string, but not a bool. These score identically under the original and fixed versions, apart from run-to-run timing noise. The one exception is a string padded with the ASCII separators U+001C to U+001F, such as `"\x1c0"`, which the original grader drops and the fixed version scores (`separator_boundary` in the formal note). Bools and non-whole floats, which the original grader converted with `int()`, are invalid in the fixed version. Submissions that omit test nodes, give non-integer values for any test node, or give two keys with the same `str()`, are invalid in the fixed version and are not comparable with their original scores. A complete submission keyed by integer node IDs is valid in both versions but not comparable either. The original scores it 0, and the fixed version scores it exactly like the same predictions keyed by strings.

## How we checked it

- We ran the real grading command (`python judge_eval.py`) of the original grader in the original public image, pinned by digest, under `--network none`, with the shipped baseline and variants of it (NaN, 0.0, 7.5 and 1.0 confidences, and the "shrink" case).
- For an independent check of the scoring function, we tested `verifier.py` as a pure function in three ways: point probes, 20,000 random confidence vectors with 40% special values, and an exhaustive search of all binary cases with n ≤ 3 (84 label/prediction pairs) over a 21-point legal grid plus 5 illegal values. The random vectors gave 0 mismatches against their clipped versions. The exhaustive search found 0 cases where an illegal value beat the best legal one. In the real grader, all-NaN matched all-0.0 (overall 0.31144) and all-7.5 matched all-1.0 (overall 0.26880). Both scored below the baseline's own legal confidences (0.33262).
- We ran the original and fixed graders side by side. The full 10-split run through the TaskSpec `eval.sh` (`--network none`, 4 CPUs, 6 GB) gave the table above. We repeated it three times with no verdict change ([`data/paired-repeatability.md`](../data/paired-repeatability.md)). We also ran the side-by-side run with the revised fixed version (v2.1) three times on fresh workers (`evidence/runs/graph_node_classification-v2-paired-v21a`, `-v21b` and their `-rep2`, `-rep3`); in each, the package's own `materialize.sh` regenerated the v2.1 verifier from the pinned image before it was built.
- We regraded the 112 gradings of 106 distinct submissions from a third-party Claude Opus 5.5 run (`evidence/runs/opus55-regrade2-graph-a`, `-b`, `-c`) with the original and the first fixed verifier. None changed validity and none was invalid under the original. The lowest original score was 0.208, so no submission was integer-keyed. In two of them the overall quality differs slightly (agent-49: 0.876092 against 0.875200; agent-6: 0.718849 against 0.715770); the fixed version accepted the same predictions, so this is most likely run-to-run variation of the solver, but we did not show that. We did not repeat these gradings with v2.1.

## Limits

- The effects shown come from test submissions and counterexamples we wrote. We regraded real solver submissions only with the original and the first fixed verifier (see above), and none of them shows the problem.
- We ran only the shipped baseline, a weak, plain neighbour-vote solver and simple contract-breaking variants, and no stronger solver.
- We worked out the expected-value analysis of the shrink case by hand, backed by one 10-split run. Only a general lemma covers how the added chance interacts with the rule that picks a run's best submission (`selection: valid_then_score`); its numeric illustration assumes a per-split hit rate of 1/4, and we did not measure the interaction.
- The fixed version matches keys of other types by their `str()`. A float key such as `5.0` becomes `"5.0"`, does not match node `"5"` and makes the run invalid. We did not run this on the real grader.
- We read the prompt text from the grader image's English copy and the Chinese source copy, which agree on the contract sentences. We did not pull the agent's working image.

## Reproduce

- Original grader image: `sha256:518c105e…`.
- Scoring-function checks: `evidence/scripts/graph_node_classification/check_confidence_mapping.py`, `check_invalid_prediction_shrink.py`, and `run_judge_variants.sh` (with `wrapper_solution.py`).
- Side-by-side run: `repairs/graph_node_classification-v2/paired/run.sh` (results in `paired/results.md`).
- Patch: `repairs/graph_node_classification-v2/repair.patch`.
- Supporting records: `repairs/graph_node_classification-v2/` (the folder holding the fixed version: source-lock.json, captured outputs of the side-by-side run).
