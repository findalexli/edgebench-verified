# Tryst of Fate (`tryst_text_adventure`)

**Outcome:** Kept, with a note. The score is the game's own repeatable score, and no scoring problem was found; the note says that a session's final score counts, not its peak, and lists session limits the prompt does not state.

## What the task asks

"Play the interactive fiction game *Tryst of Fate* by sending commands via an HTTP API and maximize your score." The prompt states no length of play, step limit or number of games. Category: Interactive Games & Simulators.

## What we checked

No problem that changes scores enough to matter was found. What was checked:

- **How the score is defined.** Each step reads `env.get_score()` from the memory of the Z-machine (the virtual machine that runs the game). A session can end because the game is done, because it is explicitly closed, because it is closed after sitting idle, or because a newer session pushes it out. In each case the stored score is the *final* score of that session. The run's score is the highest final score over all sessions. The score scale is linear from 0 (the starting score) to 350, which equals Jericho's `max_score` for this game (`tryst.c:97`). Jericho is the library that runs the game. No baseline solution ships with the task. Example: replaying a full walkthrough on the host scored 350/350, which converts to 100 out of 100.
- **Repeatability.** `FrotzEnv(rom)` with no seed falls back to the library's default seed, which is 0, so the game's random number source does not depend on the time. Six sessions saw identical sequences of game states from the same commands. Given the command sequence, the game is fully deterministic.

Notes (documentation only; they do not change scores):

- **Final score, not peak score.** The stored score is the final score, while the API also returns `peak_score`, which could mislead an agent. This matters only if points can be lost during play. In all three supplied game records (Anchorhead, Trinity, Tryst) the final score equalled the peak.
- **Session limits the prompt does not state.** The harness enforces limits the prompt does not mention: a 10 s HTTP timeout per step, at most 3 sessions at once per run (the oldest is pushed out), and closing a session after 600 s idle. Closing a session for either reason stores its current score, so no score is lost. But an agent that pauses for more than 10 minutes mid-game loses the live game and must replay it. Replay is cheap: the full walkthroughs replayed in about 3 s of engine time.

**Note shipped with the task.**

- The score is the final in-game score of the best completed or closed session, out of the game's max_score (350).
- Sessions are reaped after 600 s idle; at most 3 sessions run concurrently.

The task is not changed; the note above ships with it.

## How much it matters

The largest score change observed is 0, for both notes. Only an agent that relies on `peak_score`, or pauses for more than 10 minutes mid-game, could be affected.

## How we checked it

- **Harness source.** We read the per-step score reading (`game_server_app.py`), session storage and limits (`judge_server.py`), the rule that keeps the best submission (`selection.py`), the validity check (`grading.py`) and the score conversion (`score_rescale.py`) in the pinned harness. These copies match the hash-pinned copies byte for byte.
- **Game engine source.** The public Jericho 3.3.1 source package gives the source of the score, `max_score` and the default seed.
- **Runs on the host.** Six sessions with full walkthrough replays. These ran on the host machine; no digest of the grader image is recorded.
- No formal model applies.

## Limits

- No AI model or solver was run. Effects are shown only on walkthrough sessions.
- No game was run in a pinned grader image.
- Jericho's behavior comes from the upstream 3.3.1 source, not from hashing the installed bytes.
- Final score versus peak score was not tested in a game where points are lost.

## Reproduce

- Review and pinned hashes: `evidence/reviews/_game-tasks-correctness.md`, sections 1-3.
- Pinned harness sources: `sforge/harness/judge_server.py`, `sforge/harness/game_server_app.py`, `sforge/harness/selection.py`, `sforge/harness/score_rescale.py`.
- Pinned identity: task JSON sha256 `a6e4815a…1b5f`; `judge_server.py` sha256 `77410d7e…`, `game_server_app.py` sha256 `379572e9…`, `score_rescale.py` sha256 `98feb630…`; Jericho 3.3.1 `jericho.py` sha256 `94f2e745…`.
