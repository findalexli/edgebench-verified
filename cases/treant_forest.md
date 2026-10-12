# Treant's Forest (`treant_forest`)

**Decision:** Repair (v2). The original rescale anchors lie above the tester's turn cap, so no submission can score above 21.02/100; v2 changes only the anchors.

## What the task asks for

An AHC054 adaptation: "Your solution is scored on **50 fixed test cases**. Final score = sum of individual case scores. **Higher is better.**" Raw scores are normalized to a 0-100 scale. Category: Combinatorial Optimization.

## What goes wrong

**Rule.** Each case's score is the turn count, and the tester caps turns at `max_turns = N*N*2` (tester:63, loop at :140). The README does not mention this cap. The original rescale is `piecewise_max` with baseline 5,369, rank30 88,189, rank1 330,195 and super 451,198.

**Example.** The sum of 2N² over the 50 shipped cases is **92,304**, the maximum attainable raw score. A perfect submission at that cap is expected to score 100. Under the original rescale it maps to **21.02/100** (exactly 2543510/121003).

**Why it matters.** rank1 (330,195) is **3.58×** the attainable maximum, so every normalized score above 21.02 (nearly all of the 20-80 band and the whole 80-100 band) is unreachable by any submission. Ordering is preserved. The origin of the original anchors is unknown; they appear to come from a different scorer or case set.

**Checked and fine.** Worst-case runtime is 7 waves × 120 s = 840 s, under 870 s (tight). The tester is deterministic; solutions that use a wall-clock budget depend on the CPU available to the 8 parallel workers.

## Impact

All solvers are affected: every normalized score is compressed into 0–21. The shipped baseline (TOTAL_SCORE **3,418**, 50/50 cases OK) maps to 0.

## Fix (v2)

Only `judge.rescale` in the task JSON changes. The `piecewise_max` anchors are replaced by `"kind": "linear", "lower": 3418.0, "upper": 92304.0`. The lower anchor is the shipped baseline's score under the original judge; the upper anchor is Σ 2N² over the shipped cases, the exact maximum of the tester's score function. The four old anchor fields are removed, because two lie above the cap and no exact replacement rank anchors exist. The judge image, evaluator, tester, cases, `eval_cmd` and timeouts are unchanged, so raw scores are byte-identical.

| Submission | Image | Raw TOTAL_SCORE | Cases OK | Eval exit | v1 normalized | v2 normalized |
| --- | --- | ---: | --- | --- | ---: | ---: |
| Shipped baseline (`0`, `-1`) | v1 | 3418 | 50/50 OK | 0 | 0.00 | 0.00 |
| Shipped baseline | v2 | 3418 | 50/50 OK | 0 | 0.00 | 0.00 |
| Honest greedy (grid-only maze lengthening) | v1 | 17960 | 50/50 OK | 0 | 3.04 | 16.36 |
| Honest greedy | v2 | 17960 | 50/50 OK | 0 | 3.04 | 16.36 |
| Invalid: treant on the revealed entrance | v1 | 0 | 0/50 (all WA) | 0 | 0.00 | 0.00 |
| Invalid: treant on the revealed entrance | v2 | 0 | 0/50 (all WA) | 0 | 0.00 | 0.00 |

Anchor endpoints, computed with `score_rescale.py` rather than by running a submission:

| Raw | v1 | v2 | Exact v2 |
| ---: | ---: | ---: | --- |
| 0 | 0.00 | 0.00 | 0 |
| 3418 (shipped baseline) | 0.00 | 0.00 | 0 |
| 5369 (old v1 `baseline` field) | 0.00 | 2.19 | 97550/44443 |
| 92304 (= Σ 2N², the score cap) | **21.02** | **100.00** | 100 |
| 330195 (old rank1, exceeds the cap) | 80.00 | 100.00 | 100 |

Raw scores were identical in the v1 and v2 images; only the normalized value changes, and only because of the new anchors.

**Score compatibility.** v2 normalized scores are not comparable with v1 normalized scores for any raw score above the shipped baseline (raw > 3418). Raw `TOTAL_SCORE` values stay comparable across versions. The rank anchors no longer exist, so a v2 score of 20 or 80 has no leaderboard-percentile meaning.

## How we know

- **Original evaluator in the pinned image.** The original `eval_cmd` ran in the original judge image (`sha256:783e9ca2…`, v1) and in the v2 image, with `--network none`. In-image hashes of the evaluator, tester and cases matched the pinned values in both images.
- **Exact arithmetic.** The per-case cap 2N² was summed over the 50 shipped case headers by two independent scripts, and its normalized value under the original anchors was computed exactly.
- **Source reading.** The cap is read directly from the tester source (`tools/bin/tester`).
- **Repeatability.** The paired evaluation was run three times; no verdict changed (`paired-repeatability.md`).

## Limits

- No model or solver was run. Effects are shown on authored controls only.
- 92,304 is the exact upper bound on the score. Reaching it on every case has not been demonstrated; the best honest per-case result reached 47% of that case's cap (the per-case caps for that run are not saved here).
- A linear scale from baseline to cap compresses realistic strong scores; that cost comes from using only exact anchors instead of leaderboard-derived ones.
- The 2N² cap is still not disclosed in the README; disclosing it would be a separate solver-visible change.
- Whether the tester's movement rules match the original AHC054 game was not established, and this repair does not address it.

## Reproduce

- Cap arithmetic: `python3 evidence/scripts/_game-tasks-correctness/check_arith.py <treant cases dir>` (saved output: `evidence/scripts/_game-tasks-correctness/check_arith.out.json`).
- Original baseline control: `bash evidence/scripts/_game-tasks-correctness/run_treant_baseline.sh <cases_dir> <shipped_solution.py> <orig_eval_treants_forest.py>`.
- Paired evaluation: `repairs/treant_forest-v2/paired/run.sh`, normalization `repairs/treant_forest-v2/paired/normalize.py`.
- Pinned identity: judge image `seededge/edgebench.judge.treant_forest@sha256:783e9ca2…`; task JSON sha256 `2fdb98ce1166a1fea4743c2ae1613479bdf9eaf755cab190bfd931bc547a615e`; `eval_treants_forest.py` sha256 `ce2833ac…2048`; `tools/bin/tester` sha256 `6cbb3a72…8551`; 50 cases (sha256 of the sorted listing) `bc256294…`.
- Supporting records: `repairs/treant_forest-v2/` (`README.md`, `repair.patch`, `source-lock.json`, `paired/results.md`).
