# DCSS Dungeon Crawl Stone Soup AI (`dcss_dungeon_ai`)

**Outcome:** Kept, with a note. <mark>In normal runs the score matches what the task promises; a game without an end-of-game record counts as 0, as the task implies; the note covers the dependence on wall-clock speed and an unchecked top reference point.</mark>

## What the task asks

The solver writes a bot in Lua (a scripting language) for DCSS 0.28, the dungeon game Dungeon Crawl Stone Soup. The bot is scored on "5 hidden seeds, **900s game budget per game**, mean score across all 5 games". The games run in parallel, and the grader forces a quit at the deadline. The prompt says `Pass rate` "is a validity check, not the quality metric", and admits that "Wall-clock/PTTY scheduling can still create small score noise". Category: Interactive Games & Simulators.

## What we checked

There is no problem in normal runs. Checked and found correct: each game's score is the integer on line 5 of its morgue file (the game's end-of-game record). If wizard or explore mode appears in the morgue, the game is treated like a game without a morgue (`eval_dcss.py:84-85`, `:164-166`): it scores 0 and the grader marks the submission `valid: false`, which EdgeBench's selection does not read (see the first note). The total is the mean of the 5 games, rounded to 0.1. It is converted to a 0–100 score as `100*log1p(raw/400)/log1p(125)`. The code matches the prompt: 5 seeds, `TIMEOUT=900`, 5 games in parallel, and the quit sequence.

| Raw mean score (before conversion to 0–100) | Score out of 100 |
|---|---|
| 0 (idle bot) | 0 |
| 12.4 (five games: 2, 21, 18, 7, 14) | 0.63 |
| 400 | 14.3 |
| 5,000 | 53.8 |
| 20,000 | 81.3 |
| 50,000 | 100 |

The normal path takes at most about 948 s per game. The path with a hard timeout takes at most about 1008 s. Both are within the grader's time limit, `eval_timeout` 1100.

Notes:

- **A game without a morgue counts as 0, as the prompt implies (no defect).** The prompt describes the score as the mean of all 5 games. A game that writes no morgue (for example, the forced-quit sequence fails twice) scores 0, and the grader emits the mean of all 5 games as the score, together with `"valid": ok == total` (`eval_dcss.py:210-221`). EdgeBench's harness keeps that score: `_grade_structured` copies it, and the task's `score_first` selection does not read `valid` (`sforge/harness/grading.py:200-217`, `sforge/harness/selection.py:83-103` at EdgeBench `6e4e5f4`). A game in wizard or explore mode is handled the same way. This follows from the source, with the grader's output format fed through the harness offline; the path was not observed in a real run.
- **Dependence on wall-clock and host speed.** The seeds are fixed, but the score is roughly turn rate × 900 s. The turn rate depends on the CPU given to five game processes running at once. The task JSON sets no CPU limit; the publisher's leaderboard setting (`examples/all-tasks-k8s/experiment.yaml` (quoted in [`evidence/impact/edgebench-leaderboard-config.md`](../evidence/impact/edgebench-leaderboard-config.md)), sha256 `d9d29979…43be`) gives the grader 4 CPUs for the five games. The grader also sends space, CR and Esc every 1.5 s of wall time during play, which is an input stream that depends on timing. The prompt admits "small score noise", but its size is not measured.
- **Top reference point not checked.** Whether a raw mean of 50,000 (the reference point for 100) can be reached in 900 s is not checked. No run of a strong bot exists. The baseline bot that ships with the task scores essentially 0.

The note says:
- Scores depend on wall-clock speed and the CPU allocation; run-to-run noise is not measured.
- The reference point of 50,000 for a score of 100 has not been shown to be reachable.

The task is not changed; the note above ships with it.

## How much it matters

- Missing morgue: no effect; the game counts as 0 in the mean, as the prompt implies.
- Dependence on wall-clock speed: this affects every solver; its size is not measured. The published 12-hour results are 8.3, 13.4, 6.1, 7.6 and 5.7 out of 100 (`tasks/README.md`, dcss row); pairs 0.4 and 0.7 points apart could be reordered by noise of that size. Until the repeat runs in Limits exist, this outcome is provisional.

## How we checked it

- **Source of the original grader.** We read the pinned grader `eval_dcss.py` (sha256 `101e8858…2218`) and EdgeBench's grading and selection code (`grading.py`, `selection.py`, at `6e4e5f4`). The digest of the grader image is not recorded, and the copy of `eval_dcss.py` that was read is not published in this repository, so the quoted lines can be checked only against the grader image.
- **Exact arithmetic** on the grader's sleep schedule against `eval_timeout` 1100, and on the `log1p_max` score conversion.
- **Runs on the grader.** An idle bot scored 0 in 962 s total. One five-game run of a bot that makes progress scored 2, 21, 18, 7, 14 (mean 12.4).

## Limits

- No AI model or solver was run. Effects are shown only on the idle run and the run that makes progress.
- The missing-morgue path was reasoned from the source; it was not triggered.
- There is one five-game run with a positive score and no repeat. The check that would settle the noise question was not run: the same bot twice on one fixed allocation of at least 5 cores, and once on half that. If the spread is comparable to the differences between bots, the outcome would move to a fix or to withholding the task.

## Reproduce

- Review: `evidence/reviews/_game-tasks-correctness.md`, section 4.
- Pinned grader copy: the grader-image file `eval_dcss.py` (sha256 in [the review](../evidence/reviews/_game-tasks-correctness.md)).
- Harness grading and selection (EdgeBench `6e4e5f4`): `sforge/harness/grading.py`, `sforge/harness/selection.py`, `sforge/harness/score_rescale.py`.
