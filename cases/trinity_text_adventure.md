# Trinity (`trinity_text_adventure`)

**Outcome:** Kept, with a note. <mark>The score is the game's own repeatable score, and we found no scoring defect; the note covers the use of the final score instead of the peak score, and session limits that the task text does not disclose.</mark>

## What the task asks

The task text says: "Play the interactive fiction game *Trinity* by sending commands via an HTTP API and maximize your score." *Trinity* is a text adventure game. The task text states no time horizon, no cap on steps and no number of games. Category: Interactive Games & Simulators.

## What we checked

We found no defect that changes scores. We checked the following parts.

- Each step reads `env.get_score()` from the memory of the Z-machine, the virtual machine that runs the game. A session can end in four ways: the game is done, the session is closed explicitly, the harness closes it after it sits idle (reaped), or a newer session pushes it out (evicted). In each case the stored score is the *final* score of that session. The score for the run is the highest final score over all sessions. The score scale is linear, from 0 (the start score) to 100, which equals the `max_score` that the Jericho game library sets for this game (`trinity.c:71-73`). No starting solution ships with the task. Replaying the 610-command walkthrough on the host scored 100/100, which is also 100 out of 100.
- `FrotzEnv(rom)` with no seed falls back to the library's default seed, which is 0, so the game's random number source does not depend on the time. We ran two Trinity sessions, a 25-command partial session and the 610-command full walkthrough (six sessions across the three Jericho games). Their scores were equal over the shared 25-command prefix (`prefix_numeric_equal: true`). Given the sequence of commands, the game is deterministic.

Two notes are documentation only and do not change scores.

- The stored score is the final score, not the peak, while the API also returns `peak_score`, which could mislead an agent. The difference counts only if points can be lost during play. In all three supplied trajectories (Anchorhead, Trinity, Tryst) the final score equalled the peak.
- The harness enforces session limits that the task text does not mention: a 10 s HTTP timeout per step, at most 3 sessions at once per run (the oldest is evicted), and closing after 600 to 660 s idle (the idle check runs every 60 s, `judge_server.py:156,159`). Closing and eviction store the current score, so no score is lost, but an agent that pauses for more than 10 minutes in the middle of a game loses the live game and must replay it. Replay is cheap; the recorded HTTP replay of the 610-command Trinity walkthrough took 29.3 s (`elapsed_seconds: 29.325236`).

The task ships with this note.

- The score is the final in-game score of the best completed or closed session, out of the game's max_score (100).
- The harness closes sessions after 600 to 660 s idle; at most 3 sessions run at once.

## How much it matters

The largest effect on scores observed is 0, for both notes. Only an agent that relies on `peak_score`, or pauses for more than 10 minutes in the middle of a game, could be affected.

The task does not change; the note above ships with it.

## How we checked it

- From the pinned harness we read how it reads the score at each step (`game_server_app.py`), storing sessions and enforcing limits (`judge_server.py`), keeping the best of N sessions (`selection.py`), the validity check (`grading.py`) and the score scale (`score_rescale.py`). These copies match the hash-pinned copies byte for byte.
- The public Jericho 3.3.1 source package (sdist) gives the source of the score, `max_score` and the default seed.
- On the host we ran two Trinity sessions (one 25-command partial, one 610-command full walkthrough), part of six sessions across Anchorhead, Trinity and Tryst. They ran on a locally built image (`built_image_id sha256:a197e54f…`), and we did not record a digest of a public grader image.
- No formal model applies.

## Limits

- We ran no AI model or solver. The effects shown come only from walkthrough sessions.
- We ran no game in a pinned grader image.
- Jericho's behaviour comes from the published 3.3.1 source, not from hashing the installed files.
- We did not test the difference between final and peak score in a trajectory where points are lost.
- We compared repeatability over a 25-command shared prefix only.

## Reproduce

- Review and pinned hashes: `evidence/reviews/_game-tasks-correctness.md`, sections 1-3.
- Session records (preserved at Git tag `earlier-audit-final`): `git show earlier-audit-final:evidence/selected/three-adventure-native-release-acceptance.json` (six sessions, Trinity partial 25 commands score 7, full 610 commands score 100, prefix equal) and `git show earlier-audit-final:evidence/selected/trinity-tryst-terminal-acceptance.json` (Trinity HTTP replay, 29.3 s).
- Pinned harness sources: `sforge/harness/judge_server.py`, `sforge/harness/game_server_app.py`, `sforge/harness/selection.py`, `sforge/harness/score_rescale.py`.
- Pinned identity: task JSON sha256 `7364a012…c0ee`; `judge_server.py` sha256 `77410d7e…`, `game_server_app.py` sha256 `379572e9…`, `score_rescale.py` sha256 `98feb630…`; Jericho 3.3.1 `jericho.py` sha256 `94f2e745…`.
