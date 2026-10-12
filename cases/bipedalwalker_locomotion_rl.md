# BipedalWalker Locomotion RL (`bipedalwalker_locomotion_rl`)

**Decision:** Retain with note. The task score is capped at 30 by disclosed design, so the normalized range is 0-30, and partial checkpoint loading is silent.

## What the task asks for

"Train a BipedalWalker policy on CPU in this work container and save the final trained checkpoint as `submission/policy.pth`." The judge "only receives the submitted checkpoint and evaluates it on BipedalWalker-v3 and BipedalWalkerHardcore-v3." The cap of 30 is disclosed in the work container's `task_prompt.md` (lines 117-118). Category: Scientific Problems & ML.

## What goes wrong

**Normalized ceiling is 30 (disclosed design).** Normal reward scores `clip(R_normal/300) × 100`, hardcore scores `clip((R_hard+100)/400) × 100`, and `raw = 0.4·normal + 0.6·hard`. The task score is `min(30, 2.5·(engineering checks passed, max 4) + 0.2·raw)`. The rescale is linear from 0 to 100, so the task score maps to the same number.

| Case | Normalized |
|---|---|
| Missing checkpoint | 2.5 |
| Loadable but untrained | **10** |
| Solves normal only (300, −100) | 18 |
| **Perfect policy** | **30** |

Only 0 to 30 of the 0-100 range is reachable, and a third of that comes from passing the loading checks. The upper anchor of 100 is inconsistent with what any policy can reach. The cap is disclosed, so this is a note rather than a defect.

**Silent partial checkpoint loading (minor).** Every loader path uses `load_state_dict(strict=False)`, and the default path silently drops mismatched-shape tensors.
- Example: an honest checkpoint with renamed keys (for example a `module.` prefix) is expected to load or fail. Under the original evaluator it would be evaluated as a randomly initialized network while still collecting the loading bonus. The "Skipping" message appears only in aggregate feedback.

Checked and found correct: ten episodes per environment on the first 10 fixed seeds, about 36k steps in total. This takes seconds against 300 s per environment and `eval_timeout` 900 s. Seeds are fixed and the action is deterministic, so results are expected to be bit-reproducible on the same build.

The note says:
- The normalized range is 0-30, not 0-100.
- 10 of those points come from loadability checks.
- Checkpoints with mismatched keys or shapes load partially without an error.

## Impact

- Ceiling: by design. Every solver is limited to 30 normalized points.
- Partial loading: affects only solvers whose checkpoint keys or shapes do not match the evaluator's network. Such a checkpoint scores as an untrained network plus the loading bonus.

## Fix (v2)

No change; the note above ships with the task.

## How we know

- **Original evaluator source.** We read the pinned `sebench_eval.py`, `eval/evaluate_policy.py` and `task_prompt.md`. The normalized values above were computed with the original scoring functions. The judge image digest is not recorded.
- **Native episodes.** 20 episodes with a zero-policy overlay are consistent with deterministic scoring.

## Limits

- No model or solver runs. Effects are shown only on authored controls and counterexamples.
- No trained policy was evaluated natively, so the reward-to-score mapping was checked from source and arithmetic, not on a trained checkpoint.
- The renamed-key example was reasoned from source; it was not run.

## Reproduce

- Review: `evidence/reviews/_game-tasks-correctness.md`, section 10.
- Pinned evaluator copies: the judge image file `sebench_eval.py` (cited by sha256 in the review), the judge image file `evaluate_policy.py` (cited by sha256 in the review).
