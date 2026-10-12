# Trinity (`trinity_text_adventure`)

**Decision:** Retain with note. The score is the game's own deterministic score, and no scoring defect was found; the note covers final-versus-peak scoring and undisclosed session limits.

## What the task asks for

"Play the interactive fiction game *Trinity* by sending commands via an HTTP API and maximize your score." The prompt states no horizon, step cap or number of games. Category: Interactive Games & Simulators.

## What goes wrong

No material defect was found. What was checked:

- **Score definition.** Each step reads `env.get_score()` from Z-machine memory. When a session ends (done, explicit close, idle reap or eviction) the archived score is the *final* score of that session, and the run score is the maximum final score over all sessions. The rescale is linear from 0 (the start score) to 100, which equals Jericho's `max_score` for this game (`trinity.c:71-73`). There is no shipped baseline. Example: a native walkthrough replay scored 100/100, which normalizes to 100.
- **Repeatability.** `FrotzEnv(rom)` with no seed falls back to the binding seed, which is 0, so the game's random number source does not depend on the time. Six sessions saw identical prefix trajectories. Given the command sequence, the game is fully deterministic.

Notes (documentation only, not material):

- **Final, not peak, score.** The archived score is the final score, while the API also returns `peak_score`, which could mislead an agent. This matters only if points can be lost during play. In all three supplied trajectories (Anchorhead, Trinity, Tryst) final equalled peak.
- **Undisclosed session limits.** The harness enforces limits the prompt does not mention: a 10 s HTTP timeout per step, at most 3 concurrent sessions per run (oldest evicted), and reaping after 600 s idle. Reaping and eviction archive the current score, so no score is lost, but an agent that pauses for more than 10 minutes mid-game loses the live game and must replay it. Replay is cheap: the full walkthroughs replayed in about 3 s of engine time.

**Note shipped with the task.**

- The score is the final in-game score of the best completed or closed session, out of the game's max_score (100).
- Sessions are reaped after 600 s idle; at most 3 sessions run concurrently.

## Impact

Maximum score effect observed: 0, for both notes. Only an agent that relies on `peak_score`, or pauses for more than 10 minutes mid-game, could be affected.

## Fix (v2)

No change; the note above ships with the task.

## How we know

- **Harness source.** Per-step score reading (`game_server_app.py`), session archiving and limits (`judge_server.py`), best-of-N selection (`selection.py`), validity gate (`grading.py`) and rescale (`score_rescale.py`) were read from the pinned harness. The copies match the hash-pinned copies byte for byte.
- **Game engine source.** The public Jericho 3.3.1 sdist gives the score source, `max_score` and the default seed.
- **Native runs.** Six sessions with full walkthrough replays. These ran on the host; no judge image digest is recorded.
- No formal model applies.

## Limits

- No model or solver was run. Effects are shown on walkthrough sessions only.
- No game was run in a pinned judge image.
- Jericho behavior comes from the upstream 3.3.1 source, not from hashing the installed bytes.
- Final-versus-peak was not tested in a trajectory where points are lost.

## Reproduce

- Review and pinned hashes: `evidence/reviews/_game-tasks-correctness.md`, sections 1-3.
- Pinned harness sources: `sforge/harness/judge_server.py`, `sforge/harness/game_server_app.py`, `sforge/harness/selection.py`, `sforge/harness/score_rescale.py`.
- Pinned identity: task JSON sha256 `7364a012…c0ee`; `judge_server.py` sha256 `77410d7e…`, `game_server_app.py` sha256 `379572e9…`, `score_rescale.py` sha256 `98feb630…`; Jericho 3.3.1 `jericho.py` sha256 `94f2e745…`.
