# BipedalWalker Locomotion RL (`bipedalwalker_locomotion_rl`)

Status: reviewed by the coordinator, 2026-10-12

- **Domain:** Scientific Problems & ML
- **Decision:** Retain with note — the task score is capped at 30 by disclosed design, so the
  normalized range is 0-30; partial checkpoint loading is silent.

## What the task promises

"Train a BipedalWalker policy on CPU in this work container and save the final trained checkpoint
as `submission/policy.pth`." The judge "only receives the submitted checkpoint and evaluates it on
BipedalWalker-v3 and BipedalWalkerHardcore-v3." The cap of 30 is disclosed in the work container's
`task_prompt.md` (lines 117-118).

## What we checked and how

- Source reading of the pinned `sebench_eval.py` and `eval/evaluate_policy.py`, and of
  `task_prompt.md`.
- The normalized values below were computed with the original scoring functions.
- Reuse of earlier accepted native results: 20 episodes with a zero-policy overlay. No episode was
  rerun for this review.
- Original identity: judge image digest not recorded in the review; task JSON sha256
  `48c3ebf72861e30c116494df5258c278454fd503caba16de9adf971c1bc03ecb`; `sebench_eval.py` sha256
  `9bb2f8bf…838a`; `evaluate_policy.py` sha256 `431053573adce4dd51a647171b440c14933af0060ac94eaa1dc5141561ba7b68`.

## What we found

### Normalized ceiling is 30 — Confirmed, disclosed design

Normal reward scores `clip(R_normal/300) × 100`, hardcore scores `clip((R_hard+100)/400) × 100`,
and `raw = 0.4·normal + 0.6·hard`. The task score is
`min(30, 2.5·(engineering checks passed, max 4) + 0.2·raw)`. The rescale is linear from 0 to 100,
so the task score maps to the same number.

| Case | Normalized |
|---|---|
| Missing checkpoint | 2.5 |
| Loadable but untrained | **10** |
| Solves normal only (300, −100) | 18 |
| **Perfect policy** | **30** |

The 0-100 range is reachable only from 0 to 30, and a third of that comes from passing the loading
checks. The upper anchor of 100 is inconsistent with what any policy can reach, but the cap is
disclosed, so this is a note rather than a defect.
- Maximum score effect: by design.

### Silent partial checkpoint loading — Confirmed from source, minor

Every loader path uses `load_state_dict(strict=False)`, and the default path silently drops
mismatched-shape tensors.
- Example: an honest checkpoint with renamed keys (for example a `module.` prefix) is expected to
  load or fail; under the original evaluator it would be evaluated as a randomly initialized network
  while still collecting the loading bonus. The "Skipping" message appears only in aggregate
  feedback.

### Budget and repeatability — fine

Ten episodes per environment on the first 10 fixed seeds, about 36k steps in total, which takes
seconds against 300 s per environment and `eval_timeout` 900 s. Seeds are fixed and the action is
deterministic, so results are expected to be bit-reproducible on the same build; the 20 reused
episodes are consistent with this.

## Note for users

No repair. The note says:
- The normalized range is 0-30, not 0-100.
- 10 of those points come from loadability checks.
- Checkpoints with mismatched keys or shapes load partially without an error.

A repair that sets the rescale upper anchor to 30 was considered as an alternative; the coordinator
decision is to retain with this note.

## Limits and what was not run

- No model or solver re-runs. Effects are shown on authored controls and counterexamples only.
- No trained policy was evaluated natively, so the reward-to-score mapping was checked from source
  and arithmetic, not on a trained checkpoint.
- The renamed-key example was reasoned from source; it was not run.

## Reproduce

- Review: `evidence/reviews/_game-tasks-correctness.md`, section 10.
- Pinned evaluator copies: the judge image file `sebench_eval.py` (cited by sha256 in the review),
  the judge image file `evaluate_policy.py` (cited by sha256 in the review).
