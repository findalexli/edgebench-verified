# Wesnoth Tactical AI (`wesnoth_tactical_ai`)

Status: reviewed by the coordinator, 2026-10-12

- **Domain:** Interactive Games & Simulators
- **Decision:** Retain with note — the full evaluation fits its time budget (80–172 s against 900 s), but the shipped baseline's recruit configuration is broken on the pinned engine, so it scores 0, and games are not repeatable.

## What the task promises

The solver writes "a Lua AI for The Battle for Wesnoth 1.18 that wins turn-based multiplayer matches against the default AI". The score is "**total_score = 80 x win_rate + 20 x avg_efficiency**, evaluated over 3 maps x N seeds (default 10) x N repeats (default 2)". The prompt also says "The baseline AI (default C++ CAs) typically scores 0-20."

## What we checked and how

- **Question:** can the default evaluation (60 games) finish within `eval_timeout` of 900 s? An earlier review estimated more than 15 s per game, called the task "likely OpenRCT2-class", and left it pending, to be withheld if the timing failed.
- Job A, shipped baseline, on an 8-vCPU E2B worker. The judge image ran with `--network none --memory 6g` and no CPU limit.
  - The unmodified evaluator's `scan_for_hacks()`, `install_agent_ai()` and original `run_game(map, 0, 0)` were run once per map. Only `subprocess.run` was wrapped, to record engine output and elapsed time.
  - Then the exact `eval_cmd` (`python3 /tmp/eval_wesnoth.py`) ran with defaults under `timeout 900`.
- Job B, control. Side 1 was Wesnoth's own stock `data/ai/ais/ai_default_rca.cfg`, with only `id=` renamed to `my_custom_ai`. It passes the evaluator's hack scan. The full default evaluation ran under `timeout 900`, through the unmodified evaluator with a timing shim on `subprocess.run`.
- Engine: Wesnoth 1.18.5. Its user data directory matches the evaluator's `USER_DATA_DIR`.
- Original identity: judge image `seededge/edgebench.judge.wesnoth_tactical_ai@sha256:660e126eddcd…`; work image `seededge/edgebench.work.wesnoth_tactical_ai@sha256:4d9b1e6515b2…`; key files `eval_wesnoth.py` sha256 `b1cbe456fc15…` (measured in the container), baseline `my_custom_ai.cfg` `66e11740789a…` (the same file in both images; it is the whole submission).

## What we found

**Refuted: the timing concern.** An earlier audit left this task pending because a game was estimated to take more than 15 s. Re-checking showed that a full-length default-AI game takes about 3 s.

- Shipped baseline: the full default evaluation finished in **80 s**, exit 0, `TOTAL_SCORE 0`, `CASES_OK 0/60`, `TIMEOUT_COUNT 0`.
- Control: finished in **172 s**, exit 0, 60/60 games, `TIMEOUT_COUNT 0`, `TOTAL_SCORE 41` (18/60 wins). Per-game wall time: mean 2.86 s, median 2.79 s, maximum 5.65 s.
- Headroom: a submitted AI could spend about 5x the stock AI's time per game, or about 15 s per game on average, before reaching 900 s. The per-game limit is 180 s, but 60 x 15 s = 900 s, so a heavy Lua AI could exceed the total budget. That cliff is not disclosed. This is a note-level caveat, not a defect for honest default-speed play.

**Confirmed: the shipped baseline is broken on Wesnoth 1.18.5.** Every baseline game log contains:

```
error ai/engine/cpp: side 1 : UNKNOWN candidate_action[ai_default_rca::aspect_recruitment_phase]
```

The stock 1.18 macro uses `name=default_recruitment::recruitment`. The baseline's side 1 therefore never recruits, and its leader is overrun. One original `run_game` per map:

| Map | Wall time | `run_game` return | Markers in engine output |
|---|---|---|---|
| Weldyn_Channel | 2.08 s | (False, 8, False) | `WINNER: 2`, `GAME_END_TURN: 8` |
| The_Freelands | 1.40 s | (False, 6, False) | `WINNER: 2`, `GAME_END_TURN: 6` |
| Fallenstar_Lake | 1.42 s | (False, 9, False) | `WINNER: 2`, `GAME_END_TURN: 9` |

The prompt's "typically scores 0-20" is technically met, since the score is 0. This is a starter defect, not a scoring defect. The maximum effect is on the baseline only. The control shows that the evaluator scores a working AI (41).

**Confirmed: the repeats are not repeatable.** A fixed `--rng-seed` does not fix the outcome of AI-vs-AI games. Repeat pairs (same map and seed, repeat 0 vs 1) were identical in only **1 of 30** pairs for the control and 6 of 30 for the shipped baseline. An earlier statement that "With a fixed seed, the 2 repeats are expected to be identical" is false. The second repeat adds samples. The run-to-run variance of `TOTAL_SCORE` was not measured.

Also observed: two control games on The_Freelands reached the 50-turn cap and printed no `WINNER`, and the evaluator scored them as losses.

## Note for users

No repair. The note says:

- The shipped baseline's recruit candidate action is invalid on Wesnoth 1.18.5, so the baseline scores 0. The suggested starter fix, `name=default_recruitment::recruitment` as in the stock macro, is not tested.
- Games are not reproducible despite `--rng-seed`.
- The 60-game total must fit in 900 s, about 15 s per game on average, even though the per-game limit is 180 s.

## Limits and what was not run

- No model or solver re-runs. Effects are shown on the shipped baseline and the stock-AI control only.
- One 8-vCPU host with no CPU limit. A slower harness host could be several times slower and still fit 900 s.
- The control is Wesnoth's stock AI, not a submission. Each configuration ran one full evaluation, so there is no variance estimate.
- The Lua-in-subdirectory installation issue raised earlier was not exercised.

## Reproduce

- `evidence/runs/wesnoth_tactical_ai-native-timing/run.sh` (shipped baseline, with `game1.py`).
- `evidence/runs/wesnoth_tactical_ai-native-rca-control/run.sh` (stock-AI control, with `timed_eval.py`).
- Both need a Docker host that can pull the pinned images.
- Review: `evidence/reviews/wesnoth_tactical_ai-native.md`.
