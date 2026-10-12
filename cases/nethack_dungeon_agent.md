# NetHack Dungeon Agent (`nethack_dungeon_agent`)

Status: reviewed by the coordinator, 2026-10-12

- **Domain:** Interactive Games & Simulators
- **Decision:** Retain with note — seeding silently fails, so the 20 evaluation games are random unseeded games and scores are not reproducible run to run.

## What the task promises

The solver writes `agent.py`, which "plays NetHack via the NLE Python environment and maximizes game score". The evaluator calls the solver's `get_action(obs, info, step)` each step. Its default evaluation is 10 seeds x 2 repeats (20 games). The prompt's local-testing skeleton shows `--max-steps 5000`; the evaluator also enforces a 120 s per-game limit, which the prompt does not state.

## What we checked and how

- Native run of the original evaluator (`python3 /tmp/eval_nethack.py`, unmodified, default environment variables) in the pinned judge image on one E2B worker (8 vCPU, 7.9 GB). The container ran with `--network none --memory 6g` and no CPU limit. The submission was the shipped baseline `agent.py` copied from the work image.
- A diagnostic that calls `env.seed()` the same way the evaluator does, and checks the wrapper chain.
- The evaluator's own `seed_process(0)` and `reset_env(env, 0)` run in 3 separate processes, with the start state fingerprinted (hash of `glyphs`, `blstats` and `inv_strs` at reset).
- Two full default evaluations of the baseline, each wrapped in `timeout 1100`.
- Installed packages: `nle 1.2.0`, `gymnasium 1.0.0`, Python 3.10.
- Original identity: judge image `seededge/edgebench.judge.nethack_dungeon_agent@sha256:2917aca0e831…`; work image `seededge/edgebench.work.nethack_dungeon_agent@sha256:6adeba51c22d…`; key files `eval_nethack.py` sha256 `5bd47b4f4eea…` (measured in the container; matches the extracted copy), baseline `agent.py` sha256 `0692d3198547…`.

## What we found

**Confirmed: seeding is ineffective, so scores are not reproducible.**

- The evaluator calls `env.seed(seed)` on the object returned by `gym.make`. Under gymnasium 1.0 that object is a `PassiveEnvChecker` wrapper with no `seed` attribute, so the call raises `AttributeError`. The evaluator swallows the exception and calls `env.reset()` with no seed.
- An earlier review cited a different exception, an NLE `RuntimeError` ("NetHackChallenge doesn't allow seed changes"). That error is raised one level deeper, by `env.unwrapped.seed`, which the evaluator never reaches. The conclusion is the same; only the mechanism differs.
- Example: the evaluator's "seed 0" start, run in 3 processes, gave 3 different games, each with a different starting role:

| Process | Start fingerprint | Starting inventory (first items) |
|---|---|---|
| 1 | `d032b1011fd60c20` | 1234 gold, blessed +0 scalpel (Healer) |
| 2 | `3075b9dff32a9560` | +0 battle-axe, short sword, ring mail (Barbarian-type kit) |
| 3 | `28304be1bd905af7` | +1 dagger, +1 bow, 52 arrows (Ranger-type kit) |

- The original `--run-seed 0` child, run 3 times, returned WA/0, OK/2 and WA/0.
- Two full default evaluations of the same baseline gave different results:

| | Run 1 | Run 2 |
|---|---|---|
| Nonzero cases (case: score) | 0007: 3, 0010: 7, 0012: 2, 0018: 8 | 0009: 7, 0015: 4, 0018: 5 |
| All other cases | 0 (WA) | 0 (WA) |
| `TOTAL_SCORE` | **1.000000** | **0.800000** |
| `CASES_OK` | 4/20 | 3/20 |
| Normalized (linear, /1000 x 100) | 0.10 | 0.08 |
| Wall time | 5 s | 5 s |

- The two "repeats" of the same seed (cases 2k and 2k+1) also disagree. For example, run 1 has case 0010 = 7 but case 0011 = 0. A repeat is just another random game.
- **Size:** for the baseline, the run-to-run difference is 0.2 raw points, or 0.02 normalized points, which is immaterial at that level. The variance for a competent agent was not measured. NetHack scores are heavy-tailed, so the spread for a scoring agent is likely much larger in absolute terms, but these runs cannot size it.

**Timing.** One baseline game took 0.37-0.44 s, including start-up, and each 20-game evaluation took about 5 s. The baseline is far from the 120 s per-game limit. This run does not test that limit for a slower, planning agent.

## Note for users

No repair. The note says:

- The 20 evaluation games are unseeded, with a random role each game. The "10 seeds x 2 repeats" are in effect 20 independent random games.
- Scores are not reproducible: two evaluations of the same baseline gave `TOTAL_SCORE` 1.000000 and 0.800000.
- The per-game limits are 5,000 steps (stated in the prompt as `--max-steps 5000`) and 120 s per game (not stated in the prompt).[^1]

A small evaluator repair could make the seeds meaningful, but no working seeding path in NLE 1.2 / `NetHackChallenge` was verified. `env.reset(seed=...)` did not raise, but the review did not test whether it actually seeds the NetHack core.

## Limits and what was not run

- No model or solver re-runs. Effects are shown on the shipped baseline and authored diagnostics only.
- Only the shipped random-walk baseline was run. There is no positive-competence control, so the variance for a scoring agent is unmeasured.
- One worker with no CPU limit. The timings apply to this host only.
- Start-state fingerprints hash `glyphs`, `blstats` and `inv_strs` at reset only.

## Reproduce

- `evidence/runs/nethack_dungeon_agent-native-variance/run.sh` (with `diag.py` and `evalpath_fp.py`). It needs a Docker host that can pull the pinned images. Outputs from our run are in `result/out/` in the same folder.
- Review: `evidence/reviews/nethack_dungeon_agent-native.md`.

[^1]: Coordinator resolution: the prompt states `--max-steps 5000`; the undisclosed part is the 120 s per-game limit. `decisions.json` now reads "120 s per-game limit not stated in the prompt".
