# Order Addition Permutation Optimization (`order_addition_permutation_optimization`)

**Outcome:** Fixed. <mark>A file-integrity test expects an outdated fingerprint of a helper file, so every submission fails one of five tests; under this task's rule for picking a run's best submission, the run then stays on its first scored submission and ignores better later ones.</mark>

![Bar chart of the nine submissions of one real agent run, in the order they were graded: five early ones with no score, then 3.79, 15.91, 15.91 and 41.24 out of 100; the bar kept by the original checker is gold, the one kept by the fixed checker green, the others blue. Below it, tests passed by each submission: the original checker gives 2/5 or 4/5 and keeps submission 6 (3.79); the fixed checker gives 3/5 or 5/5 and keeps submission 9 (41.24).](figures/order_addition_permutation_optimization.svg)

*An outdated file check made a real agent run keep 3.79 out of 100 although a later submission earned 41.24. The agent orders the numbers 1 to 1000 to make a hidden cost small; one of the five tests expects an older version of a helper file, so every submission fails it. The run keeps the submission that passes the most tests and compares scores only when all five pass, so every scored submission ties at 4 of 5 and the first one stays. With the expected file version corrected, the scored submissions pass 5 of 5, each score is unchanged, and the run keeps 41.24.*

## What the task asks

The prompt asks for a permutation (an ordering) of 1..1000 that minimises a black-box response. It lists what "the evaluator will check": no private access, an unmodified baseline file, that `final_result.txt` exists, that `final_pai` is a valid permutation, and that `final_cost` matches the recomputed cost.

The evaluator then gives a continuous score "calculated using `score_cost_num(cost, num)` from the evaluator-side private `tests/score_vcpom_result.py`". Nothing in the contract mentions a helper fingerprint. The solver cannot affect one, because submissions exclude `tests/`. Category: Combinatorial Optimization.

## What goes wrong

One test always fails. `test_private_judge_files_are_available` asserts that the installed helper's sha256 fingerprint equals `3023b9a4…`. That is the fingerprint of an earlier helper with Chinese comments. A later image layer replaced the helper with an English-comment translation, `337837af…`, but nobody updated the expected value. The two helper versions differ only in comments, a docstring and example labels, and `parse_result_file` and `score_cost_num` work identically in both. The check is unconditional and fails for every submission.

- Each submission's score is still correct. Only this one test fails; the other four still run, and the grader computes `TOTAL_SCORE` with the installed helper.
- The pass rate is capped. A fully correct submission gets pass rate 0.8 instead of 1.0.
- The run's choice of best submission freezes. This task's rule (`pass_rate_first`) keeps the submission that passes the most tests and compares scores only when both pass rates are 1.0; otherwise a later submission wins only with a strictly higher pass rate. Every submission is capped at 0.8 and every scored one reaches it, so the run's `best_score` / `best_round` stay on the **first** scored submission.

For example, we gave the original grader two valid submissions, identity first and then search. The identity permutation scores 3.3e-09, and the search result scores higher. The grader should keep search; it keeps identity and ignores the better later submission.

## How much it matters

This changes the recorded score of any run with more than one valid submission where a later one scores higher, because the run's best score ignores the later improvement. Some consumers instead take the maximum over all submissions, which does not depend on order, so whether a published number is wrong depends on which consumer produced it. Each submission's own score is unaffected.

In a real agent run, we regraded all 9 submissions of a third-party Claude Opus 5.5 run (four hours; `evidence/runs/opus55-regrade2-oa/`, `result/worker.json` `status: exit=0`; combined in `evidence/runs/opus55-regrade2-summary/summary.json`) with the original and the fixed grader. Each submission's score is identical under both. The 4 submissions with a score pass 4/5 tests under the original grader and 5/5 under the fixed one; the 5 earlier automatic submissions, which had no `final_result.txt` yet, pass 2/5 and 3/5. The original grader therefore keeps the run's first scored submission, 3.79 out of 100, and the fixed grader keeps the last, 41.24.

## The fix

The fixed version changes one value in `tests/test_final_result.py`: `EXPECTED_SCORE_HELPER_SHA256` becomes the installed helper's fingerprint, `337837af…`. The helper, `.so`, baseline file, prompt, agent's working image, parser, the rule for picking the best submission and the score scale are unchanged. The task JSON changes only `judge.image_tag`.

| Submission | Role | Grader | Tests passed | pass_rate | Raw TOTAL_SCORE | Score out of 100 | Failing test |
| --- | --- | --- | --- | ---: | ---: | ---: | --- |
| identity | valid | Original | 4/5 | 0.80 | 3.3e-09 | 3.3e-09 | fingerprint |
| identity | valid | Fixed | **5/5** | **1.00** | 3.3e-09 | 3.3e-09 | – |
| search | valid, better | Original | 4/5 | 0.80 | 0.0093733018 | 0.0093733018 | fingerprint |
| search | valid, better | Fixed | **5/5** | **1.00** | 0.0093733018 | 0.0093733018 | – |
| badcost (misreported cost) | invalid test submission | Original | 3/5 | 0.60 | none | none | fingerprint, cost mismatch |
| badcost | invalid test submission | Fixed | 4/5 | 0.80 | none | none | cost mismatch |
| dup (not a permutation) | invalid test submission | Original | 3/5 | 0.60 | none | none | fingerprint, permutation |
| dup | invalid test submission | Fixed | 4/5 | 0.80 | none | none | permutation |

We computed the run's choice of best submission with EdgeBench's `select_best` under the task rule `pass_rate_first`.

| Submission order | Original grader picks | Fixed grader picks |
| --- | --- | --- |
| identity, search | **identity** (3.3e-09), stuck on the first | **search** (0.00937) |
| search, identity | search (0.00937) | search (0.00937) |
| dup, identity, search | **identity** (3.3e-09) | **search** (0.00937) |
| badcost, identity, search | **identity** (3.3e-09) | **search** (0.00937) |

Each submission's raw result and score out of 100 are unchanged, bit for bit. Pass rates change, and a legal submission now gets 5/5 instead of 4/5. The run's `best_score` / `best_round` under `pass_rate_first` are not comparable with the original version whenever a run had more than one valid submission and a later one scored higher. The original version kept the first, and the fixed version keeps the best.

## How we checked it

- We hashed the installed helper inside the original public image, pinned by digest, and compared it with the value the test expects. The original `eval_cmd` (`python -m pytest tests/test_final_result.py -s -v`) ran under `--network none --memory 2g --cpus 2` on valid and invalid test submissions.
- To find the choice of best submission, we fed the saved logs through the harness's own `grade_output`, `rescale_score` and `select_best`, from EdgeBench's harness (`sforge` at `6e4e5f4`).
- For a formal check in TLA+, we model-checked a bounded model of the selection rule, tied to `selection.py` and `grading.py` line by line. It covered 5,421,361 states with no violation, and the checker finds the violations the note describes in three further configurations, `k1` to `k3` (`evidence/formal/tla/order_addition_permutation_optimization/`, `evidence/formal/notes/order_addition_permutation_optimization.md`).
- In the side-by-side run of the original and fixed graders, each submission ran in a fresh `--network none` container through the TaskSpec `eval.sh`. A check beforehand confirmed that each image collects 5 tests. We repeated the run three times with no verdict change ([`data/paired-repeatability.md`](../data/paired-repeatability.md)).

## Limits

- Apart from the regraded real run above, the effects shown come from test submissions and counterexamples we wrote. The real run is one model and one four-hour run, not the 12-hour leaderboard runs.
- The submissions are simple ones, the identity permutation and short random-swap search runs (30 s and 60 s), far from the reference cost. The effect on the choice of best submission does not depend on score size.
- We computed the choice of best submission with EdgeBench's `select_best` on saved reports, not through a live `judge_server` run, and we did not run the agent's working image.
- We did not measure how often past leaderboard runs had a better later submission.
- This repository does not keep the earlier helper (`3023b9a4…`), so the statement that the two helpers differ only in comments rests on the earlier extraction. Scores do not depend on it, because both versions grade with the installed helper.
- The fixed image is not in any registry; users build it with the package's `materialize.sh` and `Dockerfile` (rebuilt from scratch on a clean machine in `evidence/runs/materialize-check-g2`, `status: exit=0`).
- The fix also changes one harness fallback. `pass_rate_first` reports `best_score = pass_rate` when the chosen submission has no score (`sforge/harness/selection.py`, `_pass_rate_first`). A run with only invalid submissions (for example badcost) therefore reports 0.6 under the original version and 0.8 under the fixed version. In both versions that value is above every valid submission's score measured here (3.3e-09 to 0.0094 out of 100, table above), so an all-invalid run reports a higher `best_score` than these valid runs.

## Reproduce

- Original grader image: `sha256:6d1a1506…`.
- Scripts: `evidence/scripts/order_addition_permutation_optimization/run_judge.sh`, `make_result.py`, `grade_and_select.py`; saved logs in `observed/`.
- Side-by-side run: `repairs/order_addition_permutation_optimization-v2/paired/run.sh` (results in `paired/results.md`).
- Patch: `repairs/order_addition_permutation_optimization-v2/repair.patch`.
- Supporting records: `repairs/order_addition_permutation_optimization-v2/` (the folder holding the fixed version: source-lock.json, captured outputs of the side-by-side run).
