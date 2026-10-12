# Anchorhead (`anchorhead_text_adventure`)

Status: reviewed by the coordinator, 2026-10-12

- **Domain:** Interactive Games & Simulators
- **Decision:** Retain with note — the score is the game's own deterministic score; the note covers
  final-versus-peak scoring and undisclosed session limits. No scoring defect was found.

## What the task promises

"Play the interactive fiction game *Anchorhead* by sending commands via an HTTP API and maximize
your score." The prompt states no horizon, step cap or number of games.

## What we checked and how

- Source reading of the pinned game harness: per-step score reading (`game_server_app.py`),
  session archiving and limits (`judge_server.py`), best-of-N selection (`selection.py`), validity
  gate (`grading.py`) and rescale (`score_rescale.py`). The selected copies match the hash-pinned
  copies byte for byte.
- Source reading of the public Jericho 3.3.1 sdist (the version the earlier runtime lock names) for
  the score source, `max_score` and the default seed. The installed bytes in the image were not
  hashed in this review.
- Reuse of an earlier accepted native result: six host sessions with full walkthrough replays.
  No game was rerun for this review.
- Original identity: judge image digest not recorded in the review; task JSON sha256
  `4b92b45a…31cb2`; `judge_server.py` sha256 `77410d7e…`, `game_server_app.py` sha256 `379572e9…`,
  `score_rescale.py` sha256 `98feb630…`; Jericho 3.3.1 `jericho.py` sha256 `94f2e745…`.

## What we found

### Score definition — consistent with the promise

Each step reads `env.get_score()` from Z-machine memory. When a session ends (done, explicit close,
idle reap or eviction) the archived score is the *final* score of that session, and the run score
is the maximum final score over all sessions. The rescale is linear from 0 (the start score) to
100, which equals Jericho's `max_score` for this game (`anchor.c:84-86`). There is no shipped
baseline.
- Example: the earlier native walkthrough replay scored 99/100, which normalizes to 99.

### Repeatability — deterministic

`FrotzEnv(rom)` with no seed falls back to the binding seed, which is 0, so the game's random
number source does not depend on the time. The six earlier sessions saw identical prefix
trajectories. Given the command sequence, the game is fully deterministic.

### Final, not peak, score — Not material (documentation note)

The archived score is the final score, while the API also returns `peak_score`, which could mislead
an agent. This matters only if points can be lost during play. In all three supplied trajectories
(Anchorhead, Trinity, Tryst) final equalled peak.
- Maximum score effect observed: 0.

### Undisclosed session limits — Not material (documentation note)

The harness enforces limits the prompt does not mention: a 10 s HTTP timeout per step, at most 3
concurrent sessions per run (oldest evicted), and reaping after 600 s idle. Reaping and eviction
archive the current score, so no score is lost, but an agent that pauses for more than 10 minutes
mid-game loses the live game and must replay it. Replay is cheap: the full walkthroughs replayed in
about 3 s of engine time.
- Maximum score effect observed: 0.

### Anchorhead ceiling not demonstrated — Unverified, not material to the decision

The supplied reference walkthrough ends at 99 with game_over=true and victory=false. Whether 100/100
is reachable in the pinned ROM is unverified. The upper anchor of 100 is the game's own `max_score`,
so the uncertainty about the ceiling is at most 1 normalized point.
- Example: walkthrough replay under the original harness: 99/100, normalized 99.
- Maximum score effect: at most 1 normalized point, and only if 100 is unreachable.

## Note for users

No repair. The note says:
- The score is the final in-game score of the best completed or closed session, out of the game's
  max_score (100).
- Sessions are reaped after 600 s idle; at most 3 sessions run concurrently.
- Anchorhead's reference walkthrough reaches 99/100; full score was not demonstrated.

## Limits and what was not run

- No model or solver re-runs. Effects are shown on authored controls and counterexamples only (here,
  the reused walkthrough sessions).
- No game was run for this review; native results are reused from the earlier accepted sessions.
- Jericho behavior comes from the upstream 3.3.1 source, not from hashing the installed bytes.
- Final-versus-peak was not tested in a trajectory where points are lost.
- Whether 100/100 is reachable in Anchorhead was not checked. A command sequence that attains 100
  in the pinned ROM would remove that part of the note; it would not change the decision.
- Release bookkeeping (refreezing derived pins, approvals) is pending and is not science.

## Reproduce

- Review and pinned hashes: `evidence/reviews/_game-tasks-correctness.md`, sections 1-3.
- Pinned harness sources: `sforge/harness/judge_server.py`, `sforge/harness/game_server_app.py`,
  `sforge/harness/selection.py`, `sforge/harness/score_rescale.py`.
