# NetHack Dungeon Agent (`nethack_dungeon_agent`)

**Decision:** Retain with note. Seeding silently fails, so the 20 evaluation games are random unseeded games and scores are not reproducible from run to run.

## What the task asks for

The solver writes `agent.py`, which "plays NetHack via the NLE Python environment and maximizes game score". The evaluator calls the solver's `get_action(obs, info, step)` each step. Its default evaluation is 10 seeds x 2 repeats (20 games). The prompt's local-testing skeleton shows `--max-steps 5000`; the evaluator also enforces a 120 s per-game limit, which the prompt does not state. Category: Interactive Games & Simulators.

## What goes wrong

**Seeding has no effect.** The evaluator calls `env.seed(seed)` on the object returned by `gym.make`. Under gymnasium 1.0 that object is a `PassiveEnvChecker` wrapper with no `seed` attribute, so the call raises `AttributeError`. The evaluator swallows the exception and calls `env.reset()` with no seed. (One level deeper, `env.unwrapped.seed` would raise an NLE `RuntimeError`, "NetHackChallenge doesn't allow seed changes", but the evaluator never reaches it.)

Example: the evaluator's "seed 0" start, run in 3 processes, gave 3 different games, each with a different starting role. Expected: the same game three times.

| Process | Start fingerprint | Starting inventory (first items) |
|---|---|---|
| 1 | `d032b1011fd60c20` | 1234 gold, blessed +0 scalpel (Healer) |
| 2 | `3075b9dff32a9560` | +0 battle-axe, short sword, ring mail (Barbarian-type kit) |
| 3 | `28304be1bd905af7` | +1 dagger, +1 bow, 52 arrows (Ranger-type kit) |

The original `--run-seed 0` child, run 3 times, returned WA/0, OK/2 and WA/0. Two full default evaluations of the same baseline gave different results:

| | Run 1 | Run 2 |
|---|---|---|
| Nonzero cases (case: score) | 0007: 3, 0010: 7, 0012: 2, 0018: 8 | 0009: 7, 0015: 4, 0018: 5 |
| All other cases | 0 (WA) | 0 (WA) |
| `TOTAL_SCORE` | **1.000000** | **0.800000** |
| `CASES_OK` | 4/20 | 3/20 |
| Normalized (linear, /1000 x 100) | 0.10 | 0.08 |
| Wall time | 5 s | 5 s |

The two "repeats" of the same seed (cases 2k and 2k+1) also disagree. For example, run 1 has case 0010 = 7 but case 0011 = 0. A repeat is just another random game.

Why it matters: the same agent can score differently on each evaluation, and the "10 seeds x 2 repeats" design does not hold.

The note that ships with the task:

- The 20 evaluation games are unseeded, with a random role each game. The "10 seeds x 2 repeats" are in effect 20 independent random games.
- Scores are not reproducible: two evaluations of the same baseline gave `TOTAL_SCORE` 1.000000 and 0.800000.
- The per-game limits are 5,000 steps (stated in the prompt as `--max-steps 5000`) and 120 s per game (not stated in the prompt).

## Impact

All solvers are affected by run-to-run variance. For the baseline, the difference is 0.2 raw points, or 0.02 normalized points, which is immaterial at that level. The variance for a competent agent was not measured. NetHack scores are heavy-tailed, so the spread for a scoring agent is likely much larger in absolute terms, but these runs cannot size it.

One baseline game took 0.37-0.44 s, including start-up, and each 20-game evaluation took about 5 s, far from the 120 s per-game limit. Whether a slower, planning agent hits that limit was not tested.

## Fix (v2)

No change; the note above ships with the task. A small evaluator repair could make the seeds meaningful, but no working seeding path in NLE 1.2 / `NetHackChallenge` was verified. `env.reset(seed=...)` did not raise, but it was not tested whether it actually seeds the NetHack core.

## How we know

- **Original evaluator in the pinned image.** `python3 /tmp/eval_nethack.py`, unmodified with default environment variables, ran in the judge image (`sha256:2917aca0e831…`) on an 8 vCPU, 7.9 GB host, with `--network none --memory 6g` and no CPU limit. The submission was the shipped baseline `agent.py` from the work image. Two full default evaluations were run, each wrapped in `timeout 1100`.
- **Seeding diagnostic.** A script calls `env.seed()` the same way the evaluator does and checks the wrapper chain. The evaluator's own `seed_process(0)` and `reset_env(env, 0)` ran in 3 separate processes, and the start state was fingerprinted (hash of `glyphs`, `blstats` and `inv_strs` at reset).
- Installed packages: `nle 1.2.0`, `gymnasium 1.0.0`, Python 3.10.

## Limits

- No model or solver runs. Effects are shown on the shipped baseline and authored diagnostics only.
- Only the shipped random-walk baseline was run. There is no competent-agent control, so the variance for a scoring agent is unmeasured.
- One host with no CPU limit. The timings apply to this host only.
- Start-state fingerprints hash `glyphs`, `blstats` and `inv_strs` at reset only.

## Reproduce

- `evidence/runs/nethack_dungeon_agent-native-variance/run.sh` (with `diag.py` and `evalpath_fp.py`). It needs a Docker host that can pull the pinned images. Outputs are in `result/out/` in the same folder.
- Review: `evidence/reviews/nethack_dungeon_agent-native.md`.
