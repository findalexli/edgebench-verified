# Equivalence Class Divide And Conquer (`equivalence_class_divide_and_conquer`)

**Outcome:** Fixed. <mark>The grader for sub-problem T3 leaves the last step out of its cost total, so it accepts costs up to the limit plus the size of the last step; the excess is small (at most 0.04%), no score gain is shown, and a three-token fix closes it.</mark>

![A cost scale with the 2.5·10⁹ limit and a tiny gap above it where the original checker wrongly accepts an over-limit answer of 2.501·10⁹; the fixed checker rejects it.](figures/equivalence_class_divide_and_conquer.svg)

*The original checker leaves out the last step, so it accepts costs slightly over 2.5·10⁹ (at most 0.04%); the fixed checker rejects them.*

## What the task asks

The task has six problems of increasing difficulty, worth 5, 5, 10, 15, 25 and 40 points. The problem is in T3 (P8204, "directed neighbourhoods"), worth 10 of 100 points. The problem statement fixes the cost budget: "你需要保证操作的总代价不超过 2.5×10^9", that is, the total cost of operations must not exceed 2.5·10⁹. Operation 1 costs the change in neighbourhood size, and the other operations are free. The input sizes are n, m ≤ 10⁶. Category: Combinatorial Optimization.

EdgeBench gives an AI agent the task, and the agent works for up to 12 hours. A hidden grader program scores each submission. For each problem, a checker program decides whether each output is correct.

## What goes wrong

**The final cost total misses the last state.** At the end, the T3 checker sums costs over states 0..tt−1. It leaves out the last state created, `t[tt]`. That state's net coefficient is +1, so the counted cost is the true cost minus |N_last|, where N_last is the target of the last operation 1. The limit comparison itself (`w <= W`, W = 2.5e9) matches the statement.

- Example under the original checker: a crafted output with true cost 2.501·10⁹, over the limit, is accepted ("ok Correct"). The same output with one extra zero-cost move at the end is rejected. So the verdict depends only on whether the last target is counted. It is not a deliberate tolerance.
- Bound: accepted true costs reach at most 2.5·10⁹ + |N_last| ≤ 2.5·10⁹ + 10⁶. This window is at most 0.04% of the budget.
- On the 30 official T3 inputs, the reference solution uses at most 35% of the budget (largest true cost 871,274,246, on case 19). A naive strategy exceeds the limit on 24 of 30 inputs, each time by at least 116,912,620. The problem flips none of these verdicts.

Two other checker deviations go in the opposite direction. The checker compares (x, depth) pairs rather than sets, so it rejects some outputs the statement allows. These cannot raise scores, and they are left unchanged.

## How much it matters

The effect is bounded and confined to T3. In the worst case, a solution whose cost falls inside the window on an official input could gain up to +5.17 of 100 points. Only a solver whose true cost lands within |N_last| above the limit is affected. No realistic solution that lands in the window was found, and **no score gain is demonstrated**.

## The fix

The fixed version changes one file, `T3_P8204/data/checker.cpp`. Both `std::iota(oq, oq+tt, 0)` and `std::sort(oq, oq+tt, …)` become `oq+tt+1`, and the loop bound `i<tt` becomes `i<=tt`. The arrays are already large enough for index tt. No time, memory, output or other limits change. The task JSON changes only `judge.image_tag`.

In the tables below, AC (accepted) means the checker accepts an output and WA (wrong answer) means it rejects it. "Raw" is the raw result (before conversion to 0–100).

| Test submission | Submission / input | Original grader | Fixed grader | Expected |
|---|---|---|---|---|
| **Shows the problem** | `naive.cpp` on crafted input B (star, n=10⁶, m=2501; true cost 2.501·10⁹ > limit) | **AC**, raw 10 (T3 1/1) | **WA "Operation cost exceeded"**, raw 0 | original wrong, fixed right ✔ |
| Correct, exactly at the limit | `naive.cpp` on crafted input A (m=2500; true cost exactly 2.5·10⁹) | AC, raw 10 | AC, raw 10 | accepted by both ✔ |
| **Correct (whole task)** | official `std.cpp` for T1–T6 | **raw 100 / 100 out of 100**; T1 5/5, T2 10/10, **T3 30/30**, T4 25/25, T5 20/20, T6 30/30; exit 0; pass rate 1.000 | **raw 100 / 100 out of 100**; same counts for every sub-problem; exit 0; pass rate 1.000 | unchanged ✔ |
| Incorrect | `naive.cpp` as T3, others empty, on the 30 official inputs | raw 1 / 1 out of 100; T3 6 AC / **24 WA** (cost exceeded); exit 1; pass rate 0.020 | raw 1 / 1 out of 100; the same 6 AC / 24 WA, case by case; exit 1; pass rate 0.020 | rejected by both ✔ |

The checker run directly on the crafted outputs:

| Case | Original checker | Fixed checker |
|---|---|---|
| A at limit | ok | ok |
| B over by n | **ok** | **WA** |
| C over by 2n | WA | WA |
| D (B plus a free move at the end) | WA | WA |
| E efficient | ok | ok |

Under the original grader setup, with no limits changed, the reference passes all 30 T3 inputs with both the original and the fixed checker.

**Score compatibility:** original and fixed scores are equal for every output whose true cost is ≤ 2.5·10⁹ or > 2.5·10⁹ + |N_last|. Only outputs inside the window differ: the fixed version rejects them, while the original wrongly accepted them. Only T3 can differ.

## How we checked it

- **Original checker in the original grader image, pinned by digest.** The unchanged T3 checker was compiled with the harness's own flags (`g++ -std=c++17 -Ofast -pipe -I prob -I data`) and run with `--network none`. It was run on five crafted outputs on a star-shaped tree with n = 10⁶: at the limit, just over, further over, the same over-limit output with a free move at the end, and an efficient strategy.
- **Brute-force check.** 329 random small trees (n ≤ 7) with legal operation sequences were generated. For each, a separate program computed the true cost directly from the statement's definition. This was compared with an instrumented checker that sums all states and with the original checker at an adjustable limit. Result: 0 mismatches in 329 cases. In 307 cases, all those with a non-empty last target, the original checker accepted the output with the limit set to true cost − 1.
- **Official inputs.** The official reference `std.cpp` and a naive legal strategy ran on all 30 official T3 inputs.
- **Side-by-side run of the original and fixed graders** with the original `eval.py` command, under `--network none --memory 3g --cpus 3`. For the reference submission it covered the whole six-problem task. It was repeated three times, and no test submission changed verdict (see `data/paired-repeatability.md`).

## Limits

- No AI model or solver was run. Effects are shown only on test submissions and counterexamples we wrote.
- The test submission that shows the problem uses a crafted input (an n = 10⁶ star) added as an extra T3 case. No official input puts any known solution inside the window.
- Only two strategies were tried near the limit: the reference and the naive strategy. In principle, a solver within 10⁶ of the limit on some official case cannot be ruled out.
- Only T3 was examined in depth. The side-by-side run graded all six problems for the reference submission, with identical results.
- The strictness quirks from comparing pairs are unchanged. The statement's condition reads as set equality, and pair equality is an arguable intended reading.

## Reproduce

- Original grader image: `sha256:f793d805…`.
- Scripts:
  - `evidence/scripts/equivalence_class_divide_and_conquer/run_crafted.sh`
  - `run_random.sh` (with `random_oracle.py`)
  - `run_official.sh`
  - `run_strictness.sh`
- Side-by-side run: `repairs/equivalence_class_divide_and_conquer-v2/paired/run.sh` (results in `paired/results.md`)
- Patch: `repairs/equivalence_class_divide_and_conquer-v2/repair.patch`
- Supporting records: `repairs/equivalence_class_divide_and_conquer-v2/` (the folder holding the fixed version; source-lock.json, `paired/evidence/`).
