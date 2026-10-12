# Apple Incremental Game (`apple_incremental_game`)

Status: reviewed by the coordinator, 2026-10-12

- **Domain:** Combinatorial Optimization
- **Decision:** Retain with note — the score anchors are consistent with an independent simulator
  of honest play; the advertised 1 GB memory policy is not enforced per solution.

## What the task promises

An AHC058 adaptation: "Your solution is scored on **50 fixed test cases**. Final score = sum of
individual case scores. **Higher is better.**" The per-case score is `round(1e5·log2 S)`
(README:34-36).

## What we checked and how

- Source reading of the pinned evaluator (`eval_apple_incremental_game.py`), which uses the same
  code as Treant with `TIME_LIMIT=30`, and of the `piecewise_max` rescale.
- Independent check: the earlier one-step-lookahead greedy simulator was rerun locally on all 50
  shipped cases. It follows the README rules; it is not the pinned tester.
- Arithmetic on the time budget.
- Original identity: judge image digest not recorded in the review; task JSON sha256
  `19021ddcbcaf966d7d43300b439862290a5c6c283aa6e6641f96efa07b34a25c`;
  `eval_apple_incremental_game.py` sha256 `c33f5257…d70c`. The tester binary was not available to
  the reviewer.

## What we found

### Anchors — consistent with honest play

The rescale is `piecewise_max` with baseline 45,000,000 (900,000 per case, that is S = 2⁹) and rank1
282,791,094. The shipped do-nothing baseline has S = K = 1, so it scores 0, which maps to 0.
- Example: the independent greedy simulator scored a sum of **237,518,875** (4.75M per case), which
  maps to **17.7**. That is below rank30 (5.25M per case) and in the expected order.
- Maximum score effect: 0.

### Budget and repeatability — fine

The worst case is 7 waves × 30 s = 210 s, within 600 s. Scoring is deterministic, apart from
solutions that use a wall-clock budget under the 8-way parallelism.

### Memory limit not enforced per solution — Note

The README states a 1 GB memory limit, but the evaluator does not enforce it per solution. No score
effect was found for an honest solution; the note is for users who rely on the stated limit.

## Note for users

No repair. The note says: the advertised 1 GB memory policy is not enforced per solution.[^1]

## Limits and what was not run

- No model or solver re-runs. Effects are shown on authored controls and counterexamples only.
- The greedy check uses an independent simulator, not the pinned `tools/bin/tester`. Scoring one
  greedy output with the pinned tester would close this limit; it was not done.
- No native run in the judge image was made for this review.

## Reproduce

- Review: `evidence/reviews/_game-tasks-correctness.md`, section 9.
- Greedy simulator: `evidence/scripts/_game-tasks-triage/apple/greedy_lookahead.py`.
- Pinned evaluator copy:
  the judge-image file `eval_apple_incremental_game.py` (sha256 in [the review](../evidence/reviews/_game-tasks-correctness.md)).

[^1]: The review recommends "retain, with a note on the memory limit". An earlier `decisions.json` entry said "retain"; the coordinator's updated `decisions.json` now records retain-with-note with this note, which this page follows.
