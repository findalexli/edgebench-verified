# NetHack Dungeon Agent (`nethack_dungeon_agent`)

**Outcome:** Kept, with a note. <mark>The grader's call that should fix each game's random seed silently fails, so the 20 graded games are random and scores are not repeatable from run to run.</mark>

## What the task asks

The agent writes `agent.py`, which "plays NetHack via the NLE Python environment and maximizes game score". NetHack is a classic text-based dungeon game, and NLE (the NetHack Learning Environment) wraps it for programs. The grader calls the agent's `get_action(obs, info, step)` at each step.

By default the grader plays 10 seeds x 2 repeats (20 games). A seed is the number that should fix a game's random layout. The grader stops each game after 5,000 steps; the prompt shows 5,000 only as the default of `--max-steps` in its local-testing skeleton, not as the grader's limit. The grader also enforces a 120 s per-game limit, which the prompt does not state. Category: Interactive Games & Simulators.

## What we checked

**Seeding has no effect.** The grader calls `env.seed(seed)` on the object returned by `gym.make`. Under gymnasium 1.0 that object is a `PassiveEnvChecker` wrapper with no `seed` attribute, so the call raises `AttributeError`. The grader swallows the error and calls `env.reset()` with no seed. (One level deeper, `env.unwrapped.seed` would raise an NLE `RuntimeError`, "NetHackChallenge doesn't allow seed changes", but the grader never reaches it.)

Example: the grader's "seed 0" start, run in 3 processes, gave 3 different games, each with a different starting role (character class). Expected: the same game three times.

| Process | Start fingerprint | Starting inventory (first items) |
|---|---|---|
| 1 | `d032b1011fd60c20` | 1234 gold, blessed +0 scalpel (Healer) |
| 2 | `3075b9dff32a9560` | +0 battle-axe, short sword, ring mail (Barbarian-type kit) |
| 3 | `28304be1bd905af7` | +1 dagger, +1 bow, 52 arrows (Ranger-type kit) |

The original `--run-seed 0` child process, run 3 times, returned WA/0, OK/2 and WA/0. Two full default gradings of the same baseline gave different results:

| | Run 1 | Run 2 |
|---|---|---|
| Nonzero cases (case: score) | 0007: 3, 0010: 7, 0012: 2, 0018: 8 | 0009: 7, 0015: 4, 0018: 5 |
| All other cases | 0 (WA) | 0 (WA) |
| `TOTAL_SCORE` | **1.000000** | **0.800000** |
| `CASES_OK` | 4/20 | 3/20 |
| Score out of 100 (linear scale, raw result /1000 x 100) | 0.10 | 0.08 |
| Wall time | 5 s | 5 s |

The two "repeats" of the same seed (cases 2k and 2k+1) also disagree. For example, run 1 has case 0010 = 7 but case 0011 = 0. A repeat is just another random game.

As a result, the same agent can score differently on each grading, and the "10 seeds x 2 repeats" design does not hold.

The note that ships with the task:

- The 20 graded games are unseeded, with a random role each game. The "10 seeds x 2 repeats" are in effect 20 independent random games.
- Scores are not repeatable: two gradings of the same baseline gave `TOTAL_SCORE` 1.000000 and 0.800000.
- The per-game limits are 5,000 steps (shown in the prompt only as the default of `--max-steps` in the local-testing skeleton) and 120 s per game (not stated in the prompt). A game that runs past 120 s scores 0, including any points it had already earned: the grader's `run_seed_subprocess` returns `TLE` with score 0 on `TimeoutExpired`, and the game reports its best score only when it finishes. 120 s over 5,000 steps is 24 ms per step, including NLE's own stepping.

## How much it matters

Run-to-run variation affects all solvers. For the baseline, the difference is 0.2 raw points, or 0.02 points out of 100, which does not matter at that level. The variation for a competent agent was not measured, so its size at that level is unknown. Recorded agent runs on this task score up to 41.9 out of 100 (`tasks/README.md`), far above the baseline. NetHack scores are heavy-tailed (a few games score far more than the rest), so the spread at that level is likely much larger in absolute terms, but these runs cannot size it. The task's selection rule (`score_first`) keeps the best submission, so random variation between gradings can raise a run's recorded best.

One baseline game took 0.37-0.44 s, including start-up, and each 20-game grading took about 5 s. That is far from the 120 s per-game limit. An agent that averages more than about 24 ms per step over a full 5,000-step game hits the limit and scores 0 for that game. Whether a slower, planning agent hits that limit was not tested.

The task does not change; the note above ships with it. A small grader fix could make the seeds meaningful, but no working seeding path in NLE 1.2 / `NetHackChallenge` was verified. `env.reset(seed=...)` did not raise an error, but it was not tested whether it actually seeds the NetHack core.

## How we checked it

- **Original grader.** `python3 /tmp/eval_nethack.py`, unmodified with default environment variables, ran in the original public image, pinned by digest. The machine had 8 vCPU and 7.9 GB, and the container ran with `--network none --memory 6g` and no CPU limit. The submission was the shipped baseline `agent.py` from the agent's working image. Two full default gradings were run, each wrapped in `timeout 1100`.
- **Seeding diagnostic.** A script calls `env.seed()` the same way the grader does and checks the chain of wrappers. The grader's own `seed_process(0)` and `reset_env(env, 0)` ran in 3 separate processes. The start state was fingerprinted (hash of `glyphs`, `blstats` and `inv_strs` at reset).
- Installed packages: `nle 1.2.0`, `gymnasium 1.0.0`, Python 3.10.

## Limits

- No AI model or solver was run. Effects are shown only on the shipped baseline and diagnostics we wrote.
- Only the shipped random-walk baseline was run. There is no competent agent to compare, so the variation for a scoring agent is unmeasured, and so is the size of that variation.
- One machine with no CPU limit was used. The timings apply to this machine only.
- Start-state fingerprints hash `glyphs`, `blstats` and `inv_strs` at reset only.

## Reproduce

- Original grader image: `sha256:2917aca0e831…`.
- `evidence/runs/nethack_dungeon_agent-native-variance/run.sh` (with `diag.py` and `evalpath_fp.py`). It needs a Docker host that can pull the pinned images. Outputs are in `result/out/` in the same folder.
- Review: `evidence/reviews/nethack_dungeon_agent-native.md`.
