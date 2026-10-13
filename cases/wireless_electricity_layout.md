# Wireless Electricity Layout (`wireless_electricity_layout`)

**Outcome:** Kept, with a note. <mark>Under the upstream harness, a program that fails to compile can be reported as the best submission by raw result, but this can never change a score out of 100.</mark>

## What the task asks

The agent improves a provided C++ program for a layout puzzle. The prompt says: "Your solution is scored on **50 fixed hidden test cases**. Final score = sum of (P+Q) across all hidden cases. **Lower is better.**" It also says: "A valid baseline `solution.cpp` already exists. Improve it."

The grader sums the per-case scores (`score_sum` parser) and treats lower as better (`minimize`). The run keeps the submission with the best score (`score_first` selection). The raw result (before conversion to 0–100) is converted to a score out of 100 on a piecewise logarithmic scale (`piecewise_log_min`). Its reference points are named baseline 2.606e16, rank30 2.445e15, rank1 3.624e14 and super_anchor 1.812e14. The prompt says nothing about failure penalties. Category: Combinatorial Optimization.

## What we checked

**Rule.** The original grader penalizes the two kinds of failure differently:

- A missing file or compile failure gets **one** penalty line, `CASE 0000 CE score=1e17`, with `TOTAL_SCORE 1e17`.
- Each per-case timeout, runtime error or wrong answer adds `1e17` **per case**.

**A single failed case scores the whole submission 0 out of 100.** One failed case puts the raw total at or above 1e17, which is above the baseline reference point (2.606e16), so the submission scores 0 (`eval_wirel.sh`, `BAD_SCORE=100000000000000000`; `piecewise_log_min` returns 0 at or above the baseline point). The prompt says only "Final score = sum of (P+Q) across all hidden cases" and does not say what a failed case scores. The time limit is 5 s of wall-clock time per case (`TIME_LIMIT=5`, `timeout`), with 2 cases run at once (`MAX_JOBS=2`) and no CPU limit set for the grader (`tasks/wireless_electricity_layout.json` has no `cpu_limit`). So whether a solver that runs close to 5 s times out depends on the grader's machine. Under `score_first`, an earlier submission with no failed case is still kept. This effect was not measured.

**The shipped baseline scores 0.** Its raw total, 6.631e17 (`observed/baseline.log`), is 25.4 times the baseline reference point of 2.606e16, so the "valid baseline" that the prompt supplies scores 0 out of 100. Where the reference points come from is not stated in the task and was not checked.

**Example.** The shipped working baseline totals more than 1e17. So in raw units it ranks below a program that does not compile. Expected: a working solution outranks a compile failure. Observed under the original grader:

| Submission | Original grader output |
|---|---|
| `baseline`: the **shipped** baseline, unchanged | 50/50 OK, `TOTAL_SCORE 663100735542396309` (6.63e17) |
| `ce`: does not compile | `CASE 0000 CE`, `TOTAL_SCORE 100000000000000000` (1e17), `CASES_TOTAL 50` |
| `re_some`: baseline that aborts on 8 cases | 42/50 OK, `TOTAL_SCORE 1356919142089112260` (1.36e18) |

- **Upstream harness.** The compile-failure report is valid, with raw result 1e17 and score 0.0 out of 100. It is chosen over the shipped baseline and over `re_some` in every order tested. All of these score 0.0 out of 100.

**Why it does not change scores.** The score scale never rises as the raw result rises, and it equals 0 for any raw total at or above the baseline reference point (2.606e16). The compile-failure total of 1e17 is above that point. A compile failure can be chosen only when every other submission has a raw total of at least 1e17, and those submissions also score 0 out of 100. The problem affects only reporting in raw units and which submission is named "best".

**Note shipped with the task.** In the original grader a compile failure receives one 1e17 penalty in total, while each failed case receives 1e17. Under the upstream harness, a non-compiling submission can therefore be chosen as best by raw result over a working but poor one, including the shipped baseline. This never changes a score out of 100, because all such raw totals convert to zero.

## How much it matters

Largest score effect of the compile-failure rule: 0 points out of 100. Only solvers whose best working submission has a raw total of at least 1e17 can see a compile failure named as best by raw result, and they score 0 out of 100 either way.

The all-or-nothing effect of one failed case is a separate, undisclosed rule. It costs a submission its whole score when one case fails, for example by timing out on a slower grader; its size was not measured.

The task does not change; the note above ships with it.

## How we checked it

- **Original grader.** The original `eval_wirel.sh` ran in the original public image, pinned by digest, with `--network none`, on the three submissions above.
- **Harness grading.** The saved logs were graded with the real harness functions (`grade_output` → `rescale_score` → `select_best`). This used EdgeBench's harness at `6e4e5f4` (`sforge/`, hashes in `sforge/UPSTREAM.lock`).
- **Argument and random check.** A short argument from the score-scale and selection source code shows that a score out of 100 cannot change. It was checked on 200,000 random submission histories run through the upstream code, with a compile-failure submission inserted at every position. The result: **0** changes to the chosen score out of 100 and 0 changes to the maximum score out of 100, against 43,336 changes to the raw `best_score`.
- **Formal proof (Lean 4).** `evidence/formal/lean/ebv/Ebv/WirelessCeInvariance.lean` (output `WirelessCeInvariance.out`, `lean exit=0`, standard axioms only) proves `selected_norm_invariant`, `bestMax_invariant` and `task_ce_invariant`: inserting the compile-failure entry anywhere in a non-empty submission history changes neither the selected score out of 100 nor the maximum score out of 100. Scope: raw scores are rationals rather than floats, with no NaN or infinity; the empty history is not covered (with the compile failure alone the score is 0, `task_ce_only`). See `evidence/formal/notes/wireless_electricity_layout.md`.

## Limits

- No AI model or solver was run. Effects are shown only on test submissions we wrote.
- Three submissions were run. The shipped baseline is the only working test submission, and no competitive solution was run.
- The harness files in `sforge/` match EdgeBench's GitHub commit `6e4e5f4` byte for byte (`sforge/UPSTREAM.lock`, checked by `tools/check_upstream.py`), including `selection.py` abb55b7b…, `grading.py` ba15c46d… and `score_rescale.py` 98feb630….
- The choice of best submission was tested offline with the real harness functions, not through a live grader or agent run.
- The output of the 200,000-history check is not saved in this repository.
- How often this happened in past runs was not measured.
- The effect of the 5 s wall-clock limit on solvers near the limit, on graders with fewer or slower CPUs, was not measured.

## Reproduce

- Runs on the original image: `evidence/scripts/wireless_electricity_layout/run_judge.sh OUTDIR` (submissions in `subs/`; saved logs in `observed/`)
- Harness grading and choice of best submission: `evidence/scripts/wireless_electricity_layout/grade_and_select.py HARNESS_ROOT TASKS_DIR LOGDIR`
- Random property check: `evidence/scripts/wireless_electricity_layout/normalized_invariance.py`
- Pinned identity:
  - Grader image: `seededge/edgebench.judge.wireless_electricity_layout@sha256:78c341ca6e52849dfa7644f6664cbdbf87cd144cc72ff156c2508f5d623906d9`.
  - Task JSON: sha256 `050ab35f99431e94ee6279fcd23dc06c9a795ee7b9f26b7d9ec4eadb3e060809`.
  - `/tmp/eval_wirel.sh`: `c670ff6d7ac8a0042666c275b8bc947ddc93263f0b898fdab7078e208ce7dd8f`.
  - Shipped baseline `solution.cpp`: `811fe1e54452f935563de0480bd03a0b6270752efa7b45e01fba578116cb9256`.
  - `tools/bin/tester`: `a7d59fd3cc9796305d55d280b5ebe1455b80ae7df13425a47bde88433cd9cf87`.
