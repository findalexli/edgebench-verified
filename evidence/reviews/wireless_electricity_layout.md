# Review: `wireless_electricity_layout`

Reviewer: Claude (critical re-verification), 2026-10-11. Local Docker only, no cloud, no credentials.

## Claim under review

> "Raw scoring ranks an observed compilation failure above a feasible solution. All three normalized scores were zero; no leaderboard gain was shown."

Earlier disposition: **withhold original** (`evidence/selected/wireless-original-exclusion.json`). The card rationale adds: "intact original raw score_first/minimize history therefore marks the compile failure best, and the pinned original final-result consumer persists that raw selection."

## Pinned artifacts

| Item | Identity |
|---|---|
| Task JSON `tasks/wireless_electricity_layout.json` | `050ab35f99431e94ee6279fcd23dc06c9a795ee7b9f26b7d9ec4eadb3e060809` |
| Judge image | `seededge/edgebench.judge.wireless_electricity_layout@sha256:78c341ca6e52849dfa7644f6664cbdbf87cd144cc72ff156c2508f5d623906d9` (pulled, executed) |
| `/tmp/eval_wirel.sh` (in image) | `c670ff6d7ac8a0042666c275b8bc947ddc93263f0b898fdab7078e208ce7dd8f` |
| Shipped baseline `solution.cpp` | `811fe1e54452f935563de0480bd03a0b6270752efa7b45e01fba578116cb9256` |
| `tools/bin/tester` | `a7d59fd3cc9796305d55d280b5ebe1455b80ae7df13425a47bde88433cd9cf87`; 50 files in `cases/` |
| Upstream harness `6e4e5f4` (copied from `$W/work/edgebench-source`) | `selection.py abb55b7b...`, `grading.py ba15c46d...`, `score_sum.py 49b19e22...`, `score_rescale.py 98feb630...`; hashes match `upstream-lock.json` |
| Maintained harness (this repo) | `selection.py 3338ed24...`, `grading.py b3eeac72...`, `score_rescale.py 98feb630...` (same as upstream) |

## Contract

Prompt: "Your solution is scored on **50 fixed hidden test cases**. Final score = sum of (P+Q) across all hidden cases. **Lower is better.**" and "A valid baseline `solution.cpp` already exists. Improve it." Judge: `parser: score_sum`, `score_direction: minimize`, `selection: score_first`, `rescale: piecewise_log_min` with baseline 2.606e16, rank30 2.445e15, rank1 3.624e14, super_anchor 1.812e14. The prompt says nothing about failure penalties.

`eval_wirel.sh` handles failures this way:
- Missing file or compile failure: emits **one** line `CASE 0000 CE score=1e17`, then `TOTAL_SCORE 1e17`, `CASES_OK 0`, `CASES_TOTAL 50`.
- Any per-case TLE, RE or WA: adds `1e17` **per case**.

A compile failure therefore costs 1e17 in total, while one feasible run on 50 cases costs about 50 × 1.3e16 for the shipped baseline.

## Independent reproduction

Scripts are in `evidence/scripts/wireless_electricity_layout/`:
- `run_judge.sh OUTDIR` runs the original `eval_wirel.sh` in the pulled image (`--network none --memory 2g --cpus 2`) for each `subs/*/solution.cpp`.
- `grade_and_select.py HARNESS_ROOT TASKS_DIR LOGDIR` runs the real `grade_output` → `rescale_score` → `select_best`.
- `normalized_invariance.py` is a randomized property check.

Saved logs are in `observed/`.

| Submission | Original evaluator output |
|---|---|
| `baseline`: the **shipped** baseline, unchanged | 50/50 OK, `TOTAL_SCORE 663100735542396309` (6.63e17) |
| `ce`: does not compile | `CASE 0000 CE`, `TOTAL_SCORE 100000000000000000` (1e17), `CASES_TOTAL 50` |
| `re_some`: baseline that aborts on 8 cases | 42/50 OK, `TOTAL_SCORE 1356919142089112260` (1.36e18) |

Harness composition:

```
UPSTREAM 6e4e5f4:   ce valid=True raw=1e17 norm=0.0 ; baseline raw=6.63e17 norm=0.0 ; re_some raw=1.36e18 norm=0.0
  [baseline, ce] -> selected ce   ; [ce, baseline] -> ce ; [re_some, ce] -> ce ; [baseline, re_some, ce] -> ce   (all norm 0.0)
MAINTAINED (repo):  ce valid=False ("CASES_TOTAL disagrees with CASE records"), unrankable
  [baseline, ce] -> baseline ; [ce, baseline] -> baseline ; [re_some, ce] -> re_some   (all norm 0.0)
```

`normalized_invariance.py` (upstream code) ran 200,000 random histories, inserting a CE entry at every position. It found **0** changes to the normalized score of the selected entry and 0 changes to the max normalized score, against 43,336 changes to raw `best_score`.

## Refutation attempts / questions asked

1. **Does a compile failure actually win selection in the real harness?** Under **upstream** `6e4e5f4`, yes. `parse_score_sum` accepts the single CE line, `extract_score` takes `TOTAL_SCORE 1e17`, `valid=True`, and `score_first`/minimize picks it over any history whose other entries all have raw > 1e17. This includes the unmodified **shipped feasible baseline**, which is a stronger and less contrived witness than the earlier "parked control". Under the **maintained** harness, no. Its `score_sum` parser checks the declared `CASES_TOTAL 50` against the single CASE record and invalidates the report, so `_completed_submissions` drops it.
2. **Can the defect ever change a normalized final score?** No. Proof: `piecewise_log_min` is non-increasing and equals 0 for raw ≥ baseline (2.606e16), and the CE raw value is 1e17 > baseline, so f(CE) = 0. Under `score_first`/minimize, CE is selected only if every other scored entry has raw ≥ 1e17, and then each of those entries also has f = 0. So the selected normalized score is 0 with or without the CE entry. The order-independent `max(score_0_100)` consumer gains only another 0. The randomized check above agrees.
3. **Strongest concrete case for a changed report:** a run whose only feasible submissions are worse than about 2e15 per case, such as the shipped baseline, plus one non-compiling submission. Upstream then reports raw `best_score = 1e17` with `best_round` pointing at a program that does not compile. The 0.0 normalized score is unchanged. This affects only raw-unit reporting and the identity of the "best" submission.
4. **Is the trigger contrived?** Compile failures are ordinary agent outcomes, and the shipped baseline already loses to one, so the trigger is reachable. A competent solution (≤ 2e15 per case) always beats CE. Any raw total below 1e17 beats CE.

## Formal check

No Lean/TLA+. The monotonicity argument above is short and complete given the source, and I backed it with the executed property check using the real upstream `rescale_score` and `select_best`.

## Verdict

**CONFIRMED-NARROWER.** The raw-ranking inversion is real under the upstream harness, and it reproduces with the shipped baseline. It cannot change any normalized score. The maintained harness does not exhibit it at all, because it rejects the CE report as inconsistent with `CASES_TOTAL`.

## Disposition assessment

I **disagree** that withholding the original is proportionate on this finding alone. The defect is confined to raw `best_score`/`best_round` under the upstream harness. It provably never changes a normalized score, and it is neutralized under the maintained harness that EdgeBench Verified uses for retained tasks. A note is the better disposition: "retain-eligible with a note", subject to the other review gates. If the team wants the evaluator's own output to be correct independent of harness, the alternative is a tiny repair. The card's phrase "material failure-aggregation/verifier mismatch" overstates the impact on scores.

## Recommended publishable wording

"In the original evaluator, a compile failure receives one 1e17 penalty in total, while each failed case receives 1e17, so under the upstream harness a non-compiling submission can be selected as raw-best over a feasible but poor one (including the shipped baseline). This never changes a normalized score, because all such raw totals normalize to zero, and the maintained harness rejects the inconsistent compile-failure report."

## Repair note

No repair is needed under the maintained harness. Smallest evaluator-level fix: in both CE branches of `eval_wirel.sh`, emit one `CASE <id> CE score=$BAD_SCORE` line per case file and `TOTAL_SCORE $((BAD_SCORE*CASES_TOTAL))`. That stays within bash 64-bit range (5e18 < 9.22e18) and makes CE equal to "every case failed". I could not inspect a specific earlier proposed patch for this task.

## Limits

- Three submissions. The shipped baseline is the only feasible control, and no competitive solution was run (none is needed for the argument).
- The upstream harness was taken from the canonical workspace copy, with hashes verified against the lock, rather than re-fetched from GitHub.
- Selection was exercised offline with real harness functions, not through a live `judge_server`/`run_agent` run.
- Historical incidence was not measured.
