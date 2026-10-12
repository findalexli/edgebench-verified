# DCSS Dungeon Crawl Stone Soup AI (`dcss_dungeon_ai`)

Status: reviewed by the coordinator, 2026-10-12

- **Domain:** Interactive Games & Simulators
- **Decision:** Retain with note — the score matches the promise in normal runs; the note covers the
  all-five-morgues validity rule, wall-clock dependence and an unverified upper anchor.

## What the task promises

A Lua bot for DCSS 0.28 is scored on "5 hidden seeds, **900s game budget per game**, mean score
across all 5 games", with the games run in parallel and a forced quit at the deadline. The prompt
says `Pass rate` "is a validity check, not the quality metric", and admits that
"Wall-clock/PTTY scheduling can still create small score noise".

## What we checked and how

- Source reading of the pinned evaluator `eval_dcss.py` and of the harness validity gate and
  selection (`grading.py`, `selection.py`).
- Exact arithmetic on the evaluator's sleep schedule against `eval_timeout` 1100, and on the
  `log1p_max` rescale.
- Reuse of earlier accepted native runs: an idle bot (score 0, 962 s total) and one positive
  five-game run (games 2, 21, 18, 7, 14; mean 12.4). No game was rerun for this review.
- Original identity: judge image digest not recorded in the review; task JSON sha256
  `7d89425a7b6e072e3ff3b4faf4cd171b60946584c4dd33cabdad298af20a42a4`; `eval_dcss.py` sha256
  `101e8858…2218`.

## What we found

### Score definition and budget — consistent with the promise

Each game's score is the integer on morgue line 5 (zeroed if wizard or explore mode appears). The
aggregate is the mean of 5, rounded to 0.1, rescaled as `100*log1p(raw/400)/log1p(125)`. The code
matches the prompt: 5 seeds, `TIMEOUT=900`, 5 games in parallel, and the quit sequence.

| Raw mean score | Normalized |
|---|---|
| 0 (idle bot; accepted earlier) | 0 |
| 12.4 (accepted earlier five games: 2, 21, 18, 7, 14) | 0.63 |
| 400 | 14.3 |
| 5,000 | 53.8 |
| 20,000 | 81.3 |
| 50,000 | 100 |

The normal path takes at most about 948 s per game and the hard-timeout path at most about 1008 s,
both within `eval_timeout` 1100. The accepted idle run took 962 s in total.

### One missing morgue voids the submission — Confirmed from source, conditional (not observed)

The prompt describes the score as the mean of all 5 games. The evaluator emits
`"valid": ok == total`, and the harness gives no score to an invalid result.
- Example: if one game fails to write a morgue (the forced-quit sequence fails twice), expected
  under the prompt is a mean with that game counted as 0; observed under the original evaluator is
  no score for the whole submission.
- This path was not observed in the accepted runs. Best-of-N selection over submissions softens it.
- Maximum score effect observed: 0.

### Wall-clock and host-speed dependence — Confirmed from source, size unmeasured

The seeds are fixed, but the score is roughly turn rate × 900 s, and turn rate depends on the CPU
given to five concurrent game processes. No task-level CPU limit is set. The evaluator also sends
space, CR and Esc every 1.5 s of wall time during play, a timing-dependent input stream. The prompt
admits "small score noise", but its size has never been measured: there is one positive five-game
run and no repeat.

### Upper anchor — Unverified

Whether a raw mean of 50,000 is reachable in 900 s is unverified; no strong-bot run was found. The
shipped baseline sits at essentially 0.

## Note for users

No repair. The note says:
- A submission is valid only if all 5 games produce a morgue; one missing morgue voids the score.
- Scores depend on wall-clock speed and the CPU allocation; run-to-run noise is unmeasured.
- The 50,000 upper anchor has not been shown to be reachable.

## Limits and what was not run

- No model or solver re-runs. Effects are shown on authored controls and counterexamples only (here,
  the reused idle and positive runs).
- No game was run for this review.
- The missing-morgue path was reasoned from source; it was not triggered.
- The decisive noise check was not run: the same positive bot twice on one fixed allocation of at
  least 5 cores, and once on half that. If the spread is comparable to differences between bots,
  the decision would move to repair or withhold.

## Reproduce

- Review: `evidence/reviews/_game-tasks-correctness.md`, section 4.
- Pinned evaluator copy: the judge-image file `eval_dcss.py` (sha256 in [the review](../evidence/reviews/_game-tasks-correctness.md)).
- Harness gate and selection: `sforge/harness/grading.py`, `sforge/harness/selection.py`,
  `sforge/harness/score_rescale.py`.
