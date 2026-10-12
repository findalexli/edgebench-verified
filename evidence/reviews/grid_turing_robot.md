# Review: grid_turing_robot

Scope: good-faith correctness only (user decision, 2026-10-12). Score-line injection through submission-controlled text and other scorer-isolation questions are out of scope. I did not analyse, build or run any such submission.

## Claim under review

The earlier record (`$W/audit/evidence/grid-native-proposal/AUTHOR-CORRECTION.txt`, 2026-10-08) states:

- "The retained evaluator (SHA256 99c9c55d…) does not check that tester exit status. At lines26-32 it scans combined tester stdout/stderr for a line containing Score and an equals sign or colon, takes the suffix after the last selected separator, converts it through float to int, and returns case status OK."
- "The retained verifier (SHA256 49c99062…) … rejects directions outside U,D,L,R,S."
- "Current sforge/harness/score_rescale.py:155-158 maps nonpositive raw values to normalized0 for piecewise_min."
- "Even the raw1 case lies below the mathematical minimum valid C+Q=2."
- It retracts the dossier line saying the tester emits no Score marker on failure, calling it "too broad".

The dossier (`audit/dossiers/grid_turing_robot/dossier.txt`) adds: "A solution failure produces RE or TLE with infinity; no parsed tester score produces WA with infinity. The current score_sum parser and total-score reader reject such nonfinite output, so a malformed case should invalidate the aggregate under the current harness. This is source-derived behavior awaiting a grid-native check." It also notes that the 9,025,986 baseline anchor "must not be substituted" for the shipped baseline's actual sum, which was not measured.

Earlier disposition: TASKS.md says "Review pending | Historical source/component facts retained | Held". The card's disposition is `review/pending`. The task was held under "grid reflected score".

## Pinned artifacts

- Task: `tasks/grid_turing_robot.json`. eval_cmd `cd /home/workspace/grid_turing_robot && python3 /tmp/eval_grid_turing_robot.py`, parser `score_sum`, `minimize`, `score_first`, `piecewise_min` (baseline 9,025,986, rank30 4,490, rank1 1,575, super_anchor 554.75), eval_timeout 600 s. No `cpu_limit` or `mem_limit` is set.
- Judge image `seededge/edgebench.judge.grid_turing_robot@sha256:f67864ad75a3a2af0f7904a05a30b888f66ce2ed5c1f3cac7d7482e578a296c3`. I pulled it (about 412 MB) and ran it locally. File hashes inside the image:
  - `/tmp/eval_grid_turing_robot.py` `99c9c55d618f6bf989389948b3ce3836e4d0ed85d410de78273de76571e717d6`
  - `tools/bin/tester` `3928c31acf22b34a350be764423163d7bbe9a6257c9d749078b07ad63217ddad` (850 B)
  - `tools/src/verifier.py` `49c99062067d486e2a5466b2d057540bbbeac70de835ae39c0f6026db08039f3`
  - `tools/src/gen.py` `52105988f290ac3df03bbe2bedc538459004a8814e5e963749efe1d5ee0e8aed`
  - `tools/bin/gen` `ba846f6c…`
  - `README.md` `ada04c36…`
  - `solution.py` (shipped baseline) `9c42b54a…`
  - The 50 `cases/*` files: the sha256 of their sha256 list is `6dfe7079…`.
  - The images run Python 3.10.20.
- Work image `seededge/edgebench.work.grid_turing_robot@sha256:ba101c59f66f4423ff8a10be935d25513f459393b5afd74730e5bad87eaa66bd`. I pulled it to inspect only, then removed it. README, tester, verifier, gen and solution are byte-identical to the judge image. It has no `cases/`. `tools/README.md` (`adcba91c…`) exists only in the work image.
- Harness used for grading: the repo's `sforge/harness/` (`grading.py`, `log_parsers/score_sum.py`, `selection.py`, `score_rescale.py`).

## Contract

- agent_query: "Your solution is scored on **50 fixed test cases**. Final score = sum of individual case scores. **Lower is better.**" It also says: "Run your solution to completion and verify with the tester before finishing".
- README scoring: "If V = K: Score = C + Q … If V < K: Score = 2N^4 + (K − V) × N^2 (penalty)". It promises "Time limit | 30 seconds / test case" and "Memory limit | 512 MB". The output format requires directions in U/D/L/R/S, `1 ≤ C,Q ≤ N^4` and `0 ≤ M ≤ T`. It says "Each submission returns per-case scores and a total score."
- tools/README (work image): "Success: stderr outputs `Score = <integer>`, exit code 0. Failure: stderr outputs `wrong answer: <reason>`, exit code 1."
- Neither the prompt nor either README says what happens to a case that is malformed, crashes or times out. The penalty formula covers only well-formed outputs that do not visit every target.

## Independent reproduction

All scripts are under `evidence/scripts/grid_turing_robot/`.

**Independent oracle.** `oracle.py` was written from the README text and does not import `verifier.py`. It parses, simulates (start at target 0 in state 0, repaint, update state, then move unless there is a wall or the direction is `S`; only the current target counts; a missing rule halts) and scores.
- Differential test (`fuzz_agree.py`): 3,000 random rule tables on the 50 grading cases gave 0 disagreements with the original `Verifier`. All of them were partial routes, so the penalty branch is what was exercised.
- Full-route branch: the two implementations agree on all 50 cases for `good_stepstate`, giving sum 94,092. They also agree on the half-route `fail_partial` output for case 0000: 109,575, V=38/75, in both.

**Minimum cost (brute force).** `oracle.py brute` (`brute_out.txt`) exhaustively searched every initial colouring and every rule table, with halt allowed, for C+Q ≤ 5 on 1×3 and 2×2 boards. No (C,Q) combination was skipped. Results:

| instance | minimum C+Q |
|---|---|
| straight line | 2 |
| line with a return | 3 |
| 2×2 cycle | 4 |
| 2×2 zig-zag | 4 |

So C+Q = 2 is reached only when one repeated move visits every target. C ≥ 1 and Q ≥ 1 make C+Q ≥ 2 (sum ≥ 100 over 50 cases) a trivially correct lower bound. It is not tight for real cases.

**Data checks** (`oracle.py data`, `data_out.txt`). For all 50 cases:
- N is in 10..20 and K is in N..N².
- Wall strings are well formed and the grid is fully connected.
- Targets are distinct and in range.
- Independent BFS gives X in 180..6,667, and X ≤ T ≤ 2X holds (T/X ranges from 1.005 to 1.984).

**Seeds.** No grading case is byte-identical to `gen.py` output for any seed 0..60,000 (`seeds_header.py`, `seeds_header_out.txt`). There was one header-only coincidence (seed 12143 and case 0041), and the bodies differ. So the grading cases are not in the local seed range 0..10,000 permitted to solvers.

**Native runs.** Each solution was copied into the pinned judge image as `solution.py`, and the unchanged evaluator was run with `docker run --network none --memory 2g --cpus 4` (`run_native.sh`). The logs were then graded by the repo harness: `grade_output` → `rescale_score` → `select_best` (`grade.py`, `native/grade_out.txt`).

| solution (all honest) | evaluator per-case result | TOTAL_SCORE | harness valid | raw | normalized |
|---|---|---|---|---|---|
| `good_stepstate` (C=1, one state per BFS step; known-good) | 50 OK | 94,092 | yes | 94,092 | 19.80 |
| `fail_partial` (well-formed; route cut in half on case 0000) | 50 OK | 202,310 | yes | 202,310 | 19.56 |
| `shipped_baseline` (`1 1 0`, no rules; known-bad, valid) | 50 OK | 7,744,909 | yes | 7,744,909 | **2.84** |
| `fail_crash` (raises on case 0000 only) | 0000 RE score=inf | inf | **no** ("Malformed or nonfinite CASE record") | None | None |
| `fail_trunc` (output cut short on case 0000) | 0000 WA score=inf | inf | no | None | None |
| `fail_tle` (sleeps 40 s on case 0000) | 0000 TLE score=inf | inf | no | None | None |
| `fail_lower` (lower-case directions on every case) | 50 WA score=inf | inf | no | None | None |

The tester's own output on case 0000 (`native/tester_case0000.txt`):
- `wrong answer: Invalid direction: d` (exit 1)
- `wrong answer: Output format error: list index out of range` (exit 1)
- `Score = 1357` and `Score = 109575` (exit 0)

Honest error texts contain no "Score" token, so they land in WA, which is what the evaluator intends.

Selection across rounds: when all the logs are passed as rounds, `score_first` picks the valid 94,092 round and ignores the invalid ones.

**CPU dependence.** `cpu12` does a fixed 12 s of CPU work per case (under the README's 30 s), then emits the good answer. I ran it through the same evaluator twice:
- `--cpus 8`: 50 OK, raw 94,092, normalized 19.80.
- `--cpus 2`: **48 TLE**, which makes the submission invalid.

The evaluator always runs 8 cases in parallel against a 30 s wall-clock limit, and the task sets no `cpu_limit`. Results are in `native_cpus2/`, `native_cpus8/` and `native_cpus8/grade_out.txt`.

## Refutation attempts

1. **Reflected score line.** This is a submission-text-injection path, so it is a scorer-isolation question and out of scope. I built no fixture for it. For honest submissions, the earlier source reading is right: the evaluator ignores the tester's exit status and scans for a "Score" line with `=`/`:`. That changes no honest outcome, because the tester prints a Score line only on success, and honest `wrong answer:` texts contain no "Score" token (shown natively above).
2. **Do failures help a minimiser?** No. RE, TLE and WA cases get `score=inf` in the evaluator. The harness parser's NUMBER pattern does not accept `inf`, so `grade_output` invalidates the whole submission (score None, pass_rate 0, no rankable result). A failed case is never dropped and never counted as 0. Even if the infinite sum were passed through, `piecewise_min` would give 0 for raw ≥ baseline. No honest failure can score better than a valid run. The dossier's source prediction, "a malformed case should invalidate the aggregate", is **confirmed natively**.
3. **Is the failure rule consistent with the prompt?** It is stricter than the prompt implies but does not contradict it. The prompt promises a "sum of individual case scores" and per-case scores, and its penalty formula covers only well-formed outputs that do not visit every target. In practice, one honest crash, timeout or format slip in 50 cases makes the whole submission unrankable. If that case were charged even its smallest penalty instead (2N⁴+(K−1)N² ≥ 20,900), the total would exceed rank30 = 4,490, so the submission would earn at most about 19.96 points. The cost of invalidation over a per-case penalty is therefore at most about 20 normalized points for that submission. It is zero if an earlier round was valid, because `score_first` keeps the best valid round.
4. **Baseline anchor.** The shipped baseline actually totals 7,744,909 on the 50 grading cases. By the penalty formula, every case is 2N⁴+(K−1)N², because the robot starts on target 0 and halts at once. That total is not the configured 9,025,986. The configured value matches none of the alternatives I tried:
   - V=0 penalty: 7,756,665
   - generator seeds 0–49: 9,049,202
   - seeds 1–50: 9,098,133

   As a result the do-nothing baseline scores 2.84 points instead of 0. Every score between baseline and rank30 is shifted by at most 2.84 points.
5. **Anchors.** `super_anchor` = rank1 − 0.35·(rank30 − rank1) = 1575 − 1020.25 = 554.75. This is the same 0.35 extrapolation used by apple_incremental_game and molecular_self_assembly, so it is a convention, not a measurement. 554.75 (about 11 per case) is above the hard floor of 100 (2 per case), so it is not impossible. I could not trace where rank1 = 1,575 and rank30 = 4,490 came from. AHC056 ranked by relative scores on different cases, so these totals cannot be official leaderboard values for these 50 cases.
6. **README "Only output rules for pairs that actually occur".** The verifier does not enforce this, and unused rules do not change the score (cost is C+Q, not M). This is harmless documentation overstatement.
7. **The prompt points to `tools/README.md`.** It exists in the work image the solver sees. It is missing from the judge image, which does not matter for scoring.
8. **Memory limit.** The README promises 512 MB, but the evaluator does not enforce it. That is lenient and cannot hurt an honest solver.

## Formal check

None. The state rules are short and deterministic. The independent oracle, the 3,000-table differential test and the exhaustive tiny-board search cover them directly, so a TLA+ model would not resolve any open question.

## Verdict

**CONFIRMED-NARROWER.**

- The source facts quoted from AUTHOR-CORRECTION are accurate: the tester's exit status is ignored, Score lines are scanned for, non-U/D/L/R/S directions are rejected, nonpositive raw maps to 0, and C+Q ≥ 2.
- The dossier's prediction that a malformed case invalidates the whole aggregate is confirmed natively.
- For honest solvers, the "reflected score" concern has no effect. The injection path itself is out of scope.

For honest solvers, the task scores correctly. The oracle and verifier agree, the data is valid, and failures never help. Three things need a note:

- **(a)** One failed case makes the whole submission unrankable, and the prompt does not say so.
- **(b)** The configured baseline is not the shipped baseline's score, which gives a 2.84-point floor offset.
- **(c)** The 30 s limit is wall-clock time shared by 8 parallel cases, with no pinned judge CPU allocation. A fixed-work solution valid on 8 CPUs was invalidated on 2.

## Disposition assessment

**Retain with a note.** The "grid reflected score" hold concerned an out-of-scope isolation path and should not block the task. Withholding it would be disproportionate: no good-faith defect inverts rankings or accepts incorrect solutions.

Run condition: grade with at least 8 dedicated judge CPUs, as in my 8-CPU run, or equivalently with evaluator parallelism no greater than the CPUs available. Otherwise, timeout results depend on the host.

Maximum score effect:
- Point (a): at most about 20 points per affected submission, and 0 if an earlier round was valid.
- Point (b): at most 2.84 points, only in the 0–20 band.
- Point (c): up to the full score (about 100 points) for fixed-work solutions on a judge with fewer than about 8 CPUs. Solvers that budget by wall-clock time stay valid but get less compute. This is an execution-environment condition, not a defect in the task's rules.

## Recommended publishable wording

"Scoring was reproduced in the original judge image with an independent simulator. Results matched and the 50 cases are valid. One crashed, timed-out or malformed case makes the whole submission unrankable, which the prompt does not say; the configured baseline (9,025,986) is higher than the shipped baseline's actual 7,744,909, so the shipped baseline earns 2.8 points instead of 0. Cases run eight at a time under a 30-second wall-clock limit, so results are reproducible only with at least 8 judge CPUs."

## Repair note

No earlier repair was proposed for these points. The smallest fixes, if a v2 is wanted, are:

1. Pin judge `cpu_limit` ≥ 8, or set `max_workers` to the available CPU count.
2. Either document that any failed case voids the submission, or have the evaluator emit a finite per-case penalty for RE/TLE/WA. One option is 2N⁴+K·N², the V=0 penalty, which is always worse than any well-formed output.
3. Set the rescale baseline to 7,744,909, the measured shipped-baseline total.

None of these is needed to retain the original with a note.

## Limits

- Native runs used local Docker with `--cpus 4` (main table), `--cpus 2` and `--cpus 8`, and `--memory 2g`. The production judge's CPU allocation is unknown.
- I tested only simple honest solutions. I did not build a strong solution, so whether rank1 = 1,575 is achievable is not checked, and the anchor lineage is not traced.
- The seed search covered gen.py seeds 0..60,000 with exact byte matching. I did not try other generator revisions or the official AHC056 generator.
- The differential test's random tables produced only partial routes. Full-route agreement rests on the 50 `good_stepstate` cases plus the `fail_partial` case.
- Scorer isolation and injection are out of scope by decision and were not analysed.
