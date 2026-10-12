# Order Addition Permutation Optimization (`order_addition_permutation_optimization`)

Status: reviewed by the coordinator, 2026-10-12

- **Domain:** Combinatorial Optimization
- **Decision:** Repair v2. An integrity test expects an outdated helper hash, so every submission is capped at pass rate 0.8. Under the task's `pass_rate_first` policy, this freezes the run on its first valid submission.

## What the task promises

The prompt asks for a permutation of 1..1000 that minimises a black-box response, and lists what "the evaluator will check":

- no private access
- the baseline file is unmodified
- `final_result.txt` exists
- `final_pai` is a valid permutation
- `final_cost` matches the recomputed cost

A continuous score is then "calculated using `score_cost_num(cost, num)` from the evaluator-side private `tests/score_vcpom_result.py`". Nothing in the contract mentions a helper fingerprint. The solver cannot affect one either, because `tests/` is excluded from submissions.

## What we checked and how

- **Hash check.** We hashed the installed helper inside the pulled judge image and compared it with the literal the test expects. Diffing the two helper versions shows that only comments, a docstring and example labels differ. `parse_result_file` and `score_cost_num` are functionally identical.
- **Native runs.** We ran the original `eval_cmd` (`python -m pytest tests/test_final_result.py -s -v`) in the pinned judge image, under `--network none --memory 2g --cpus 2`, on valid and invalid controls. Each run was repeated after a one-literal correction.
- **Grading and selection.** We fed the saved logs through the harness's own `grade_output`, `rescale_score` and `select_best`, for both the upstream and the maintained harness versions.
- **Paired evaluation.** One E2B worker ran a paired v1/v2 evaluation through the TaskSpec `eval.sh`, with a fresh `--network none` container for each submission. A preflight confirmed that each image collects 5 tests.
- **Original identity:**
  - judge image `seededge/edgebench.judge.order_addition_permutation_optimization@sha256:6d1a1506…`
  - `tests/test_final_result.py` sha256 `4f1d5fad…`
  - installed `tests/score_vcpom_result.py` `337837af…`
  - expected literal in the test `3023b9a4…`

## What we found

**Confirmed, with impact broader than the earlier wording.** `test_private_judge_files_are_available` asserts that the installed helper's sha256 equals `3023b9a4…`. That is the hash of an earlier Chinese-comment helper. A later image layer replaced the helper with an English-comment translation, `337837af…`, and the expected literal was never updated. The check is unconditional and fails for every submission.

- **Per-submission score is correct.** Only this one test fails. The other four still run, and `TOTAL_SCORE` is computed with the installed helper, which is functionally identical.
- **Pass rate is capped.** A fully correct submission gets pass rate 0.8 instead of 1.0.
- **Selection freezes.**
  - `pass_rate_first` compares scores only when both pass rates are 1.0.
  - Otherwise, a later entry wins only with a strictly higher pass rate.
  - Every valid submission is capped at 0.8, so the run's `best_score` / `best_round` stay on the **first** valid submission.
- **Example under the original evaluator.** Take two valid submissions in the order identity, then search:
  - The identity permutation scores 3.3e-09.
  - The search result scores higher.
  - v1 selects identity. The better later submission is ignored.
- **Maximum effect:** material. Later improvements are ignored in the run-level best score. Some consumers instead take the maximum over all submissions, which is order-independent. Whether a published number is wrong therefore depends on which consumer produced it.

An earlier audit withheld this task with the wording "valid reports and nonzero scores remain possible". Re-checking showed that statement is true per submission. The defect still reaches the reported run score through selection. The fix is one literal, outside the solver's control, so the decision is a versioned repair.

## Repair

v2 changes one literal in `tests/test_final_result.py`: `EXPECTED_SCORE_HELPER_SHA256` becomes the installed helper's hash, `337837af…`. The helper, `.so`, baseline file, prompt, work image, parser, selection and rescale are all unchanged. The task JSON changes only `judge.image_tag`.

| Submission | Role | Image | Tests passed | pass_rate | Raw TOTAL_SCORE | Normalized 0–100 | Failing test |
| --- | --- | --- | --- | ---: | ---: | ---: | --- |
| identity | valid | v1 | 4/5 | 0.80 | 3.3e-09 | 3.3e-09 | fingerprint |
| identity | valid | v2 | **5/5** | **1.00** | 3.3e-09 | 3.3e-09 | – |
| search | valid, better | v1 | 4/5 | 0.80 | 0.0093733018 | 0.0093733018 | fingerprint |
| search | valid, better | v2 | **5/5** | **1.00** | 0.0093733018 | 0.0093733018 | – |
| badcost (misreported cost) | invalid control | v1 | 3/5 | 0.60 | none | none | fingerprint, cost mismatch |
| badcost | invalid control | v2 | 4/5 | 0.80 | none | none | cost mismatch |
| dup (not a permutation) | invalid control | v1 | 3/5 | 0.60 | none | none | fingerprint, permutation |
| dup | invalid control | v2 | 4/5 | 0.80 | none | none | permutation |

Selection (task policy `pass_rate_first`, repo `select_best`):

| Submission order | v1 selects | v2 selects |
| --- | --- | --- |
| identity, search | **identity** (3.3e-09), frozen on the first | **search** (0.00937) |
| search, identity | search (0.00937) | search (0.00937) |
| dup, identity, search | **identity** (3.3e-09) | **search** (0.00937) |
| badcost, identity, search | **identity** (3.3e-09) | **search** (0.00937) |

An earlier native repair pilot failed with "zero tests". The cause was in its transport setup and is recorded as unknown, and nothing in it points at the checker literal. This package builds v2 directly from the pinned base, and both preflights collected 5 tests.

**Score compatibility:** per-submission raw and normalized scores are unchanged, bit for bit. Pass rates change: a legal submission now gets 5/5 instead of 4/5. The run-level `best_score` / `best_round` under `pass_rate_first` are not comparable with v1 whenever a run had more than one valid submission and a later one scored higher: v1 kept the first, and v2 keeps the best.

## Limits and what was not run

- No model or solver re-runs. Effects are shown only on authored controls and counterexamples.
- The submissions are simple controls: the identity permutation, and short random-swap search runs (30 s in the review, 60 s in the paired run). They are far from the reference cost. The selection effect does not depend on score magnitude.
- Selection was computed with the repo's `select_best` on saved reports, not through a live `judge_server` run. The work image was not executed.
- How often runs in historical leaderboards had a better later submission was not measured.
- One harness behaviour is unchanged by this repair. `pass_rate_first` reports `best_score = pass_rate` when the chosen entry has no score. So a run with only invalid submissions shows 0.6 under v1, or 0.8 under v2.

## Reproduce

- Review scripts:
  - `evidence/scripts/order_addition_permutation_optimization/run_judge.sh`
  - `make_result.py`
  - `grade_and_select.py`
  - saved logs in `observed/`
- Paired evaluation: `repairs/order_addition_permutation_optimization-v2/paired/run.sh` (results in `paired/results.md`)
- Patch: `repairs/order_addition_permutation_optimization-v2/repair.patch`

Supporting records: `repairs/order_addition_permutation_optimization-v2/` (source-lock.json, paired captures).

