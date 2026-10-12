# Apple Incremental Game (`apple_incremental_game`)

**Outcome:** Kept, with a note. The score scale agrees with an independent simulation of honest play, but the 1 GB memory limit stated in the task text is not enforced for each solution.

## What the task asks

The task is adapted from an AtCoder Heuristic Contest problem (AHC058), a machine-production incremental game. The task text says: "Your solution is scored on **50 fixed test cases**. Final score = sum of individual case scores. **Higher is better.**" The score for one case is `round(1e5·log2 S)` (README:34-36). Category: Combinatorial Optimization.

## What we checked

No scoring defect was found. These parts were checked and are correct:

- **Score scale.** The raw result (before conversion to 0–100) is converted with the `piecewise_max` method. Its reference point for 0 is 45,000,000 (900,000 per case, that is S = 2⁹). Its reference point for 100 is 282,791,094. The shipped do-nothing starting solution has S = K = 1. It therefore scores a raw result of 0, which maps to 0. A simple greedy simulator, written independently, reaches a raw result of **237,518,875** (4.75M per case). That maps to **17.7** out of 100. This is below the reference point for the 30th-ranked level (5.25M per case), which is the expected order.
- **Time budget and repeatability.** The worst case is 7 waves × 30 s = 210 s, which fits within 600 s. Scoring is deterministic. The one exception is a solution that budgets its own work by wall-clock time, because the grader runs 8 cases in parallel.

The task text (README) states a 1 GB memory limit, but the grader does not enforce it for each solution.

The note says: the advertised 1 GB memory policy is not enforced per solution.

## How much it matters

The score scale has no effect on scores: the maximum effect is 0. The memory note had no score effect on an honest solution. It matters only to users who rely on the stated limit.

## How we checked it

- **Original grader source.** We read the grader file `eval_apple_incremental_game.py` from the original public image. It uses the same code as the Treant task, with `TIME_LIMIT=30`, and the `piecewise_max` score scale. The digest of the grader image is not recorded.
- **Independent simulator.** A greedy simulator that looks one step ahead and follows the rules in the task text ran on all 50 shipped cases. It is not the original tester program.
- **Arithmetic** on the time budget.

## Limits

- No AI model or solver runs were made. Effects are shown only on test submissions and counterexamples that we wrote.
- The greedy check uses an independent simulator, not the original `tools/bin/tester`. Scoring one greedy output with the original tester would close this gap.
- The grader was not run inside the grader image.

## Reproduce

- Review: `evidence/reviews/_game-tasks-correctness.md`, section 9.
- Greedy simulator: `evidence/scripts/_game-tasks-triage/apple/greedy_lookahead.py`.
- Copy of the original grader: the grader-image file `eval_apple_incremental_game.py` (sha256 in [the review](../evidence/reviews/_game-tasks-correctness.md)).
