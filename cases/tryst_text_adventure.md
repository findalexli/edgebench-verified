# Tryst of Fate (`tryst_text_adventure`)

**Outcome:** Kept, with a note. <mark>The score is the game's own repeatable score, and no scoring problem was found; the note says that a session's final score counts, not its peak, and lists session limits the prompt does not state.</mark>

## What the task asks

"Play the interactive fiction game *Tryst of Fate* by sending commands via an HTTP API and maximize your score." The prompt states no length of play, step limit or number of games. Category: Interactive Games & Simulators.

## What we checked

No problem that changes scores was found. What was checked:

- **How the score is defined.** Each step reads `env.get_score()` from the memory of the Z-machine (the virtual machine that runs the game). A session can end because the game is done, because it is explicitly closed, because it is closed after sitting idle, or because a newer session pushes it out. In each case the stored score is the *final* score of that session. The run's score is the highest final score over all sessions. The score scale is linear from 0 (the starting score) to 350, which equals Jericho's `max_score` for this game (`tryst.c:97`). Jericho is the library that runs the game. No baseline solution ships with the task. Example: replaying a full walkthrough on the host scored 350/350, which converts to 100 out of 100.
- **Repeatability.** `FrotzEnv(rom)` with no seed falls back to the library's default seed, which is 0, so the game's random number source does not depend on the time. A 25-command partial replay matched the first 25 steps of a full walkthrough replay, and two separate full replays of the walkthrough (518 commands) both scored 350/350. Given the command sequence, the game is deterministic.

Notes (documentation only; they do not change scores):

- **Final score, not peak score.** The stored score is the final score, while the API also returns `peak_score`, which could mislead an agent. This matters only if points can be lost during play. In all three supplied game records (Anchorhead, Trinity, Tryst) the final score equalled the peak.
- **Session limits the prompt does not state.** The harness enforces limits the prompt does not mention: a 10 s HTTP timeout per step, at most 3 sessions at once per run (the oldest is pushed out), and closing a session after 600 to 660 s idle (the idle check runs every 60 s, `judge_server.py:156,159`). Closing a session for either reason stores its current score once the session's game container has been removed, so no score is lost. If the removal fails, the session is kept and retried at the next idle check, and its score is stored only after a removal succeeds (`judge_server.py:226-239`). An agent that pauses for more than 10 minutes mid-game loses the live game and must replay it. Replay is cheap: a recorded HTTP replay of the full walkthrough (518 commands) took 32 s.

**Note shipped with the task.**

- The score is the final in-game score of the best completed or closed session, out of the game's max_score (350).
- Sessions are reaped after 600 to 660 s idle; at most 3 sessions run concurrently.

The task is not changed; the note above ships with it.

## How much it matters

The largest score change observed is 0, for both notes. Only an agent that relies on `peak_score`, or pauses for more than 10 minutes mid-game, could be affected.

A third-party Claude Opus 5.5 run (4 hours, published on Hugging Face as `adafadaq/edgebench-opus-5-5-xhigh-rollouts`) has 480 session logs in this repository. All 477 stored session results have final score equal to peak score; the best is 215/350 (game-81). Three sessions (game-95, game-465, game-479) reached 215 according to their step logs but have no stored result; the run's best score of 215 is unaffected.

## How we checked it

- **Harness source.** We read the per-step score reading (`game_server_app.py`), session storage and limits (`judge_server.py`), the rule that keeps the best submission (`selection.py`), the validity check (`grading.py`) and the score conversion (`score_rescale.py`) in the pinned harness. These copies match the hash-pinned copies byte for byte.
- **Game engine source.** The public Jericho 3.3.1 source package gives the source of the score, `max_score` and the default seed.
- **Runs on the host.** Six sessions ran on the host through this repository's copy of EdgeBench's harness (`JudgeState` with the Docker backend; its grading and selection files were then the earlier audit's modified version; the session scores reported here come from the game server and do not depend on them), in game containers built from the original game files (built image id `sha256:a197e54f…`); the digest of the public grader image is not recorded. For each of Anchorhead, Trinity and Tryst there was one full walkthrough replay and one 25-command partial replay, and each partial replay's scores matched the first 25 steps of the full replay. Separately, one full walkthrough replay through the game container's HTTP endpoints scored 350/350 in 32 s.
- No formal model applies.

## Limits

- No AI model or solver was run by us. Effects are shown on walkthrough sessions; the third-party run above was read, not replayed.
- No game was run in the public grader image pinned by digest. The game containers were built from the original game files (image id `sha256:a197e54f…`).
- Jericho's behavior comes from the upstream 3.3.1 source, not from hashing the installed bytes.
- Final score versus peak score was not tested in a game where points are lost.

## Reproduce

- Review and pinned hashes: `evidence/reviews/_game-tasks-correctness.md`, sections 1-3.
- Session records: `git show earlier-audit-final:evidence/selected/three-adventure-native-release-acceptance.json` and `git show earlier-audit-final:evidence/selected/trinity-tryst-terminal-acceptance.json`.
- Third-party run: `evidence/runs/opus55-rollouts-meta/result/meta/opus-16x4h-1009-0036-w3/tryst_text_adventure/` (`final_result.json`, `submissions/game-*/game_result.json` and `steps.jsonl`).
- Pinned harness sources: `sforge/harness/judge_server.py`, `sforge/harness/game_server_app.py`, `sforge/harness/selection.py`, `sforge/harness/score_rescale.py`.
- Pinned identity: task JSON sha256 `a6e4815a…1b5f`; `judge_server.py` sha256 `77410d7e…`, `game_server_app.py` sha256 `379572e9…`, `score_rescale.py` sha256 `98feb630…`; Jericho 3.3.1 `jericho.py` sha256 `94f2e745…`.
