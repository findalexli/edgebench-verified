# Anchorhead (`anchorhead_text_adventure`)

**Outcome:** Kept, with a note. <mark>The score is the game's own score, which is the same every time for the same commands; the note covers final-versus-peak scoring and session limits the task does not state.</mark>

## What the task asks

The prompt says: "Play the interactive fiction game *Anchorhead* by sending commands via an HTTP API and maximize your score." Interactive fiction is a text adventure: the player types commands and the game replies in text. The prompt states no time horizon, step cap or number of games. Category: Interactive Games & Simulators.

EdgeBench gives an AI agent the task, and the agent works for up to 12 hours. A hidden grader program scores the result. Its raw result (before conversion to 0–100) is converted to a score out of 100 using reference points chosen by the task authors.

## What we checked

There is no scoring problem. The following parts were checked and found correct.

- **How the score is defined.** At each step the grader reads `env.get_score()` from the memory of the Z-machine, the virtual machine that runs the game. A session can end in four ways: the game finishes, the agent closes it, it is closed after sitting idle, or it is evicted to make room for a newer session. When a session ends, the grader stores the *final* score of that session. The run's score is the highest final score over all its sessions. The score scale is linear. Its reference point for 0 is the start score. Its reference point for 100 is 100, which equals Jericho's `max_score` for this game (`anchor.c:84-86`). Jericho is the library that runs the game. The task ships no baseline reference point. Example: a replay of the walkthrough scored 99/100, which is 99 out of 100.
- **Repeatability.** `FrotzEnv(rom)` is called with no seed, so it falls back to the library's default seed, which is 0. The game's random number source therefore does not depend on the clock. For a given sequence of commands, the game plays exactly the same way every time.

Notes:

- **Final score, not peak score.** The grader stores the final score. The API also returns a `peak_score`, which could mislead an agent into thinking the peak counts. This matters only if points can be lost during play. In all three supplied play recordings (Anchorhead, Trinity, Tryst), the final score equalled the peak.
- **Session limits the prompt does not state.** The harness enforces three limits:
  - a 10 s HTTP timeout per step;
  - at most 3 sessions at once per run (the oldest is evicted);
  - closing a session after 600 to 660 s idle (the idle check runs every 60 s, `judge_server.py:156,159`).

  Closing and eviction both store the current score once the session's game container has been removed, so no score is lost. If the removal fails, the session is kept and retried at the next idle check, and its score is stored only after a removal succeeds (`judge_server.py:226-239`). An agent that pauses for more than 10 minutes in the middle of a game loses the live game and must replay it. Replay is cheap: recorded HTTP replays of the full Trinity (610 commands) and Tryst (518 commands) walkthroughs took 29 s and 32 s.
- **Full score not shown to be reachable.** The supplied reference walkthrough ends at 99 with game_over=true and victory=false. Whether 100/100 can be reached in the pinned game file is not verified.

The note says:

- The score is the final in-game score of the best completed or closed session, out of the game's max_score (100).
- Sessions are closed after 600 to 660 s idle; at most 3 sessions run at once.
- Anchorhead's reference walkthrough reaches 99/100; full score was not demonstrated.

## How much it matters

- Final versus peak score: the largest score effect seen is 0.
- Session limits: the largest score effect seen is 0. Only agents that pause for over 10 minutes in the middle of a game must replay it.
- Full score: at most 1 point out of 100, and only if 100 cannot be reached.

There is no code change. The note above ships with the task.

## How we checked it

- **Original grader, pinned sources.** We read the code for each part of scoring:
  - reading the score at each step (`game_server_app.py`);
  - storing session scores and enforcing session limits (`judge_server.py`);
  - keeping the best of all sessions (`selection.py`);
  - the validity check (`grading.py`);
  - converting to the score scale (`score_rescale.py`).

  The repository copies match the hash-pinned copies byte for byte. The digest of the grader image is not recorded.
- **Sessions run on the host.** Six sessions ran on the host through this repository's copy of EdgeBench's harness (`JudgeState` with the Docker backend; its grading and selection files were then the earlier audit's modified version; the session scores reported here come from the game server and do not depend on them), in game containers built from the original game files (built image id `sha256:a197e54f…`); the digest of the public grader image is not recorded. For each of Anchorhead, Trinity and Tryst there was one full walkthrough replay and one 25-command partial replay, and each partial replay's scores matched the first 25 steps of the full replay. The Anchorhead walkthrough (531 commands) scored 99/100.
- **Upstream game-engine source.** The score source, `max_score` and the default seed were read from the public Jericho 3.3.1 source package (sdist).

## Limits

- No AI model or solver was run. Effects are shown only on the walkthrough sessions.
- Anchorhead's repeatability rests on one partial replay compared with one full replay over 25 steps, plus Jericho's fixed default seed.
- Jericho's behaviour comes from the upstream 3.3.1 source. The installed files in the image were not hashed.
- Final versus peak score was not tested in a play recording where points are lost.
- Whether 100/100 can be reached in Anchorhead was not checked. A command sequence that reaches 100 in the pinned game file would remove that part of the note. It would not change the outcome.

## Reproduce

- Review and pinned hashes: `evidence/reviews/_game-tasks-correctness.md`, sections 1-3.
- Session record: `git show earlier-audit-final:evidence/selected/three-adventure-native-release-acceptance.json`; replay timings: `git show earlier-audit-final:evidence/selected/trinity-tryst-terminal-acceptance.json`.
- Pinned harness sources: `sforge/harness/judge_server.py`, `sforge/harness/game_server_app.py`, `sforge/harness/selection.py`, `sforge/harness/score_rescale.py`.
