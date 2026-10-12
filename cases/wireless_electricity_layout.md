# Wireless Electricity Layout (`wireless_electricity_layout`)

Status: reviewed by the coordinator, 2026-10-12

- **Domain:** Combinatorial Optimization
- **Decision:** Retain with note. Under the upstream harness, a compile failure can be reported as the raw-best submission, but this can never change a normalized score.

## What the task promises

The prompt says: "Your solution is scored on **50 fixed hidden test cases**. Final score = sum of (P+Q) across all hidden cases. **Lower is better.**" It also says: "A valid baseline `solution.cpp` already exists. Improve it."

The judge uses the `score_sum` parser, `minimize`, `score_first` selection and a `piecewise_log_min` rescale with these anchors:

- baseline 2.606e16;
- rank30 2.445e15;
- rank1 3.624e14;
- super_anchor 1.812e14.

The prompt says nothing about failure penalties.

## What we checked and how

- **Native runs.** The original `eval_wirel.sh` ran in the pinned judge image locally, with `--network none --memory 2g --cpus 2`. There were three submissions:
  - the unchanged shipped baseline;
  - a submission that does not compile;
  - the baseline modified to abort on 8 cases.
- **Harness grading.** The saved logs were graded with the real harness functions (`grade_output` → `rescale_score` → `select_best`). We used both the upstream harness at `6e4e5f4`, with hashes matching its lock file, and the maintained harness in this repository.
- **Monotonicity argument, checked on 200,000 random histories.** A short argument from the rescale and selection source shows that a normalized score cannot change. We checked it by running 200,000 random submission histories through the upstream code, with a compile-failure entry inserted at every position, and comparing the normalized and raw results with and without that entry.
- **Original identity.**
  - Judge image: `seededge/edgebench.judge.wireless_electricity_layout@sha256:78c341ca6e52849dfa7644f6664cbdbf87cd144cc72ff156c2508f5d623906d9`.
  - Task JSON: sha256 `050ab35f99431e94ee6279fcd23dc06c9a795ee7b9f26b7d9ec4eadb3e060809`.
  - `/tmp/eval_wirel.sh`: `c670ff6d7ac8a0042666c275b8bc947ddc93263f0b898fdab7078e208ce7dd8f`.
  - Shipped baseline `solution.cpp`: `811fe1e54452f935563de0480bd03a0b6270752efa7b45e01fba578116cb9256`.
  - `tools/bin/tester`: `a7d59fd3cc9796305d55d280b5ebe1455b80ae7df13425a47bde88433cd9cf87`.

## What we found

**Confirmed, narrower: a compile failure is penalized once, not per case.** The original evaluator penalizes the two kinds of failure differently:

- A missing file or compile failure gets **one** penalty line, `CASE 0000 CE score=1e17`, with `TOTAL_SCORE 1e17`.
- Each per-case timeout, runtime error or wrong answer adds `1e17` **per case**.

The shipped feasible baseline totals more than 1e17, so in raw units it ranks below a program that does not compile.

| Submission | Original evaluator output |
|---|---|
| `baseline`: the **shipped** baseline, unchanged | 50/50 OK, `TOTAL_SCORE 663100735542396309` (6.63e17) |
| `ce`: does not compile | `CASE 0000 CE`, `TOTAL_SCORE 100000000000000000` (1e17), `CASES_TOTAL 50` |
| `re_some`: baseline that aborts on 8 cases | 42/50 OK, `TOTAL_SCORE 1356919142089112260` (1.36e18) |

**Under the upstream harness.** The compile-failure report is valid, with raw 1e17 and normalized 0.0. It is selected over the shipped baseline and over `re_some` in every order tested. All of these have a normalized score of 0.0.

**Under the maintained harness.** The compile-failure report is rejected as inconsistent: its declared `CASES_TOTAL` disagrees with its CASE records. The shipped baseline, or `re_some`, is selected instead, again with normalized 0.0.

**A normalized score can never change.** The rescale is non-increasing and equals 0 for any raw total at or above the baseline anchor (2.606e16). The compile-failure total of 1e17 is above that anchor. A compile failure can be selected only when every other entry has a raw total of at least 1e17, and those entries also normalize to 0. The 200,000-history check (its output is not saved in this repository) found **0** changes to the selected normalized score and 0 changes to the maximum normalized score. Over the same histories it found 43,336 changes to the raw `best_score`.

Maximum score effect: 0 normalized (monotonicity argument, checked on 200,000 random histories). The defect affects only raw-unit reporting and which submission is named "best".

**Earlier withholding.** An earlier audit withheld the original task because "Raw scoring ranks an observed compilation failure above a feasible solution." Re-checking confirms the raw-ranking inversion, and it reproduces with the unmodified shipped baseline. It cannot change any normalized score, and the maintained harness does not exhibit it, so withholding is not justified on this ground.

## Note for users

No repair. The note says: in the original evaluator a compile failure receives one 1e17 penalty in total, while each failed case receives 1e17. Under the upstream harness, a non-compiling submission can therefore be selected as raw-best over a feasible but poor one, including the shipped baseline. This never changes a normalized score, because all such raw totals normalize to zero. The maintained harness rejects the inconsistent compile-failure report.

## Limits and what was not run

- No model or solver re-runs were done. Effects are shown only on authored controls and counterexamples.
- Three submissions were run. The shipped baseline is the only feasible control, and no competitive solution was run.
- The upstream harness came from the canonical workspace copy, verified against its lock file, and was not re-fetched from GitHub.
- Selection was exercised offline with the real harness functions, not through a live judge or agent run.
- Historical incidence was not measured.

## Reproduce

- Native runs: `evidence/scripts/wireless_electricity_layout/run_judge.sh OUTDIR` (submissions in `subs/`; saved logs in `observed/`)
- Harness grading and selection: `evidence/scripts/wireless_electricity_layout/grade_and_select.py HARNESS_ROOT TASKS_DIR LOGDIR`
- Randomized property check: `evidence/scripts/wireless_electricity_layout/normalized_invariance.py`

