# wesnoth_tactical_ai: native timing check (E2B)

## Question (decisive)

Can the default evaluation (3 maps x 10 seeds x 2 repeats = 60 games) finish within the task's
`eval_timeout` of 900 s? The earlier review concluded this was "likely OpenRCT2-class" (pending,
withhold if timing fails), based on an estimate that a game takes more than 15 s.

## Pinned artifacts

- Judge image: `seededge/edgebench.judge.wesnoth_tactical_ai@sha256:660e126eddcd91464431e83fdc0b432cea8f8e4e4d0a087d356e864460e154c8`
- Work image (baseline source): `seededge/edgebench.work.wesnoth_tactical_ai@sha256:4d9b1e6515b2ac2f00c22c3a2537127fd8b0c009cf5f93e747059b1555fe6a67`
- `/tmp/eval_wesnoth.py`: sha256 `b1cbe456fc1595c28cee023d9a4955fe5c7aa7e5a75151614dd69b83e5e16165`, measured in the container.
- Shipped baseline `my_custom_ai.cfg`: sha256 `66e11740789a158b67d33f56956e1714cb712adb68c34217ce58002709483e05`. It is the same file in the work and judge images, and it is the whole submission (`.git` excluded).
- Engine: Wesnoth 1.18.5. The user config/data directory is `/root/.config/wesnoth-1.18`, which matches the evaluator's `USER_DATA_DIR`, so the add-on install path resolves.

## Execution

- Containers: judge image, `--network none --memory 6g`, root, no CPU limit, on an 8-vCPU E2B worker.
- Job A: `evidence/runs/wesnoth_tactical_ai-native-timing/`, worker `i68x1yi3ijifyq5m9v9sc`. It exited 0 in 121 s and the worker was killed.
  - Step 1 (`game1.py`): imports the unmodified evaluator, calls `scan_for_hacks()` and `install_agent_ai()`, then calls the original `run_game(map, 0, 0)` once per map. It only wraps `subprocess.run` to record the raw engine output and the elapsed time.
  - Step 2: the exact `eval_cmd` (`python3 /tmp/eval_wesnoth.py`) with defaults, under `timeout 900`.
- Job B (control): `evidence/runs/wesnoth_tactical_ai-native-rca-control/`, worker `i659aq7z7n36oq2c6c95y`. It exited 0 in 201 s and the worker was killed.
  - Same evaluator. Side 1 uses Wesnoth's own stock `data/ai/ais/ai_default_rca.cfg`, with only `id=` renamed to `my_custom_ai`.
  - It passes the evaluator's hack scan.
  - The full default evaluation ran under `timeout 900`. `timed_eval.py` runs the unmodified evaluator via `runpy` with a timing shim on `subprocess.run`.
  - Purpose: measure game time when side 1 actually plays a full game, because the shipped baseline does not (see below).

## Results

**1. Shipped baseline: one original `run_game` per map** (`game1.jsonl`):

| Map | Wall time | `run_game` return | Markers in engine output |
|---|---|---|---|
| Weldyn_Channel | 2.08 s | (False, 8, False) | `WINNER: 2`, `GAME_END_TURN: 8` |
| The_Freelands | 1.40 s | (False, 6, False) | `WINNER: 2`, `GAME_END_TURN: 6` |
| Fallenstar_Lake | 1.42 s | (False, 9, False) | `WINNER: 2`, `GAME_END_TURN: 9` |

The engine does print both markers, through the `ai/testing` log domain at `info` level, and the evaluator's regexes parse them.

**2. Shipped baseline: full default evaluation** (`full_eval.txt`):

- It finished in **80 s** with exit 0.
- `TOTAL_SCORE 0`, `CASES_OK 0/60`, `TIMEOUT_COUNT 0`.
- Every game was lost, between turn 4 and turn 14.

**3. Why the baseline loses every game: its recruit CA does not exist in 1.18.5.** Every baseline game log contains:

```
error ai/engine/cpp: side 1 : UNKNOWN candidate_action[ai_default_rca::aspect_recruitment_phase]
```

- The stock 1.18 macro uses `name=default_recruitment::recruitment`.
- The baseline's side 1 therefore never recruits, and its leader is overrun.
- The prompt's "baseline ... typically scores 0-20" is technically met, since the score is 0. But the shipped starting point is broken on the pinned engine, which is a cosmetic or starter defect rather than a scoring defect.

**4. Control: stock default RCA as side 1, full default evaluation** (`rca_full_eval.txt`, `rca_games.jsonl`):

- It finished in **172 s** with exit 0: 60/60 games, `TIMEOUT_COUNT 0`, `TOTAL_SCORE 41` (18/60 wins).
- Per-game wall time:
  - Mean 2.86 s, median 2.79 s, maximum 5.65 s.
  - By map: Weldyn 2.54 s, Freelands 2.83 s, Fallenstar 3.20 s.
- Game lengths: the median end turns are close to the prompt's stated default-vs-default baselines (16/15/20). Two Freelands games reached the 50-turn cap and printed no `WINNER`; the evaluator scored them as losses.
- Repeat pairs (same map and `--rng-seed`, repeat 0 vs 1) were identical in only **1 of 30** pairs. For the shipped baseline, 6 of 30 were identical.

## What this establishes

- **The earlier timing concern is refuted on this host.** A full-length default-AI game takes about 3 s, not more than 15 s. The 60-game default evaluation took 172 s, against 900 s. The shipped baseline's evaluation took 80 s.
- **Headroom:** a submitted AI could spend about 5x the stock AI's time per game before hitting 900 s. It could spend about 15 s per game on average.
  - A heavy Lua AI could still exceed the budget. That cliff is undisclosed: the per-game limit is 180 s, but 60 x 15 s = 900 s.
  - This is a note-level caveat, not a defect for honest default-speed play.
- **New: the repeats are not repeatable.** A fixed `--rng-seed` does not fix the outcome of AI-vs-AI games here. The earlier statement "With a fixed seed, the 2 repeats are expected to be identical" is **false**. Scores therefore vary run to run, and the second repeat adds samples rather than wasting time.
  - The run-to-run variance of `TOTAL_SCORE` was not measured, because each configuration ran once.

## Recommended disposition

**Retain with a note.** This replaces "pending, withhold if timing fails". The note should cover three points:

- The shipped baseline's recruit CA name is invalid on Wesnoth 1.18.5, so the baseline scores 0.
- Games are not reproducible despite `--rng-seed`.
- The 60-game total must fit in 900 s, about 15 s per game on average.

Smallest starter fix: change the baseline's recruit CA to `name=default_recruitment::recruitment`, as in the stock macro. This fix is not tested here.

## Limits

- One 8-vCPU host with no CPU limit. A slower harness host could be several times slower and still fit 900 s.
- The control is Wesnoth's stock AI, not a submission. Each configuration ran one full evaluation, so there is no variance estimate.
- The Lua-in-subdirectory installation issue raised earlier was not exercised.
