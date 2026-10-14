# BipedalWalker Locomotion RL (`bipedalwalker_locomotion_rl`)

**Outcome:** Kept, with a note. <mark>The task caps its score at 30 by a design it states, so scores run from 0 to 30 out of 100, and a checkpoint that only partly matches the grader's network loads partly without an error.</mark>

## What the task asks

The prompt says: "Train a BipedalWalker policy on CPU in this work container and save the final trained checkpoint as `submission/policy.pth`." BipedalWalker is a simulated two-legged robot. A policy is the trained network that chooses its moves, and a checkpoint is the file that stores the network's weights. The grader "only receives the submitted checkpoint and evaluates it on BipedalWalker-v3 and BipedalWalkerHardcore-v3." The cap of 30 is stated in the work container's `task_prompt.md` (lines 117-118). Category: Scientific Problems & ML.

## What goes wrong

**The highest reachable score is 30 out of 100 (stated design).** The grader computes the score in steps:

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

The rows for loadable checkpoints assume all four engineering checks pass. An untrained policy that does not fall on rough ground has R_hard > −100 and scores above 10: for example R_hard = −60 gives a hardcore score of 10, raw 6 and a task score of 11.2. No mean rewards of an untrained policy are recorded in this repository.

Only 0 to 30 of the 0-100 range can be reached, and a third of that comes from passing the loading checks. The reference point for 100 does not match anything a policy can reach. The cap is stated in the task, so this is a note rather than a defect.

**A checkpoint can load partly without an error (minor).** Every path where the grader loads the weights itself uses `load_state_dict(strict=False)` (`evaluate_policy.py:119,141,196`); with a `load_policy(path)` hook the solver's own code loads them. The default path also drops, without an error, any weight tensor whose shape does not match (`:188-196`).

- Example: a checkpoint from a good-faith solver has renamed keys, for example a `module.` prefix. One would expect it either to load or to fail. Under the original grader it would be scored as a randomly initialized network, while still collecting the points for loading. The evaluator's "Skipping" message is discarded: `sebench_eval.py` keeps the child process's output only when it exits with an error (`:109-113`), and on success it reads only `mean_reward` (`:114-118`). Partial loading is therefore silent in the feedback.

Checked and found correct: the grader runs ten episodes per environment on the first 10 fixed seeds, about 36k steps in total. This takes seconds, against limits of 300 s per environment and `eval_timeout` 900 s. The seeds are fixed and the actions are deterministic, so results are expected to repeat bit for bit on the same build.

The note says:

- Scores run from 0 to 30, not 0 to 100.
- 10 of those points come from loading checks.
- Checkpoints with mismatched keys or shapes load partly without an error.

## How much it matters

- The cap: by design. Every solver is limited to 30 points out of 100.
- Partial loading: affects only solvers whose checkpoint keys or shapes do not match the grader's network. Such a checkpoint scores like an untrained network (about 10 with all checks passed).

There is no code change. The note above ships with the task.

## How we checked it

- **Original grader source.** We read copies of `sebench_eval.py` (sha256 `9bb2f8bf…838a`), `eval/evaluate_policy.py` (`43105357…7b68`) and `task_prompt.md` (`e4023718…adcf`) taken from the task's source files. The scores in the table above were computed with the original scoring functions. Which image these copies were taken from, and the digest of the grader image, are not recorded. The task prompt says "Hidden evaluator code is not present in this work container"; whether the work image contains `sebench_eval.py` was not checked.
- **Episodes run on the original grader.** 20 episodes with a policy that always outputs zero (overlaid on the network) are consistent with deterministic scoring.

## Limits

- No AI model or solver was run. Effects are shown only on test submissions and counterexamples we wrote.
- No trained policy was scored on the grader. The mapping from reward to score was checked from the source and by arithmetic, not on a trained checkpoint.
- The renamed-key example was reasoned from the source. It was not run.
- The copies of `sebench_eval.py`, `evaluate_policy.py` and `task_prompt.md` that were read are not published in this repository, so the quoted lines (including the cap in `task_prompt.md` lines 117-118) can be checked only against the task images, by the sha256 values above.

## Reproduce

- Review: `evidence/reviews/_game-tasks-correctness.md`, section 10.
- Grader source copies (not published): `sebench_eval.py` and `eval/evaluate_policy.py`, identified by the sha256 values above and in the review.
- Formal check: `evidence/formal/notes/bipedalwalker_locomotion_rl.md` (Lean 4; the score formula only, not the simulation).
