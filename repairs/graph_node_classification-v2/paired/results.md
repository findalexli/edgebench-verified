# graph_node_classification v2: paired evaluation

## Job

- **Run:** one E2B worker (sandbox `i73vtw11nt4fe9y4v448g`) ran `run.sh` in 2685 s, exit 0, then
  was killed by its exact ID. Raw captures are in `result/out/`.
- **v1:** `seededge/edgebench.judge.graph_node_classification@sha256:518c105e…`. In-image
  `verifier.py` is `044cd50e…`.
- **v2:** built in the worker from `v2ctx/Dockerfile` (image `sha256:1a8d32d0…`). In-image
  `verifier.py` is `32caddb1…`, the same as `files/`.
- **Unchanged in both images:** `runner.py`, `judge_eval.py`, `config.yaml` and the shipped
  `solution.py` (`pins_v1.txt`, `pins_v2.txt`).

## Method

- **Judging:** every submission ran the original eval_cmd through the TaskSpec `eval.sh`, with
  `--network none`, 4 CPUs, 6 GB and `SEB_PARALLEL_WORKERS=4`. This is the full 10-split run.
  All 10 evals exited normally in about 170 s and none timed out.
- **Grading:** `grade.py` graded the captures with the repo's `grade_output` and
  `rescale_score` (linear 0..1, shown here as 0–100).
- **Submissions:** self-contained `solution/solution.py` files built by `make_subs.py` from the
  shipped baseline.

## Paired table

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

## Notes

- **Quality metrics.** overall, macro/micro F1, balanced accuracy and ECE are identical
  between v1 and v2 for every valid submission, to all printed digits.
- **final score.** It differs by at most 8e-5, which is about 0.008 normalized points. This
  comes only from the wall-time penalty `0.01·log(time)`, which varies between runs. It does
  not come from the repair.
- **nanconf.** It scores exactly like the 0.0-confidence case in the review, in both v1 and
  v2. The score-neutral clipping is intentionally unchanged.

## Spec checks

- **Trigger.** v1 accepts a run whose predictions are almost all non-integer as valid, and
  scores each split on one node. v2 rejects it (`valid: false`) through the existing runner
  failure path.
- **Valid controls.** The baseline, an honest independent solver and the NaN-confidence
  variant have unchanged quality metrics, and their scores differ only by the timing penalty.
- **Invalid control.** Missing predictions are rejected in both versions. v1 rejects them
  through `judge_eval`'s coverage count, v2 already in the verifier.
- **Verdict:** **accepted.**

## Not run

- No stronger honest solvers were run.
- No submission with non-string node-ID keys was run. Such a submission becomes invalid in
  v2 (see the README's compatibility note).
