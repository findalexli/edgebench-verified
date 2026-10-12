# nethack_dungeon_agent: native run-to-run check (E2B)

## Question

The default evaluation is described as "10 seeds x 2 repeats", but seeding was thought not to work.
Does it? How far apart are two default evaluations of the shipped baseline agent?
Does `env.seed()` raise in the installed NLE?

## Pinned artifacts

- Judge image: `seededge/edgebench.judge.nethack_dungeon_agent@sha256:2917aca0e831dd91e88d8c40a453b73d0080230cdf4d9824291b0b601c08f1e0`
- Work image (source of the baseline submission): `seededge/edgebench.work.nethack_dungeon_agent@sha256:6adeba51c22d1bbc412a4d7926428424cdf467cd4f6f897d90b623ca1587c9cd`
- `/tmp/eval_nethack.py`: sha256 `5bd47b4f4eea5d15b4033a1a11d4fde1eede800af5e61d4aa4468d6fd4514787`. This is the hash measured inside the container, and it matches the extracted copy.
- Baseline `agent.py`, copied from the work image: sha256 `0692d3198547ee2aaa568e1b52d8c0e535719adf99fa46f0d18aaea4ba3bffd2`.
- Installed packages: `nle 1.2.0`, `gymnasium 1.0.0`, Python 3.10.

## Execution

- Job: `evidence/runs/nethack_dungeon_agent-native-variance/` (files: `run.sh`, `diag.py`, `evalpath_fp.py`).
- Worker: E2B sandbox `iuyfxphzvpgzslfhs1t1w` (template `harbor-worker-v4`, 8 vCPU, 7.9 GB). It ran for 41 s, exited 0 and was killed (`result/worker.json`).
- Container setup: the judge image run with `--network none --memory 6g` as root, with the work image's `agent.py` copied to `/home/nethack_agent/`.
- Evaluation command: the exact `python3 /tmp/eval_nethack.py`, unmodified, with default environment variables (10 seeds x 2 repeats, 5,000 steps, 120 s per game). Each of the two runs was wrapped in `timeout 1100`.
- Outputs are in `result/out/`.

## Results

**1. `env.seed()` raises, but not with the exception the earlier review cited** (`diag_seed.txt`):

```
wrapper chain: PassiveEnvChecker -> NetHackChallenge
env.seed (as evaluator calls it) : RAISED AttributeError - 'PassiveEnvChecker' object has no attribute 'seed'
env.unwrapped.seed : RAISED RuntimeError - NetHackChallenge doesn't allow seed changes
env.reset(seed=1729): no error
```

- The evaluator calls `env.seed(seed)` on the object returned by `gym.make`. Under gymnasium 1.0 that object is a wrapper with no `seed` attribute, so the call raises `AttributeError`. The NLE `RuntimeError` cited by the earlier review is raised one level deeper, by `env.unwrapped.seed`, which the evaluator never reaches.
- Either way, `reset_env` swallows the exception and calls `env.reset()` with no seed. The conclusion is unchanged; only the mechanism differs.
- `env.reset(seed=...)` did not raise, but this check did not test whether it actually seeds the NetHack core.

**2. The same "seed" gives a different game each time.** I ran the evaluator's own `seed_process(0)` and `reset_env(env, 0)` in 3 separate processes (`evalpath_fp.txt`). Each start state differs, including the starting role:

| Process | Start fingerprint | Starting inventory (first items) |
|---|---|---|
| 1 | `d032b1011fd60c20` | 1234 gold, blessed +0 scalpel (Healer) |
| 2 | `3075b9dff32a9560` | +0 battle-axe, short sword, ring mail (Barbarian-type kit) |
| 3 | `28304be1bd905af7` | +1 dagger, +1 bow, 52 arrows (Ranger-type kit) |

The original `--run-seed 0` child, run 3 times (`single_game_timing.txt`), returned WA/0, OK/2 and WA/0.

**3. Two full default evaluations of the baseline give different per-game lists and different totals** (`full_eval_run1.txt`, `full_eval_run2.txt`):

| | Run 1 | Run 2 |
|---|---|---|
| Nonzero cases (case: score) | 0007: 3, 0010: 7, 0012: 2, 0018: 8 | 0009: 7, 0015: 4, 0018: 5 |
| All other cases | 0 (WA) | 0 (WA) |
| `TOTAL_SCORE` | **1.000000** | **0.800000** |
| `CASES_OK` | 4/20 | 3/20 |
| Normalized (linear, /1000 x 100) | 0.10 | 0.08 |
| Wall time | 5 s | 5 s |

- The two repeats of the same seed (cases 2k and 2k+1) also disagree. For example, run 1 has case 0010 = 7 but case 0011 = 0.
- This confirms that a "repeat" is just another random game.

**4. Time.**

- One baseline game took 0.37-0.44 s, including Python and NLE start-up.
- Each 20-game evaluation took about 5 s.
- The baseline is far from the 120 s per-game TLE cliff. This run does not test the cliff for a slower, planning agent.

## What this establishes

- **Confirmed natively:** seeding is ineffective. Scores are not reproducible run to run, and the "repeats" are independent games. The mechanism in this image is `AttributeError` from the gymnasium wrapper, not the NLE `RuntimeError`.
- **Size for the baseline:** the run-to-run difference is 0.2 raw points, or 0.02 normalized points. That is immaterial at the baseline's level.
- **Not established:** variance for a competent agent. NetHack scores are heavy-tailed, so the spread of a 20-game mean for a scoring agent is likely much larger in absolute terms. These two baseline runs cannot size it.

## Recommended disposition

**Retain with a note.** The note should say three things:

- The 20 games are unseeded, with a random role each game.
- The two scores above illustrate that scores are not reproducible.
- The per-game limits are 5,000 steps and 120 s.

A small evaluator repair would make the "seeds" meaningful, but no working seeding path in NLE 1.2 / `NetHackChallenge` was verified here.

## Limits

- Only the shipped random-walk baseline was run, so there is no positive-competence control.
- This is a single worker with no CPU limit. The timing is for this host only.
- Start-state fingerprints hash `glyphs`, `blstats` and `inv_strs` at reset only.
