# Wesnoth Tactical AI (`wesnoth_tactical_ai`)

**Outcome:** Kept, with a note. <mark>The full grading run fits its time budget on one 8-vCPU host (80–172 s against 900 s), but the supplied starter's recruiting setting is broken on the pinned game version, so it scores 0, and games are not repeatable.</mark>

## What the task asks

The Battle for Wesnoth is a turn-based strategy game. The solver writes "a Lua AI for The Battle for Wesnoth 1.18 that wins turn-based multiplayer matches against the default AI". Lua is the scripting language the game uses for computer players. The score is "**total_score = 80 x win_rate + 20 x avg_efficiency**, evaluated over 3 maps x N seeds (default 10) x N repeats (default 2)". The prompt also says "The baseline AI (default C++ CAs) typically scores 0-20." The default grading run is 60 games under an `eval_timeout` of 900 s. Category: Interactive Games & Simulators.

## What we checked

No scoring problem was found in how games are scored. Four points are noted: the time limit, the broken starter, games that do not repeat, and a text scan that can reject a harmless file.

**1. The time budget fits, but there is a limit the task does not state.** A full-length game with the default AI takes about 3 s.

- Supplied starter: the full default grading run finished in **80 s**, exit 0, `TOTAL_SCORE 0`, `CASES_OK 0/60`, `TIMEOUT_COUNT 0`.
- Correct test submission using the game's stock AI: finished in **172 s**, exit 0, 60/60 games, `TIMEOUT_COUNT 0`, `TOTAL_SCORE 41` (18/60 wins). Wall time per game: mean 2.86 s, median 2.79 s, maximum 5.65 s.
- Headroom: a submitted AI could spend about 5x the stock AI's time per game, or about 15 s per game on average, before reaching 900 s. The per-game limit is 180 s, but 60 x 15 s = 900 s, so a heavy Lua AI could exceed the total budget. The task does not state this limit.
- Past 900 s, everything is lost, not just the late games: the grader prints its `CASE` lines and `TOTAL_SCORE` only after all 60 games finish, and when the harness timeout kills the grader, no `TOTAL_SCORE` is printed, so the submission has no score (EdgeBench's grading does not use the timeout flag itself, `sforge/harness/grading.py:224-241`).

**2. The supplied starter is broken on Wesnoth 1.18.5.** All three captured game logs of the starter (one per map) contain:

```
error ai/engine/cpp: side 1 : UNKNOWN candidate_action[ai_default_rca::aspect_recruitment_phase]
```

The game's stock 1.18 macro uses `name=default_recruitment::recruitment` instead. The starter's side 1 therefore never recruits units, and its leader is overrun. One original `run_game` per map:

| Map | Wall time | `run_game` return value | Markers in game output |
|---|---|---|---|
| Weldyn_Channel | 2.08 s | (False, 8, False) | `WINNER: 2`, `GAME_END_TURN: 8` |
| The_Freelands | 1.40 s | (False, 6, False) | `WINNER: 2`, `GAME_END_TURN: 6` |
| Fallenstar_Lake | 1.42 s | (False, 9, False) | `WINNER: 2`, `GAME_END_TURN: 9` |

The prompt's "typically scores 0-20" is technically met, since the score is 0. This is a starter problem, not a scoring problem: the grader scores a working AI correctly (41).

**3. Repeat games are not repeatable.** A fixed `--rng-seed` does not fix the outcome of games between two AIs. Repeat pairs (same map and seed, repeat 0 vs 1) were identical in only **1 of 30** pairs for the stock-AI test submission and 6 of 30 for the supplied starter. The second repeat therefore adds new samples rather than duplicating them.

Also observed: two stock-AI games on The_Freelands reached the 50-turn cap and printed no `WINNER`, and the grader scored them as losses.

How large this variation is per grading can be estimated, not measured: if the 60 games are independent with win probability p, the standard deviation of the win component (80 x win rate) is 80 x √(p(1 − p)/60). That is about 4.7 points out of 100 at p = 0.3 (the stock-AI control won 18/60) and about 3.7 points at p = 0.85, before any variation in efficiency.

**4. The grader's text scan can reject a harmless file.** Before any game, `scan_for_hacks()` searches the raw text of every submitted `.lua` file for `wml_actions`, `game_events`, `os\.execute`, `io\.open` and `debug\.`, and every `.cfg` file for `[kill]`, `[event]`, `[command]` and `wml_actions`. Comments and parts of longer names also match. Any match scores the whole submission 0. The prompt lists these APIs as forbidden ("violation = score=0 and hack flag") but does not say that comments and substrings count.

- **Example.** A comment `-- never use wesnoth.wml_actions here`, a table named `mydebug` used as `mydebug.log`, or a variable `n_game_events_seen` each matches a pattern (checked by applying the grader's patterns with Python's `re.search`). Such a submission scores 0. No such submission was graded.

**Note shipped with the task.**

- The supplied starter's recruiting candidate action is invalid on Wesnoth 1.18.5, so the starter scores 0. The suggested starter fix, `name=default_recruitment::recruitment` as in the stock macro, is not tested.
- Games are not reproducible despite `--rng-seed`.
- The 60-game total must fit in 900 s, about 15 s per game on average, even though the per-game limit is 180 s.

## How much it matters

- The broken recruiting setting affects only solvers who submit the starter unchanged or build on it; it scores 0.
- The total time limit affects only AIs that average more than about 15 s per game.
- Games that do not repeat add variance to every solver's score: about ±4 to ±5 points out of 100 per grading by the binomial estimate above, not measured. Recorded agent runs on this task score 36.3–88.0 out of 100 (`tasks/README.md`), so this variation is at a scoring level. The task's selection rule (`score_first`) keeps the best submission, so variation between gradings can raise a run's recorded best.
- The text scan affects only solvers whose files mention a forbidden name, in code or in a comment; it scores them 0.

There is no code change. The note above ships with the task.

## How we checked it

- **Original grader in the original image, pinned by digest.** The grader image (Wesnoth 1.18.5) ran with `--network none` on one 8-vCPU host with no CPU limit. For the supplied starter, the unmodified grader's `scan_for_hacks()`, `install_agent_ai()` and original `run_game(map, 0, 0)` ran once per map. Only `subprocess.run` was wrapped, to record the game output and elapsed time. Then the exact `eval_cmd` (`python3 /tmp/eval_wesnoth.py`) ran with defaults under `timeout 900`.
- **Correct test submission.** Side 1 was Wesnoth's own stock `data/ai/ais/ai_default_rca.cfg`, with only `id=` renamed to `my_custom_ai`. It passes the grader's hack scan. The full default grading run ran under `timeout 900`, through the unmodified grader with a timing wrapper on `subprocess.run`.
- No formal model applies.

## Limits

- No AI model or solver was run. Effects are shown only on the supplied starter and the stock-AI test submission.
- One 8-vCPU host with no CPU limit. A slower grading host could be several times slower and still fit in 900 s.
- The stock-AI test submission is Wesnoth's own AI, not a solver's submission. Each configuration ran one full grading run, so the variance of `TOTAL_SCORE` is a binomial estimate, not a measurement.
- The text-scan false positives come from reading the grader source and applying its patterns to sample strings; no such submission was graded.
- A possible problem installing Lua files in a subdirectory was not exercised.

## Reproduce

- `evidence/runs/wesnoth_tactical_ai-native-timing/run.sh` (supplied starter, with `game1.py`).
- `evidence/runs/wesnoth_tactical_ai-native-rca-control/run.sh` (stock-AI test submission, with `timed_eval.py`).
- Both need a Docker host that can pull the pinned images.
- Pinned identity: grader image `seededge/edgebench.judge.wesnoth_tactical_ai@sha256:660e126eddcd…`; work image `seededge/edgebench.work.wesnoth_tactical_ai@sha256:4d9b1e6515b2…`; `eval_wesnoth.py` sha256 `b1cbe456fc15…`; starter `my_custom_ai.cfg` `66e11740789a…` (the same file in both images; it is the whole submission).
- Supporting records: `evidence/reviews/wesnoth_tactical_ai-native.md`.
