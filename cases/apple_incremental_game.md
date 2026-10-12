# Apple Incremental Game (`apple_incremental_game`)

**Decision:** Retain with note. The score anchors are consistent with an independent simulator of honest play, but the advertised 1 GB memory policy is not enforced per solution.

## What the task asks for

An AHC058 adaptation: "Your solution is scored on **50 fixed test cases**. Final score = sum of individual case scores. **Higher is better.**" The per-case score is `round(1e5·log2 S)` (README:34-36). Category: Combinatorial Optimization.

## What goes wrong

No scoring defect. What was checked and found correct:

- **Anchors.** The rescale is `piecewise_max` with baseline 45,000,000 (900,000 per case, that is S = 2⁹) and rank1 282,791,094. The shipped do-nothing baseline has S = K = 1, so it scores 0, which maps to 0. An independent greedy simulator scored a sum of **237,518,875** (4.75M per case), which maps to **17.7**. That is below rank30 (5.25M per case) and in the expected order.
- **Budget and repeatability.** The worst case is 7 waves × 30 s = 210 s, within 600 s. Scoring is deterministic, apart from solutions that use a wall-clock budget under the 8-way parallelism.

Note: the README states a 1 GB memory limit, but the evaluator does not enforce it per solution.

The note says: the advertised 1 GB memory policy is not enforced per solution.

## Impact

Maximum score effect from the anchors: 0. No score effect was found for an honest solution from the memory note; it matters only to users who rely on the stated limit.

## Fix (v2)

No change; the note above ships with the task.

## How we know

- **Original evaluator source.** We read the pinned evaluator (`eval_apple_incremental_game.py`), which uses the same code as Treant with `TIME_LIMIT=30`, and the `piecewise_max` rescale. The judge image digest is not recorded.
- **Independent simulator.** A one-step-lookahead greedy simulator that follows the README rules was run on all 50 shipped cases. It is not the pinned tester.
- **Arithmetic** on the time budget.

## Limits

- No model or solver runs. Effects are shown only on authored controls and counterexamples.
- The greedy check uses an independent simulator, not the pinned `tools/bin/tester`. Scoring one greedy output with the pinned tester would close this limit.
- The evaluator was not run in the judge image.

## Reproduce

- Review: `evidence/reviews/_game-tasks-correctness.md`, section 9.
- Greedy simulator: `evidence/scripts/_game-tasks-triage/apple/greedy_lookahead.py`.
- Pinned evaluator copy: the judge-image file `eval_apple_incremental_game.py` (sha256 in [the review](../evidence/reviews/_game-tasks-correctness.md)).
