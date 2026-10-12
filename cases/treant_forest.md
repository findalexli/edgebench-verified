# Treant's Forest (`treant_forest`)

**Outcome:** Fixed. <mark>The original score scale puts its reference points above the most turns the grader allows, so no submission can score above 21.02/100; the fixed version changes only the score scale.</mark>

![Number line of the original 0 to 100 score scale, where everything above 21.02, the score of the maximum possible 92,304 turns, is unreachable, compared with a fixed scale running from 3,418 to 92,304.](figures/treant_forest.svg)

*The original scale's reference points lie above the maximum possible raw score, so the best possible submission scores only 21.02 of 100; the fixed scale ends at 92,304.*

## What the task asks

The task is a grid puzzle adapted from the AtCoder contest AHC054: "Your solution is scored on **50 fixed test cases**. Final score = sum of individual case scores. **Higher is better.**" Raw results (before conversion to 0–100) are converted to a 0-100 scale. Category: Combinatorial Optimization.

## What goes wrong

**Rule.** Each case's raw result is its turn count, and the grader's tester program caps turns at `max_turns = N*N*2`, where N is the grid size (tester:63, loop at :140). The README does not mention this cap. The original score scale is `piecewise_max` with four reference points: baseline 5,369, rank30 88,189, rank1 330,195 and super 451,198.

**Example.** The sum of 2N² over the 50 shipped cases is **92,304**, the largest raw result anyone can reach. A perfect submission at that cap should score 100. Under the original score scale it gets **21.02/100** (exactly 2543510/121003).

**Why it matters.** The rank1 reference point (330,195) is **3.58×** the reachable maximum. So every score above 21.02 out of 100 (nearly all of the 20-80 band and the whole 80-100 band) is out of reach for any submission. The order of submissions is preserved. The origin of the original reference points is unknown; they appear to come from a different scorer or set of cases.

**Checked and fine.** The worst-case runtime is 7 waves × 120 s = 840 s, under the 870 s limit (tight). The tester is deterministic. Solutions that use a wall-clock time budget depend on the CPU available to the 8 parallel workers.

## How much it matters

All solvers are affected: every score out of 100 is squeezed into 0–21. The baseline solution that ships with the task (TOTAL_SCORE **3,418**, 50/50 cases OK) maps to 0.

## The fix

Only `judge.rescale` (the score scale) in the task JSON changes. The `piecewise_max` reference points are replaced by `"kind": "linear", "lower": 3418.0, "upper": 92304.0`. The lower point is the shipped baseline's raw result under the original grader. The upper point is Σ 2N² over the shipped cases, the exact maximum of the tester's score function. The four old reference-point fields are removed: two lie above the cap, and no exact replacements for the rank-based points exist. The grader image, grader, tester, cases, `eval_cmd` and timeouts are unchanged, so raw results are byte-identical.

| Submission | Image | Raw result (`TOTAL_SCORE`) | Cases OK | Grader exit code | Score out of 100, original scale | Score out of 100, fixed scale |
| --- | --- | ---: | --- | --- | ---: | ---: |
| Shipped baseline (`0`, `-1`) | original | 3418 | 50/50 OK | 0 | 0.00 | 0.00 |
| Shipped baseline | fixed | 3418 | 50/50 OK | 0 | 0.00 | 0.00 |
| Honest greedy (lengthens the maze on the grid only) | original | 17960 | 50/50 OK | 0 | 3.04 | 16.36 |
| Honest greedy | fixed | 17960 | 50/50 OK | 0 | 3.04 | 16.36 |
| Invalid: treant on the revealed entrance | original | 0 | 0/50 (all WA) | 0 | 0.00 | 0.00 |
| Invalid: treant on the revealed entrance | fixed | 0 | 0/50 (all WA) | 0 | 0.00 | 0.00 |

(WA = wrong answer.)

End points of the scale, computed with `score_rescale.py` rather than by running a submission:

| Raw result | Original scale | Fixed scale | Fixed scale, exact |
| ---: | ---: | ---: | --- |
| 0 | 0.00 | 0.00 | 0 |
| 3418 (shipped baseline) | 0.00 | 0.00 | 0 |
| 5369 (old `baseline` field of the original version) | 0.00 | 2.19 | 97550/44443 |
| 92304 (= Σ 2N², the score cap) | **21.02** | **100.00** | 100 |
| 330195 (old rank1, exceeds the cap) | 80.00 | 100.00 | 100 |

Raw results were identical in the original and fixed images. Only the score out of 100 changes, and only because of the new score scale.

**Are scores comparable?** Scores out of 100 from the fixed version are not comparable with those from the original for any raw result above the shipped baseline (raw > 3418). Raw `TOTAL_SCORE` values stay comparable across versions. The rank-based reference points no longer exist, so a score of 20 or 80 in the fixed version has no meaning as a leaderboard percentile.

## How we checked it

- **Original grader, from the public image pinned by digest.** The original `eval_cmd` ran in the original grader image and in the fixed image, with `--network none`. The hashes of the grader, tester and cases inside each image matched the pinned values.
- **Exact arithmetic.** The per-case cap 2N² was summed over the 50 shipped case headers by two independent scripts. Its value under the original score scale was computed exactly.
- **Source reading.** The cap is read directly from the tester source (`tools/bin/tester`).
- **Repeatability.** The side-by-side run of the original and fixed versions was done three times, and no result changed (`data/paired-repeatability.md`).

## Limits

- No AI model or solver was run. Effects are shown only on the test submissions we wrote.
- 92,304 is the exact upper bound on the raw result. Reaching it on every case has not been demonstrated. The best honest result on a single case reached 47% of that case's cap (the per-case caps for that run are not saved here).
- A linear scale from the baseline to the cap squeezes realistic strong scores together. That cost comes from using only exactly computable reference points instead of ones taken from a leaderboard.
- The 2N² cap is still not disclosed in the README. Disclosing it would be a separate change to what the solver sees.
- Whether the tester's movement rules match the original AHC054 game was not established, and this fix does not address it.

## Reproduce

- Cap arithmetic: `python3 evidence/scripts/_game-tasks-correctness/check_arith.py <treant cases dir>` (saved output: `evidence/scripts/_game-tasks-correctness/check_arith.out.json`).
- Original baseline run: `bash evidence/scripts/_game-tasks-correctness/run_treant_baseline.sh <cases_dir> <shipped_solution.py> <orig_eval_treants_forest.py>`.
- Side-by-side run: `repairs/treant_forest-v2/paired/run.sh`, conversion to 0–100 with `repairs/treant_forest-v2/paired/normalize.py` (`repairs/treant_forest-v2/` is the folder holding the fixed version).
- Pinned identity: grader image `seededge/edgebench.judge.treant_forest@sha256:783e9ca2…` (`sha256:783e9ca2…`, the original version); task JSON sha256 `2fdb98ce1166a1fea4743c2ae1613479bdf9eaf755cab190bfd931bc547a615e`; `eval_treants_forest.py` sha256 `ce2833ac…2048`; `tools/bin/tester` sha256 `6cbb3a72…8551`; 50 cases (sha256 of the sorted listing) `bc256294…`.
- Supporting records: `repairs/treant_forest-v2/` (`README.md`, `repair.patch`, `source-lock.json`, `paired/results.md`).
