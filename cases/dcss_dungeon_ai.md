# DCSS Dungeon Crawl Stone Soup AI (`dcss_dungeon_ai`)

**Outcome:** Kept, with a note. <mark>In normal runs the score matches what the task promises; the note covers the rule that all five end-of-game records must exist, the dependence on wall-clock speed and an unchecked top reference point.</mark>

## What the task asks

The solver writes a bot in Lua (a scripting language) for DCSS 0.28, the dungeon game Dungeon Crawl Stone Soup. The bot is scored on "5 hidden seeds, **900s game budget per game**, mean score across all 5 games". The games run in parallel, and the grader forces a quit at the deadline. The prompt says `Pass rate` "is a validity check, not the quality metric", and admits that "Wall-clock/PTTY scheduling can still create small score noise". Category: Interactive Games & Simulators.

## What we checked

There is no problem in normal runs. Checked and found correct: each game's score is the integer on line 5 of its morgue file (the game's end-of-game record). It is set to zero if wizard or explore mode appears. The total is the mean of the 5 games, rounded to 0.1. It is converted to a 0–100 score as `100*log1p(raw/400)/log1p(125)`. The code matches the prompt: 5 seeds, `TIMEOUT=900`, 5 games in parallel, and the quit sequence.

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

- **One missing morgue voids the submission.** The prompt describes the score as the mean of all 5 games. The grader emits `"valid": ok == total`, and the harness gives no score to an invalid result. Example: suppose one game fails to write a morgue (the forced-quit sequence fails twice). The prompt implies a mean with that game counted as 0. The original grader instead gives no score for the whole submission. This follows from the source and was not observed. Because the run keeps its best submission, this is softened.
- **Dependence on wall-clock and host speed.** The seeds are fixed, but the score is roughly turn rate × 900 s. The turn rate depends on the CPU given to five game processes running at once. No CPU limit is set for the task. The grader also sends space, CR and Esc every 1.5 s of wall time during play, which is an input stream that depends on timing. The prompt admits "small score noise", but its size is not measured.
- **Top reference point not checked.** Whether a raw mean of 50,000 (the reference point for 100) can be reached in 900 s is not checked. No run of a strong bot exists. The baseline bot that ships with the task scores essentially 0.

The note says:
- A submission is valid only if all 5 games produce a morgue; one missing morgue voids the score.
- Scores depend on wall-clock speed and the CPU allocation; run-to-run noise is not measured.
- The reference point of 50,000 for a score of 100 has not been shown to be reachable.

The task is not changed; the note above ships with it.

## How much it matters

- Missing morgue: the largest score change observed is 0. In the worst case, one failed game voids a whole submission.
- Dependence on wall-clock speed: this affects every solver; its size is not measured.

## How we checked it

- **Source of the original grader.** We read the pinned grader `eval_dcss.py` and the harness's validity check and selection code (`grading.py`, `selection.py`). The digest of the grader image is not recorded.
- **Exact arithmetic** on the grader's sleep schedule against `eval_timeout` 1100, and on the `log1p_max` score conversion.
- **Runs on the grader.** An idle bot scored 0 in 962 s total. One five-game run of a bot that makes progress scored 2, 21, 18, 7, 14 (mean 12.4).

## Limits

- No AI model or solver was run. Effects are shown only on the idle run and the run that makes progress.
- The missing-morgue path was reasoned from the source; it was not triggered.
- There is one five-game run with a positive score and no repeat. The check that would settle the noise question was not run: the same bot twice on one fixed allocation of at least 5 cores, and once on half that. If the spread is comparable to the differences between bots, the outcome would move to a fix or to withholding the task.

## Reproduce

- Review: `evidence/reviews/_game-tasks-correctness.md`, section 4.
- Pinned grader copy: the grader-image file `eval_dcss.py` (sha256 in [the review](../evidence/reviews/_game-tasks-correctness.md)).
- Harness validity check and selection: `sforge/harness/grading.py`, `sforge/harness/selection.py`, `sforge/harness/score_rescale.py`.
