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

"–" marks a result the grader reports as `valid: false`. EdgeBench's harness still records its score (`graded.md` shows it), and the task's `valid_then_score` selection leaves it out.

## Notes

- **Quality metrics.** overall, macro/micro F1, balanced accuracy and ECE are identical
  between v1 and v2 for every valid submission, to all printed digits.
- **final score.** It differs by at most 8.1e-5 (baseline 0.292783 against 0.292702), which is about 0.008 normalized points. This
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

## Revision v2.1 (2026-10-13): integer node-id keys

**Why.** An independent review (GitHub issue #66) found that neither the original nor the first fixed
verifier (`32caddb1…`) implements the prompt's key contract. `solution/problem.md` says "The keys of
`predictions` must be test node IDs, which can be strings or values convertible to strings", and
`input_data["test_nodes"]` is a list of integers. Both verifiers look predictions up under the answer
key's string IDs only. A complete integer-keyed submission therefore matches no node: the original
scores it valid with every metric 0, and the first fixed verifier rejects it as "predictions
missing". The note in "Not run" above is superseded by this section, and the README's earlier claim
that the original count check rejects such submissions was wrong: the count of a complete
integer-keyed submission matches.

**Change.** `evaluate` converts the keys of `predictions` and `confidences` with `str(key)` (new
`_str_keyed`) before any check and raises `ValueError` when two keys give the same string. Everything
else is unchanged. Revised verifier: `7b4860ec…` (5531 B), tag `f2ddd52992ae-ebv-v2.1`.

**Jobs.** The 21 judgements (7 submissions × 3 verifiers, ~180 s each) do not fit one worker's time
limit, so each run is split by submission over two workers, each judging its submissions with all
three verifiers: `evidence/runs/graph_node_classification-v2-paired-v21a` (baseline, neighbor,
neighbor_intkeys, dupkeys_after_str; sandbox `iqhpe6p2gldqudfukdo5e`, exit 0 in 2187 s) and `-v21b`
(shrink, nanconf, missing_half; sandbox `ibyv8m7k77auzo8m775k8`, exit 0 in 1706 s). In each job the
v2.1 image was built from a copy of this package: the package's own `materialize.sh` pulled the
pinned image, extracted the original verifier, applied `repair.patch` and verified the output
(`materialize_rc=0`, `7b4860ec…`; `result/out/materialized_sha256.txt`), and the package
`Dockerfile` built it. The first fixed verifier (`32caddb1…`) was built from `v2prevctx/`. In-image
pins (`pins_v1.txt`, `pins_v2prev.txt`, `pins_v2.txt`): `verifier.py` `044cd50e…`, `32caddb1…` and
`7b4860ec…`; `runner.py`, `judge_eval.py`, `config.yaml` and the shipped solution unchanged. Same
judging as above (TaskSpec `eval.sh`, `--network none`, 4 CPUs, 6 GB, `SEB_PARALLEL_WORKERS=4`, full
10 splits); no judgement timed out. New submissions from `make_subs.py`:

- `neighbor_intkeys`: `neighbor` with `preds[t]` / `confs[t]` instead of `preds[str(t)]` /
  `confs[str(t)]`, where `t` is the integer node ID. Same predictions and confidences as `neighbor`.
- `dupkeys_after_str`: `neighbor_intkeys` with the last test node dropped and the first node repeated
  under its string key, so the key count still equals the number of test nodes.

| Submission | Role | Verifier | Harness valid | final score | Normalized 0–100 | overall (quality) | macro_f1 | one_minus_ece |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| baseline (shipped solution.py), v2.1 run | valid control | v1 | true | 0.292337 | 29.234 | 0.332624 | 0.238512 | 0.925034 |
| baseline | valid control | first fixed | true | 0.292478 | 29.248 | 0.332624 | 0.238512 | 0.925034 |
| baseline | valid control | v2.1 | true | 0.292253 | 29.225 | 0.332624 | 0.238512 | 0.925034 |
| neighbor (string keys), v2.1 run | valid control | v1 | true | 0.240670 | 24.067 | 0.281108 | 0.221556 | 0.758336 |
| neighbor | valid control | first fixed | true | 0.240663 | 24.066 | 0.281108 | 0.221556 | 0.758336 |
| neighbor | valid control | v2.1 | true | 0.240656 | 24.066 | 0.281108 | 0.221556 | 0.758336 |
| **neighbor_intkeys** (neighbor keyed by integer node IDs) | **trigger (good faith)** | v1 | **true** | −0.040546 | **0.000** | **0.000000** | 0.000000 | 0.000000 |
| neighbor_intkeys | trigger (good faith) | first fixed | **false** | – | – | runner error: `predictions missing for 1041 test node(s), e.g. '0'` | | |
| neighbor_intkeys | trigger (good faith) | v2.1 | true | 0.240886 | 24.089 | 0.281108 | 0.221556 | 0.758336 |
| dupkeys_after_str (two keys share one `str()`) | invalid control | v1 | **true** | 0.198962 | 19.896 | 0.239264 | 0.200000 | 0.592639 |
| dupkeys_after_str | invalid control | first fixed | false | – | – | runner error: `predictions missing for 1040 test node(s), e.g. '9'` | | |
| dupkeys_after_str | invalid control | v2.1 | false | – | – | runner error: `predictions: duplicate node id after str(): '7'` | | |
| shrink (one real prediction, rest `"x"`), v2.1 run | trigger | v1 | true | 0.159660 | 15.966 | 0.200000 | 0.200000 | 0.200000 |
| shrink | trigger | first fixed | false | – | – | runner error: `prediction for node '3' is not an integer class id: 'x'` | | |
| shrink | trigger | v2.1 | false | – | – | runner error: `prediction for node '9' is not an integer class id: 'x'` | | |
| nanconf (baseline predictions, NaN confidences), v2.1 run | clipping left unchanged | v1 | true | 0.270547 | 27.055 | 0.311437 | 0.238512 | 0.713160 |
| nanconf | clipping left unchanged | first fixed | true | 0.270468 | 27.047 | 0.311437 | 0.238512 | 0.713160 |
| nanconf | clipping left unchanged | v2.1 | true | 0.270388 | 27.039 | 0.311437 | 0.238512 | 0.713160 |
| missing_half (half the test nodes), v2.1 run | invalid control | v1 | false | – | – | coverage check: `predictions=520 expected=1041` | | |
| missing_half | invalid control | first fixed | false | – | – | runner error: `predictions missing for 521 test node(s)` | | |
| missing_half | invalid control | v2.1 | false | – | – | runner error: `predictions missing for 521 test node(s)` | | |

"–" marks `valid: false`, as above. The node named in an error message is the first failing node
of whichever split fails first; with 4 parallel split workers that split can differ between runs.
The normalized score of `neighbor_intkeys` under v1 is the rescaled final score −0.040546 clipped to 0.

**Spec checks.**

- **Trigger (good faith).** The integer-keyed honest solver is valid with every quality metric 0
  under the original, invalid under the first fixed verifier, and scores under v2.1 exactly like its
  string-keyed twin: overall, macro_f1, micro_f1, balanced accuracy and ECE identical to all printed
  digits (0.281108 overall); the final scores differ only by the wall-time penalty.
- **Bad control.** Two keys that share one `str()` make the run invalid under v2.1. The original
  scores it valid on the one node it can match per split (overall 0.239264); the first fixed
  verifier rejects it as incomplete.
- **Earlier arms unchanged.** baseline, neighbor, nanconf, shrink and missing_half keep their verdicts
  under all three verifiers, and every valid one has the same quality metrics under all three and as
  in the first run of this package (top of this file).
- **Verdict:** **accepted** (verifier v2.1, `7b4860ec…`).

## Repeatability of revision v2.1

Each of the two v2.1 jobs was run three times on fresh E2B workers:

| Job | Run 1 | Run 2 (`-rep2`) | Run 3 (`-rep3`) |
| --- | --- | --- | --- |
| `graph_node_classification-v2-paired-v21a` | `iqhpe6p2gldqudfukdo5e`, 2187 s | `ijnkd798ezvajczxhjjhc`, 1866 s | `iutql8v0mcuudt1rhokqu`, 2228 s |
| `graph_node_classification-v2-paired-v21b` | `ibyv8m7k77auzo8m775k8`, 1706 s | `i8sfmh4wdvbtvqk1k91d7`, 1606 s | `itz4nrtxonpo6pxgs3vdn`, 1605 s |

All six closed with `status: exit=0`, `materialize_rc=0` and `build_rc=0` for both fixed images, no
judgement timed out, and every run's results were collected and graded by that job's `grade.py`
(`graded.md`, `graded.json`). Across the three runs, all 21 results (7 submissions × original,
first fixed and v2.1 verifier) keep the same validity, and every valid result has the same quality
metrics (overall, macro_f1, micro_f1, balanced accuracy, one_minus_ece) to all printed digits. Only
the final score moves, through the wall-time penalty: across the three runs and three verifiers,
baseline 29.190–29.411, neighbor 24.055–24.231, neighbor_intkeys under v2.1 24.062–24.207 (0.000 under
the original in every run), nanconf 27.039–27.151, shrink under the original 15.966–15.992,
dupkeys_after_str under the original 19.873–20.025 (normalized 0–100). The node named in an error
message varies between runs, as noted above; the counts do not. The staged first fixed verifier
(`v2prevctx/files/`, `32caddb1…`) was removed after collection, and the shipped baseline copied into
`v21a*/subs/baseline/` was moved out of the repository (`subs/baseline/NOT-PUBLISHED.md`).
