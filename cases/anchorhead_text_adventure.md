# Anchorhead (`anchorhead_text_adventure`)

**Outcome:** Kept, with a note. <mark>The score is the game's own score, which is the same every time for the same commands. The note covers two things the task does not state, final-versus-peak scoring and session limits.</mark>

## What the task asks

The prompt says: "Play the interactive fiction game *Anchorhead* by sending commands via an HTTP API and maximize your score." Interactive fiction is a text adventure, in which the player types commands and the game replies in text. The prompt states no time horizon, step cap or number of games. The task is in the Interactive Games & Simulators category.

EdgeBench gives an AI agent the task, and the agent works for up to 12 hours. A hidden grader program scores the result. Its raw result is the score before conversion to 0–100. Reference points chosen by the task authors convert it to a score out of 100.

## What we checked

We found no scoring problem. We checked the parts below and found them correct.

The grader defines the score as follows. At each step it reads `env.get_score()` from the memory of the Z-machine, the virtual machine that runs the game. A session can end in four ways. The game finishes, the agent closes it, the harness closes it after it sits idle, or the harness evicts it to make room for a newer session. When a session ends, the grader stores the *final* score of that session, and the run's score is the highest final score over all its sessions. The score scale is linear. Its reference point for 0 is the start score, and its reference point for 100 is 100, which equals Jericho's `max_score` for this game (`anchor.c:84-86`). Jericho is the library that runs the game. The task ships no baseline reference point. A replay of the walkthrough scored 99/100, so 99 out of 100 on the scale.

The game is repeatable. The harness calls `FrotzEnv(rom)` with no seed, so the library falls back to its default seed, which is 0, and the game's random number source does not depend on the clock. A given sequence of commands plays exactly the same way every time.

We have three notes.

The grader stores the final score, not the peak score. The API also returns a `peak_score`, which could lead an agent to think the peak counts. The difference shows only if a player can lose points during play. In all three supplied play recordings (Anchorhead, Trinity, Tryst), the final score equalled the peak.

The harness enforces three session limits that the prompt does not state:

- a 10 s HTTP timeout per step;
- at most 3 sessions at once per run (the harness evicts the oldest);
- closing a session after 600 to 660 s idle (the idle check runs every 60 s, `judge_server.py:156,159`).

Closing and eviction both store the current score once the harness has removed the session's game container, so no score is lost. If the removal fails, the harness keeps the session, retries at the next idle check, and stores its score only after a removal succeeds (`judge_server.py:226-239`). An agent that pauses for more than 10 minutes in the middle of a game loses the live game and must replay it. Replay is cheap. Recorded HTTP replays of the full Trinity (610 commands) and Tryst (518 commands) walkthroughs took 29 s and 32 s.

The task does not show that the full score can be reached. The supplied reference walkthrough ends at 99 with game_over=true and victory=false, and we did not verify whether 100/100 can be reached in the pinned game file.

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

- We read the pinned sources of the original grader for each part of scoring:
  - reading the score at each step (`game_server_app.py`);
  - storing session scores and enforcing session limits (`judge_server.py`);
  - keeping the best of all sessions (`selection.py`);
  - the validity check (`grading.py`);
  - converting to the score scale (`score_rescale.py`).

  The repository copies match the hash-pinned copies byte for byte. The digest of the grader image is not recorded.
- We ran six sessions on the host through this repository's copy of EdgeBench's harness (`JudgeState` with the Docker backend). Its grading and selection files were then the earlier audit's modified version, but the session scores reported here come from the game server and do not depend on them. The game containers were built from the original game files (built image id `sha256:a197e54f…`); the digest of the public grader image is not recorded. For each of Anchorhead, Trinity and Tryst we ran one full walkthrough replay and one 25-command partial replay, and each partial replay's scores matched the first 25 steps of the full replay. The Anchorhead walkthrough (531 commands) scored 99/100.
- We read the score source, `max_score` and the default seed from the public Jericho 3.3.1 source package (sdist), the upstream game-engine source.

## Limits

- We ran no AI model or solver. The effects shown come only from the walkthrough sessions.
- Anchorhead's repeatability rests on one partial replay compared with one full replay over 25 steps, plus Jericho's fixed default seed.
- Jericho's behaviour comes from the upstream 3.3.1 source. We did not hash the installed files in the image.
- We did not test final versus peak score in a play recording where points are lost.
- We did not check whether 100/100 can be reached in Anchorhead. A command sequence that reaches 100 in the pinned game file would remove that part of the note, but it would not change the outcome.

## Reproduce

- Review and pinned hashes: `evidence/reviews/_game-tasks-correctness.md`, sections 1-3.
- Session record: `git show earlier-audit-final:evidence/selected/three-adventure-native-release-acceptance.json`; replay timings: `git show earlier-audit-final:evidence/selected/trinity-tryst-terminal-acceptance.json`.
- Pinned harness sources: `sforge/harness/judge_server.py`, `sforge/harness/game_server_app.py`, `sforge/harness/selection.py`, `sforge/harness/score_rescale.py`.
