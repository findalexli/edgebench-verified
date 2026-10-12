# order_addition_permutation_optimization v2: paired evaluation

## Job

- **Run:** one E2B worker (sandbox `id4znglqvxy1dtb0o7f02`) ran `run.sh` in 101 s, exit 0, then
  was killed by its exact ID. Raw captures are in `result/out/`.
- **v1:** `seededge/edgebench.judge.order_addition_permutation_optimization@sha256:6d1a1506…`.
- **v2:** built in the worker from `v2ctx/Dockerfile` (image `sha256:fd099ff2…`).
- **Preflight** (`preflight_v1.txt`, `preflight_v2.txt`): both images collect 5 tests. The
  checker hash is `4f1d5fad…` in v1 and `37e7bae6…` in v2. The helper `337837af…`, the `.so`
  and the baseline file are identical in both.

## Method

- **Submissions:** generated once in the v1 image by `make_result.py`, which calls only the
  public black-box function. Each submission is `final_result.txt` plus the solver source.
  - `identity`: the identity permutation, 1 call.
  - `search`: 60 s of random-swap local search, 1707 calls.
  - `badcost`: identity with the reported cost halved.
  - `dup`: identity with a duplicated element.
- **Judging:** each submission ran the original eval_cmd through the TaskSpec `eval.sh` in a
  fresh `--network none` container (`judge_one.sh`).
- **Grading:** `grade.py` uses the repo's `grade_output`, `rescale_score` and `select_best`.

## Paired table

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

Every eval exited normally (rc 0) and none timed out.

## Selection (task policy `pass_rate_first`, repo `select_best`)

| Submission order | v1 selects | v2 selects |
| --- | --- | --- |
| identity, search | **identity** (3.3e-09), frozen on the first | **search** (0.00937) |
| search, identity | search (0.00937) | search (0.00937) |
| dup, identity, search | **identity** (3.3e-09) | **search** (0.00937) |
| badcost, identity, search | **identity** (3.3e-09) | **search** (0.00937) |

## Spec checks

- **Trigger.** Under v1 every valid submission passes 4/5, so selection freezes on the first
  valid one. Under v2 they pass 5/5 and the better submission is selected.
- **Valid controls.** Raw and normalized scores are identical between v1 and v2.
- **Invalid controls.** The misreported-cost and non-permutation submissions fail their
  ordinary test and produce no score in both versions. They are never selected over a valid
  submission.
- **Verdict:** **accepted.**

## Observation (harness, unchanged by this repair)

`pass_rate_first` reports `best_score = pass_rate` when the chosen entry has no score. A run
whose only submissions were invalid would therefore show a best_score of 0.6 under v1, or 0.8
under v2, rather than none. This is pre-existing harness behaviour and outside this repair.
