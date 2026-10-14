# Equivalence Class Divide And Conquer (`equivalence_class_divide_and_conquer`)

**Outcome:** Fixed. <mark>The grader for sub-problem T3 leaves the size of the last neighbourhood reached out of its cost total, so it accepts costs up to the limit plus that size. The excess is small (at most 10⁶, 0.04% of the budget), we have shown no score gain, and a three-token fix closes it.</mark>

![A cost scale with the 2.5·10⁹ limit and a tiny gap above it where the original checker wrongly accepts an over-limit answer of 2.501·10⁹; the fixed checker rejects it.](figures/equivalence_class_divide_and_conquer.svg)

*The original checker leaves out the size of the last neighbourhood reached, so it accepts costs slightly over 2.5·10⁹ (at most 0.04%); the fixed checker rejects them.*

## What the task asks

The task has six problems of increasing difficulty, worth 5, 5, 10, 15, 25 and 40 points. The problem is in T3 (P8204, "directed neighbourhoods"), worth 10 of 100 points. The problem statement fixes the cost budget, "你需要保证操作的总代价不超过 2.5×10^9": the total cost of operations must not exceed 2.5·10⁹. Operation 1 costs the change in neighbourhood size, and the other operations are free. The input sizes are n, m ≤ 10⁶. The task is in the Combinatorial Optimization category.

EdgeBench gives an AI agent the task, and the agent works for up to 12 hours. A hidden grader program scores each submission. For each problem, a checker program decides whether each output is correct.

## What goes wrong

The final cost total misses the last state. At the end, the T3 checker sums costs over states 0..tt−1 and leaves out the last state created, `t[tt]`. That state's net coefficient is +1, so the counted cost is the true cost minus |N_last|, where N_last is the target of the last operation 1. The limit comparison itself (`w <= W`, W = 2.5e9) matches the statement.

- The original checker accepts a crafted output with true cost 2.501·10⁹, over the limit ("ok Correct"). It rejects the same output with one extra zero-cost move at the end. The verdict therefore depends only on whether the checker counts the last target, which rules out a deliberate tolerance.
- Accepted true costs reach at most 2.5·10⁹ + |N_last| ≤ 2.5·10⁹ + 10⁶, a window of at most 0.04% of the budget.
- On the 30 official T3 inputs, the reference solution uses at most 35% of the budget (largest true cost 871,274,246, on case 19). A naive strategy exceeds the limit on 24 of 30 inputs, each time by at least 116,912,620. The problem flips none of these verdicts.

Two other checker deviations go in the opposite direction. The checker compares (x, depth) pairs instead of sets, so it rejects some outputs the statement allows. These cannot raise scores, and we left them unchanged.

## How much it matters

The effect is bounded and confined to T3, and it can only lower scores under the fixed version. T3 gives its full 10 points only when all 30 cases pass. Otherwise each passing case is worth 0.5·10/30 points (`task_score_fraction` in `eval_common.py`, lines 56–61, in the grader image).

- If one official case falls inside the window, the original grader gives 10 points for T3 where the fixed version gives at most 0.5·29/30·10 = 4.83, a difference of 5.17 of 100 points.
- An upper bound on the difference is 9.67 of 100 points, though we have not established that a solution can reach it on all the official cases at once. Cases 29 (n = 1) and 30 (m = 1) cannot exceed the limit, because at most 5m operations each cost at most n, which caps their true cost at 5·10⁶. Cases 1–28 have n, m ≈ 10⁶ (`official_results.txt`), which does not establish that a legal output reaches the acceptance window on each. If a solution were inside the window on all 28 and correct on cases 29–30, it would score 10 under the original grader and 0.5·2/30·10 = 0.33 under the fixed version.
- The 9.67 comes from the following derivation. T3 is worth 10 of the 100 points. Under `task_score_fraction`, T3 gives 10 when all 30 cases pass and 0.5·k/30·10 when k < 30 cases pass, where the factor 0.5 is the partial-credit rule. The fix can only turn an accepted case inside the window into a rejected one, and cases 29 and 30 can never be inside it, so their verdicts are the same in both versions. The largest difference therefore needs the original to give the full 10 (all 30 pass) while the fixed version passes only cases 29 and 30 (k = 2), which gives 10 − 0.5·2/30·10 = 10 − 1/3 = 29/3 ≈ 9.67. If the original does not pass all 30, it gives at most 0.5·29/30·10 = 4.83, so the difference is smaller. The bound assumes a solution that is correct everywhere and lands inside the window on all 28 large cases; we have not shown that such a solution exists.

The problem affects only a solver whose true cost lands within |N_last| above the limit. We found no realistic solution that lands in the window, and **we have demonstrated no score gain**.

## The fix

The fixed version changes one file, `T3_P8204/data/checker.cpp`. Both `std::iota(oq, oq+tt, 0)` and `std::sort(oq, oq+tt, …)` become `oq+tt+1`, and the loop bound `i<tt` becomes `i<=tt`. The arrays are already large enough for index tt, and no time, memory, output or other limit changes. The task JSON changes only `judge.image_tag`.

In the tables below, AC (accepted) means the checker accepts an output and WA (wrong answer) means it rejects it. "Raw" is the raw result (before conversion to 0–100).

| Test submission | Submission / input | Original grader | Fixed grader | Expected |
|---|---|---|---|---|
| **Shows the problem** | `naive.cpp` on crafted input B (star, n=10⁶, m=2501; true cost 2.501·10⁹ > limit) | **AC**, raw 10 (T3 1/1) | **WA "Operation cost exceeded"**, raw 0 | original wrong, fixed right ✔ |
| Correct, exactly at the limit | `naive.cpp` on crafted input A (m=2500; true cost exactly 2.5·10⁹) | AC, raw 10 | AC, raw 10 | accepted by both ✔ |
| **Correct (whole task)** | official `std.cpp` for T1–T6 | **raw 100 / 100 out of 100**; T1 5/5, T2 10/10, **T3 30/30**, T4 25/25, T5 20/20, T6 30/30 (cases passed); exit 0; pass rate 1.000 | **raw 100 / 100 out of 100**; same counts for every sub-problem; exit 0; pass rate 1.000 | unchanged ✔ |
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

Original and fixed scores are equal for every output whose true cost is ≤ 2.5·10⁹ or > 2.5·10⁹ + |N_last|. Only outputs inside the window differ, and only in T3. The fixed version rejects them, where the original wrongly accepted them.

## How we checked it

- We compiled the unchanged T3 checker in the original grader image, pinned by digest, with the harness's own flags (`g++ -std=c++17 -Ofast -pipe -I prob -I data`) and ran it with `--network none`. We ran it on five crafted outputs on a star-shaped tree with n = 10⁶: at the limit, just over, further over, the same over-limit output with a free move at the end, and an efficient strategy.
- For a brute-force check we generated 329 random small trees (n ≤ 7) with legal operation sequences. For each, a separate program computed the true cost directly from the statement's definition, and we compared it with an instrumented checker that sums all states and with the original checker at an adjustable limit. There were 0 mismatches in 329 cases. In 307 cases, all those with a non-empty last target, the original checker accepted the output with the limit set to true cost − 1.
- We ran the official reference `std.cpp` and a naive legal strategy on all 30 official T3 inputs.
- We ran the original and fixed graders side by side with the original `eval.py` command, under `--network none --memory 3g --cpus 3`. For the reference submission the run covered the whole six-problem task. We repeated it three times, and no test submission changed verdict (see `data/paired-repeatability.md`).

## Limits

- We ran no AI model or solver. The effects shown come only from test submissions and counterexamples we wrote.
- The test submission that shows the problem uses a crafted input (an n = 10⁶ star) added as an extra T3 case. No official input puts any known solution inside the window.
- We tried only two strategies near the limit, the reference and the naive strategy. In principle we cannot rule out a solver within 10⁶ of the limit on some official case.
- We examined only T3 in depth. The side-by-side run graded all six problems for the reference submission, with identical results.
- We did not verify the six-family evaluator checks. Issue #2 asked for original and fixed evaluator checks on each of the six problems (T1–T6), with the T2 reference control kept separate from the T3 checker correction. We graded only the reference submission on all six problems (identical results in both versions) and ran no per-problem test submissions for T1, T2, T4, T5 or T6. The fix changes only `T3_P8204/data/checker.cpp`, so the other problems' checkers are the original files. We keep this as a documented limitation.
- The fixed version keeps the strictness quirks from comparing pairs. The statement's condition reads as set equality, and pair equality is an arguable intended reading.

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
