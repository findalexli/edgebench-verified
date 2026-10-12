# Wesnoth Tactical AI (`wesnoth_tactical_ai`)

**Decision:** Retain with note. The full evaluation fits its time budget on one 8-vCPU host (80–172 s against 900 s), but the shipped baseline's recruit configuration is broken on the pinned engine, so it scores 0, and games are not repeatable.

## What the task asks for

The solver writes "a Lua AI for The Battle for Wesnoth 1.18 that wins turn-based multiplayer matches against the default AI". The score is "**total_score = 80 x win_rate + 20 x avg_efficiency**, evaluated over 3 maps x N seeds (default 10) x N repeats (default 2)". The prompt also says "The baseline AI (default C++ CAs) typically scores 0-20." The default evaluation is 60 games under an `eval_timeout` of 900 s. Category: Interactive Games & Simulators.

## What goes wrong

No scoring defect was found. Three points are noted.

**1. The time budget fits, with an undisclosed cliff.** A full-length default-AI game takes about 3 s.

- Shipped baseline: the full default evaluation finished in **80 s**, exit 0, `TOTAL_SCORE 0`, `CASES_OK 0/60`, `TIMEOUT_COUNT 0`.
- Stock-AI control: finished in **172 s**, exit 0, 60/60 games, `TIMEOUT_COUNT 0`, `TOTAL_SCORE 41` (18/60 wins). Per-game wall time: mean 2.86 s, median 2.79 s, maximum 5.65 s.
- Headroom: a submitted AI could spend about 5x the stock AI's time per game, or about 15 s per game on average, before reaching 900 s. The per-game limit is 180 s, but 60 x 15 s = 900 s, so a heavy Lua AI could exceed the total budget. That cliff is not disclosed.

**2. The shipped baseline is broken on Wesnoth 1.18.5.** Every baseline game log contains:

```
error ai/engine/cpp: side 1 : UNKNOWN candidate_action[ai_default_rca::aspect_recruitment_phase]
```

The stock 1.18 macro uses `name=default_recruitment::recruitment`. The baseline's side 1 therefore never recruits, and its leader is overrun. One original `run_game` per map:

| Map | Wall time | `run_game` return | Markers in engine output |
|---|---|---|---|
| Weldyn_Channel | 2.08 s | (False, 8, False) | `WINNER: 2`, `GAME_END_TURN: 8` |
| The_Freelands | 1.40 s | (False, 6, False) | `WINNER: 2`, `GAME_END_TURN: 6` |
| Fallenstar_Lake | 1.42 s | (False, 9, False) | `WINNER: 2`, `GAME_END_TURN: 9` |

The prompt's "typically scores 0-20" is technically met, since the score is 0. This is a starter defect, not a scoring defect: the evaluator scores a working AI (41).

**3. Repeats are not repeatable.** A fixed `--rng-seed` does not fix the outcome of AI-vs-AI games. Repeat pairs (same map and seed, repeat 0 vs 1) were identical in only **1 of 30** pairs for the control and 6 of 30 for the shipped baseline. The second repeat adds samples rather than duplicating them.

Also observed: two control games on The_Freelands reached the 50-turn cap and printed no `WINNER`, and the evaluator scored them as losses.

**Note shipped with the task.**

- The shipped baseline's recruit candidate action is invalid on Wesnoth 1.18.5, so the baseline scores 0. The suggested starter fix, `name=default_recruitment::recruitment` as in the stock macro, is not tested.
- Games are not reproducible despite `--rng-seed`.
- The 60-game total must fit in 900 s, about 15 s per game on average, even though the per-game limit is 180 s.

## Impact

- The broken recruit configuration affects only solvers who submit the baseline unchanged or build on it; it scores 0.
- The time cliff affects only AIs that average more than about 15 s per game.
- Non-repeatability affects every solver's score variance; its size was not measured.

## Fix (v2)

No change; the note above ships with the task.

## How we know

- **Original evaluator in the pinned image.** The judge image (`sha256:660e126eddcd…`, Wesnoth 1.18.5) ran with `--network none` on one 8-vCPU host with no CPU limit. For the shipped baseline, the unmodified evaluator's `scan_for_hacks()`, `install_agent_ai()` and original `run_game(map, 0, 0)` ran once per map, with only `subprocess.run` wrapped to record engine output and elapsed time. Then the exact `eval_cmd` (`python3 /tmp/eval_wesnoth.py`) ran with defaults under `timeout 900`.
- **Control.** Side 1 was Wesnoth's own stock `data/ai/ais/ai_default_rca.cfg`, with only `id=` renamed to `my_custom_ai`. It passes the evaluator's hack scan. The full default evaluation ran under `timeout 900`, through the unmodified evaluator with a timing shim on `subprocess.run`.
- No formal model applies.

## Limits

- No model or solver was run. Effects are shown on the shipped baseline and the stock-AI control only.
- One 8-vCPU host with no CPU limit. A slower harness host could be several times slower and still fit 900 s.
- The control is Wesnoth's stock AI, not a submission. Each configuration ran one full evaluation, so there is no variance estimate for `TOTAL_SCORE`.
- A possible problem installing Lua files in a subdirectory was not exercised.

## Reproduce

- `evidence/runs/wesnoth_tactical_ai-native-timing/run.sh` (shipped baseline, with `game1.py`).
- `evidence/runs/wesnoth_tactical_ai-native-rca-control/run.sh` (stock-AI control, with `timed_eval.py`).
- Both need a Docker host that can pull the pinned images.
- Pinned identity: judge image `seededge/edgebench.judge.wesnoth_tactical_ai@sha256:660e126eddcd…`; work image `seededge/edgebench.work.wesnoth_tactical_ai@sha256:4d9b1e6515b2…`; `eval_wesnoth.py` sha256 `b1cbe456fc15…`; baseline `my_custom_ai.cfg` `66e11740789a…` (the same file in both images; it is the whole submission).
- Supporting records: `evidence/reviews/wesnoth_tactical_ai-native.md`.
