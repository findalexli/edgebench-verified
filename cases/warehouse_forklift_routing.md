# Warehouse Forklift Routing (`warehouse_forklift_routing`)

**Outcome:** Fixed. <mark>The grader gives 60 s per five-case input while the prompt promises 30 s per test case; the fixed version raises the limit to the promised 150 s per input, keeps the score scale unchanged and documents a proven ceiling of about 30.3 points out of 100.</mark>

![Time bar from 0 to 150 seconds per input showing the enforced 60 s limit, the promised 150 s, and the zone between marked as promised but scored 0; a test submission taking 13 s per test case (65 s per input) times out on all 50 inputs under the original grader and is fully scored by the fixed version with its 150 s limit.](figures/warehouse_forklift_routing.svg)

*The prompt promises 30 s per test case, 150 s per input, but the original grader enforces 60 s, so a solver that takes more than 60 s on any input, though within the promise, loses its whole score.*

## What the task asks

The task is an adaptation of the CodeChef problem WAREHOUS. The solver must output forklift command strings that store R·C−1 arriving goods on an R x C grid and then dispatch them in order. The goal is to "Minimize the total instruction string length". The prompt states "T=5 test cases per input" and "Time limit: 30 seconds per test case". The README says "Final score = sum of per-input average scores." Lower raw results are better. Category: Combinatorial Optimization.

## What goes wrong

### 1. The time limit is stricter than promised

**Rule.** The prompt promises 30 s per test case, with 5 test cases per input, which is 150 s per input. The grader sets `TIME_LIMIT = 60` for the whole input and runs 8 inputs in parallel. A timeout scores `inf`, and the harness rejects any CASE result that is not finite, so a single timeout invalidates the whole submission.

**Example, on the original grader.** A test submission with a time budget (it sleeps) spends 13 s per test case, less than half the promised limit. It gets 50 TLE (time limit exceeded) and an invalid submission. Expected from the prompt: all 50 inputs scored.

**Why it matters.** The local tools give no warning, because `tools/bin/tester` only scores an output file. A solver that follows the promised budget loses its whole score.

### 2. The reference points of the score scale cannot be reached

**Rule.** Every string the tester accepts satisfies S ≥ 2RC(R+C−1) − 6(R+C−2) − 2. So every valid per-case score is ≥ 20 − 6(R+C−2)/(R+C−1). On the 50 grading inputs every valid TOTAL is ≥ 198283458104808536/278277680055375 ≈ 712.538. That stays above the "rank1" reference point even after the rounding used for display.

**Example.** TOTAL ≥ 712.538 > rank1 395.80. The "super_anchor" reference point (293.51) is also below it. Under the task's own score scale, no valid submission can score above about 30.3 out of 100 (30.308 at the exact bound; 30.586 at 710.2, the lowest total possible after display rounding).

**Why it matters.** The 0–100 scale has a ceiling well below 100. The order of submissions is preserved.

### Checked and found not to change scores

- **A rule change that the prompt discloses.** The tester lets an empty forklift enter occupied cells. This is looser than the original CodeChef rule, but the prompt states it. Solvers that follow either rule are accepted.
- The diagonal construction scores exactly 20.0. Adding an E,W detour gives 20.2.
- The tester prints each input's score to 1 decimal place. This shifts TOTAL by at most 2.5 raw, or about 0.2 points out of 100.
- Failures add up to `inf` and invalidate the submission, which matches the README's "sum".
- Scoring is deterministic.
- The data are well-formed. Replaying generator seeds 0..300,000 reproduced none of the 50 grading files, so the grading inputs are not in the public seed range.

## How much it matters

- **Time limit:** a solver that takes 60–150 s on any input, within the promised budget, loses its whole score. Faster solvers are unaffected.
- **Ceiling:** every solver's score out of 100 is capped at about 30.3.

## The fix

The fixed version changes one line in `/tmp/eval_warehouse_manager.py`: `TIME_LIMIT = 60` becomes `TIME_LIMIT = 150`. The value is 30 s per test case × T=5, as the prompt promises. `eval_timeout` stays at 3600. The task JSON changes only `judge.image_tag`. The work image, prompt, README, tester, cases, parser, selection and score scale are unchanged.

The `piecewise_log_min` reference points are kept, not replaced. The proven floor is a lower bound, not a known optimum, so putting 100 there would be an invented recalibration. Keeping the reference points keeps scores comparable with the original version. The release notes state the ceiling of ≈30.3.

| Submission | Role | Original grader | Fixed grader |
| --- | --- | --- | --- |
| generic valid test submission | correct | OK 50/50, TOTAL 46676.8 | OK 50/50, TOTAL 46676.8 |
| one honest bug | invalid | 49 OK + 1 WA → inf | 49 OK + 1 WA → inf |
| shipped starter | invalid | 50 WA → inf | 50 WA → inf |
| **13 s per test case (uses the promised budget)** | **shows the problem** | **50 TLE → inf** | **50 OK, TOTAL 46676.8** |
| near the 150 s per-input limit | shows the problem | 50 TLE → inf | 50 OK, TOTAL 46676.8 |

(WA = wrong answer, TLE = time limit exceeded.)

**Are scores comparable?** Scores from the fixed version equal those from the original for every submission whose solver finishes each input within 60 s. The two are not comparable for a submission that takes 60–150 s on any input: the original invalidates the whole submission, while the fixed version scores it. A run near the limit can also change outcome with machine speed, as in any timed task. Because the reference points are unchanged, the 0–100 scale (including the ceiling of ≈30.3) is the same in both versions.

## How we checked it

- **Original grader, from the public image pinned by digest.** The verbatim `eval_cmd` ran in the grader image with `--network none` and the solution mounted read-only, and was graded by the repository's harness. Test submissions: a generic valid one, a repeat of it, the shipped starter, one with an honest bug, and solvers with a time budget. 16 hand-written outputs ran through the tester in the grader image with 0 mismatches against the oracle's predictions.
- **Independent oracle.** A simulator written from the statement text, with exact `Fraction` scoring and two rule modes (the prompt's rule and the stricter CodeChef rule). A differential test against the original tester program used 20,000 random command strings plus 2,000 outputs of the test submissions (half of them with one-character edits); all agreed. Exact optima for tiny grids came from Dijkstra's shortest-path search on 2x2, 2x3 and 3x2, under both rule sets. Data checks covered all 50 grading inputs (250 subcases) and generator seeds 0..300,000.
- **Formal check in Lean 4.** The per-case bound is the theorem `EbvWarehouse.lower_bound` in `formal/lean/ebv/Ebv/WarehouseBound.lean`. Lean's kernel checked it under Lean v4.34.1 and Mathlib `d13f23b7`, with no `sorry` and no `native_decide`, and it was recompiled independently. It depends only on Lean's standard axioms `[propext, Classical.choice, Quot.sound]`. `EbvWarehouse.score_bound` gives the per-case score bound. In `Ebv/WarehouseData.lean`, `totalLB_eq` and `totalLB_gt` give the bound on TOTAL, and `displayed_gt_rank1` covers display rounding. The theorem is not empty: the model accepts a 42-character optimum (`opt23_accepted`), and a stronger bound without the −6(R+C−2) term is proved false (`too_strong_bound_false`). That stronger bound fails on 239 of 248 optima found by brute force. The proof does not use the guard on moving into occupied cells, so it holds under both the prompt's rule and the CodeChef rule.
- **Repeatability.** The side-by-side run of the original and fixed graders was done three times, and no result changed (`data/paired-repeatability.md`).

## Limits

- No AI model or solver was run. Effects are shown only on the test submissions we wrote.
- The valid test submission is generic and weak (0.0 out of 100). No competitive solver was built. So the best score reachable between the floor (712.5 raw) and about 1000 raw (the diagonal construction) is not measured.
- The test submissions with a time budget use `sleep`. They show that the limit is enforced per input as promised. They do not model CPU contention from 8 compute-heavy inputs running in parallel, and `eval_cmd` sets no CPU allocation.
- The match between the Lean model and the tester is a line-by-line mapping done by hand, backed by a runtime differential test on 294 strings with 0 mismatches. It is not a kernel-checked proof. The case hypotheses (permutation, last arrival ≠ 1) and the extraction of (R,C) were checked in Python. The ceiling on the 0–100 scale comes from the harness's floating-point conversion code, not from Lean.
- The origin of the reference points is unknown.
- Scorer isolation is outside this release's scope (an EdgeBench design choice); findings that affect honest solvers are reported above.

## Reproduce

- Grader image: `sha256:ac7fdf03…`.
- Checks on the host: `evidence/scripts/warehouse_forklift_routing/` (`oracle_sim.py`, `diff_fuzz.py`, `authored_cases.py`, `data_and_bound.py`, `tiny_optimum.py`, `native/run_native.sh`, `harness_grade.py`; checksums in `SHA256SUMS`).
- Lean bound: `evidence/formal/lean/ebv/Ebv/Warehouse{Bound,Check,Data}.lean`, compiled with `evidence/scripts/warehouse_forklift_routing/lean_bound/compile_capped.sh`. Exact totals: `lean_bound/recompute_total.py`. Brute force: `lean_bound/brute_force.py`.
- Side-by-side run: `repairs/warehouse_forklift_routing-v2/paired/run.sh` (as run: `evidence/runs/warehouse_forklift_routing-v2-paired-b/run.sh`).
- Pinned identity: grader image `seededge/edgebench.judge.warehouse_forklift_routing@sha256:ac7fdf03…`; `/tmp/eval_warehouse_manager.py` sha256 `c5ff0c26…`; `tools/bin/tester` sha256 `277f4841…`; the 50 grading inputs (concatenated) sha256 `04b8cd29…`; task JSON sha256 `78002570…`.
- Supporting records: `repairs/warehouse_forklift_routing-v2/` (the folder holding the fixed version: README, `repair.patch`, `source-lock.json`), `evidence/reviews/warehouse_forklift_routing.md`, `evidence/reviews/warehouse_lower_bound_lean.md`.
