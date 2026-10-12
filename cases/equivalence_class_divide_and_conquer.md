# Equivalence Class Divide And Conquer (`equivalence_class_divide_and_conquer`)

Status: reviewed by the coordinator, 2026-10-12

- **Domain:** Combinatorial Optimization
- **Decision:** Repair v2. The T3 checker's cost loop skips the final state, so it accepts costs up to the limit plus the size of the last target. The excess is bounded (under 0.04%) and no score gain was shown. A three-token fix closes it.

## What the task promises

The task has six progressive problems worth 5, 5, 10, 15, 25 and 40 points. The defect is in T3 (P8204, "directed neighbourhoods"), worth 10 of 100 points. The statement fixes the cost budget: "你需要保证操作的总代价不超过 2.5×10^9", that is, the total cost of operations must not exceed 2.5·10⁹. Operation 1 costs the change in neighbourhood size, and the other operations are free. The constraints are n, m ≤ 10⁶.

## What we checked and how

- **Direct checker runs.** We compiled the unchanged T3 checker inside the pinned judge image with the harness's own flags (`g++ -std=c++17 -Ofast -pipe -I prob -I data`) and ran it with `--network none`, in one container.
- **Crafted cases.** These were five controls on a star with n = 10⁶. They cover at the limit, just over, further over, the same over-limit output with a trailing free move, and an efficient strategy.
- **Brute-force oracle.** We generated 329 random small trees (n ≤ 7) with legal operation sequences. For each, the oracle computed the true cost directly from the statement's definition. We compared it with an instrumented full-sweep checker and with the original checker at a parameterised limit.
- **Official inputs.** We ran the official reference `std.cpp` and a naive legal strategy on all 30 official T3 inputs.
- **Paired v1/v2 evaluation.** This ran in one E2B worker with the original `eval.py` command, under `--network none --memory 3g --cpus 3`. It covered the whole six-problem task for the reference arm.
- **Original identity:** judge image `seededge/edgebench.judge.equivalence_class_divide_and_conquer@sha256:f793d805…e767e6`. The key file is `T3_P8204/data/checker.cpp`, sha256 `f92b52cc…`.

## What we found

**Confirmed, narrower than the earlier wording.** The checker's final cost sweep covers states 0..tt−1 and leaves out the last state created, `t[tt]`. That state's net coefficient is +1, so the counted cost is the true cost minus |N_last|, where N_last is the target of the last operation 1. The limit comparison itself (`w <= W`, W = 2.5e9) matches the statement.

- **Example under the original checker:**
  - A crafted output with true cost 2.501·10⁹, over the limit, is accepted ("ok Correct").
  - The same output with one trailing zero-cost move appended is rejected.
  - So the verdict depends only on whether the last target is counted. It is not a tolerance.
- **Oracle:** 0 mismatches in 329 cases. In 307 cases, all those with a non-empty last target, the original accepted with the limit set to true cost − 1.
- **Bound:** accepted true costs reach at most 2.5·10⁹ + |N_last| ≤ 2.5·10⁹ + 10⁶. The window is at most 0.04% of the budget.
- **Official inputs:**
  - The reference uses at most 35% of the budget. Its largest true cost is 871,274,246, on case 19.
  - The naive strategy exceeds the limit on 24 of 30 inputs, each time by at least 116,912,620.
  - The defect flips none of these verdicts.
- **Maximum effect:** bounded and confined to T3. In the worst case, a solution whose cost falls inside the window on an official input could gain up to +5.17 of 100 points. No realistic solution that lands in the window was found, and **no score gain is demonstrated**.

An earlier audit withheld this task because the checker accepts over-limit cost. Re-checking showed that the leak is bounded by the last target's size and that no observed score is affected. Withholding the whole 100-point task is disproportionate, so the decision is repair.

The review also noted two checker deviations in the opposite direction. The checker compares (x, depth) pairs rather than sets, so it rejects some statement-legal outputs. These cannot inflate scores, and they are left unchanged.

## Repair

v2 changes one file, `T3_P8204/data/checker.cpp`. Both `std::iota(oq, oq+tt, 0)` and `std::sort(oq, oq+tt, …)` become `oq+tt+1`, and the loop bound `i<tt` becomes `i<=tt`. The arrays are already sized for index tt. No time, memory, output or other limits change. The task JSON changes only `judge.image_tag`.

| Arm | Submission / input | v1 | v2 | Expected |
|---|---|---|---|---|
| **Trigger** | `naive.cpp` on crafted B (star, n=10⁶, m=2501; true cost 2.501·10⁹ > limit) | **AC**, raw 10 (T3 1/1) | **WA "Operation cost exceeded"**, raw 0 | v1 wrong, v2 right ✔ |
| At-limit control | `naive.cpp` on crafted A (m=2500; true cost exactly 2.5·10⁹) | AC, raw 10 | AC, raw 10 | accept both ✔ |
| **Valid control (whole task)** | official `std.cpp` for T1–T6 | **raw 100 / norm 100**; T1 5/5, T2 10/10, **T3 30/30**, T4 25/25, T5 20/20, T6 30/30; exit 0; pass rate 1.000 | **raw 100 / norm 100**; identical per-subtask counts; exit 0; pass rate 1.000 | unchanged ✔ |
| Invalid control | `naive.cpp` as T3, others empty, on the 30 official inputs | raw 1 / norm 1; T3 6 AC / **24 WA** (cost exceeded); exit 1; pass rate 0.020 | raw 1 / norm 1; the same 6 AC / 24 WA, case by case; exit 1; pass rate 0.020 | rejected both ✔ |

Checker run directly on the crafted outputs:

| Case | v1 | v2 |
|---|---|---|
| A at limit | ok | ok |
| B over by n | **ok** | **WA** |
| C over by 2n | WA | WA |
| D (B plus a trailing free move) | WA | WA |
| E efficient | ok | ok |

An earlier note said the corrected checker "needed a 64 MiB output allowance". That limit came from the earlier audit's own sandbox. It is not a property of the task. Under the native evaluator, with no limits changed, the reference passes all 30 T3 inputs in both v1 and v2.

**Score compatibility:** v1 and v2 scores are equal for every output whose true cost is ≤ 2.5·10⁹ − |N_last| or > 2.5·10⁹ + |N_last|. Only outputs inside the leak window differ: v2 rejects them, while v1 wrongly accepted them. Only T3 can differ.

## Limits and what was not run

- No model or solver re-runs. Effects are shown only on authored controls and counterexamples.
- The trigger uses a crafted input (an n = 10⁶ star) mounted as an extra T3 case. No official input puts any known solution inside the leak window.
- Only two strategies were tried near the limit: the reference and the naive strategy. A solver within 10⁶ of the limit on some official case cannot be ruled out in principle.
- In the original review only T3 was examined. The paired run graded all six problems for the reference arm, with identical results.
- Each paired arm ran once, on one worker.
- The pair-equality strictness quirks are unchanged. The review reads the statement's mark condition as set equality, and pair equality is an arguable intended reading.

## Reproduce

- Review scripts:
  - `evidence/scripts/equivalence_class_divide_and_conquer/run_crafted.sh`
  - `run_random.sh` (with `random_oracle.py`)
  - `run_official.sh`
  - `run_strictness.sh`
- Paired evaluation: `repairs/equivalence_class_divide_and_conquer-v2/paired/run.sh` (results in `paired/results.md`)
- Patch: `repairs/equivalence_class_divide_and_conquer-v2/repair.patch`

Supporting records: `repairs/equivalence_class_divide_and_conquer-v2/` (source-lock.json, `paired/evidence/`).
