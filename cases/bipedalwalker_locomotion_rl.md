# BipedalWalker Locomotion RL (`bipedalwalker_locomotion_rl`)

**Outcome:** Kept, with a note. <mark>The task caps its score at 30 by a design it states, so scores run from 0 to 30 out of 100, and a checkpoint that only partly matches the grader's network loads partly without an error.</mark>

## What the task asks

The prompt says: "Train a BipedalWalker policy on CPU in this work container and save the final trained checkpoint as `submission/policy.pth`." BipedalWalker is a simulated two-legged robot. A policy is the trained network that chooses its moves, and a checkpoint is the file that stores the network's weights. The grader "only receives the submitted checkpoint and evaluates it on BipedalWalker-v3 and BipedalWalkerHardcore-v3." The work container's `task_prompt.md` states the cap of 30 (lines 117-118). The task is in the Scientific Problems & ML category.

## What goes wrong

By a design the task states, the highest reachable score is 30 out of 100. The grader computes the score in steps:

- Normal-ground reward R_normal scores `clip(R_normal/300) × 100`.
- Rough-ground ("hardcore") reward R_hard scores `clip((R_hard+100)/400) × 100`.
- The raw result (before conversion to 0–100) is `raw = 0.4·normal + 0.6·hard`.
- The task score is `min(30, 2.5·(engineering checks passed, max 4) + 0.2·raw)`.

The score scale is linear from 0 to 100, so the task score becomes the same number out of 100.

| Case | Mean rewards assumed (R_normal, R_hard) | Score out of 100 |
|---|---|---|
| Missing checkpoint | not evaluated (−200, −200) | 2.5 |
| Loadable but untrained | ≤ 0 and ≤ −100 | **10** |
| Solves normal ground only | 300, −100 | 18 |
| **Perfect policy** | ≥ 300, ≥ 300 | **30** |

The rows for loadable checkpoints assume all four engineering checks pass. An untrained policy that does not fall on rough ground has R_hard > −100 and scores above 10. R_hard = −60, for example, gives a hardcore score of 10, raw 6 and a task score of 11.2. This repository records no mean rewards of an untrained policy.

Only 0 to 30 of the 0-100 range can be reached, and a third of that comes from passing the loading checks. No policy can reach the reference point for 100. The task states the cap, so we treat it as a note and not as a defect.

A smaller issue is that a checkpoint can load partly without an error. Every path where the grader loads the weights itself uses `load_state_dict(strict=False)` (`evaluate_policy.py:119,141,196`); with a `load_policy(path)` hook the solver's own code loads them. The default path also drops, without an error, any weight tensor whose shape does not match (`:188-196`).

- Suppose a checkpoint from a good-faith solver has renamed keys, such as a `module.` prefix. A solver would expect it either to load or to fail. The original grader would score it as a randomly initialized network, and it would still collect the points for loading. The grader discards the evaluator's "Skipping" message, because `sebench_eval.py` keeps the child process's output only when it exits with an error (`:109-113`) and on success reads only `mean_reward` (`:114-118`). The feedback therefore says nothing about partial loading.

We checked the episode runs and found them correct. The grader runs ten episodes per environment on the first 10 fixed seeds, about 36k steps in total, which takes seconds against limits of 300 s per environment and `eval_timeout` 900 s. The seeds are fixed and the actions are deterministic, so we expect results to repeat bit for bit on the same build.

The note says:

- Scores run from 0 to 30, not 0 to 100.
- 10 of those points come from loading checks.
- Checkpoints with mismatched keys or shapes load partly without an error.

## How much it matters

- The cap is by design. It limits every solver to 30 points out of 100.
- Partial loading affects only solvers whose checkpoint keys or shapes do not match the grader's network. Such a checkpoint scores like an untrained network (about 10 with all checks passed).

There is no code change. The note above ships with the task.

## How we checked it

- We read copies of `sebench_eval.py` (sha256 `9bb2f8bf…838a`), `eval/evaluate_policy.py` (`43105357…7b68`) and `task_prompt.md` (`e4023718…adcf`) taken from the task's source files, the original grader source. We computed the scores in the table above with the original scoring functions. We did not record which image these copies came from, or the digest of the grader image. The task prompt says "Hidden evaluator code is not present in this work container"; we did not check whether the work image contains `sebench_eval.py`.
- On the original grader we ran 20 episodes with a policy that always outputs zero (overlaid on the network). The results are consistent with deterministic scoring.

## Limits

- We ran no AI model or solver. The effects shown come only from test submissions and counterexamples we wrote.
- We scored no trained policy on the grader. We checked the mapping from reward to score from the source and by arithmetic, not on a trained checkpoint.
- We reasoned the renamed-key example from the source and did not run it.
- This repository does not publish the copies of `sebench_eval.py`, `evaluate_policy.py` and `task_prompt.md` that we read, so the quoted lines (including the cap in `task_prompt.md` lines 117-118) can be checked only against the task images, by the sha256 values above.

## Reproduce

- Review: `evidence/reviews/_game-tasks-correctness.md`, section 10.
- Grader source copies (not published): `sebench_eval.py` and `eval/evaluate_policy.py`, identified by the sha256 values above and in the review.
- Formal check: `evidence/formal/notes/bipedalwalker_locomotion_rl.md` (Lean 4; the score formula only, not the simulation).
