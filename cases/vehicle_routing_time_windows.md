# Vehicle Routing Time Windows (`vehicle_routing_time_windows`)

**Outcome:** Kept, with a note. <mark>The concern about the decimal tolerance does not change scores under an exact check; the note explains the weighting and the fixed test set, says that the checker is compiled from the submitted `include/types.h` and `Makefile`, and says that the 60-second time argument cannot be used on every instance within the 20-minute total.</mark>

## What the task asks

The task asks the solver to "optimize the C++17 CVRPTW solver", to "Modify only src/, include/, and Makefile" and to "Preserve the cvrptw_solver binary name and CLI". CVRPTW is the capacitated vehicle routing problem with time windows, which asks for routes for vehicles of limited capacity that visit each customer within a set time window. The task README describes weighting the instances in three groups and scrambling the nodes for each deployment "防硬编码答案" (to prevent hard-coded answers). It states a cost tolerance of "≤ 0.05". Category: Combinatorial Optimization.

## What we checked

We found no scoring problem that changes scores for a solver that follows the documented time limits. We note four points, and we did not measure the effect of the third (solver edits that reach the checker).

**1. Decimal tolerance (checked; does not change scores).** The README states an inclusive "≤ 0.05" cost tolerance. The checker tests it in binary64 (standard double-precision floating point).

- All coordinates and time-window and service values in the 56 instances are integers. Across 282,800 pairs of nodes, the task's rounded binary64 distance equals an exact integer calculation every time (0 mismatches). Every distance and arrival time is therefore exactly a multiple of 0.1.
- The largest binary64 drift seen in 20,000 random trials of 120-term sums of tenths was 1.13e-11. The checker's time-window test uses a 1e-6 margin, so it returns exactly the verdict that exact rational arithmetic gives. No feasible/infeasible verdict depends on floating point.
- The check of the declared cost behaves inconsistently at exactly 0.05. It rejects a declared 12.05 or 11.95 against a true 12, but accepts 4.05 and 3.95 against 4.
- This counts only if a solver declares a cost off by exactly 0.05. A solver that prints its own sum is within about 1e-11 of the checker's total. The distance used for scoring is the checker's own recomputation, not the declared cost.

**2. The README describes scoring the grader does not implement (documentation only).** The README describes weighting in three groups and scrambling for each deployment, and an internal README describes a scrambled copy of the cases. The grader averages all 56 cases equally over a fixed, unscrambled test set, so no score changes.

**3. The checker is compiled from the submitted header and Makefile.** `tools/verify.cpp` includes `../include/types.h`. That file is in a path the solver may modify, and it defines `dist_x10` and the `Node`/`Instance` structs. The grader also runs `make -j4` with the submitted `Makefile`, and the shipped `Makefile` builds `tools/verify` with the same `CXXFLAGS` as the solver. A solver that edits the distance code, changes `Node` field types, or changes compiler flags (for example adding `-ffast-math`) for speed, with no intent to cheat, therefore also changes how the checker computes feasibility and distance. The exact-arithmetic result in point 1 holds for the original header and flags only. We recommend building the checker from the original header and flags owned by the grader, outside the submitted code.

**4. The 60-second time argument cannot be used on every instance.** The solver is called as `./cvrptw_solver <input> <output> <time_budget_sec>`. The grader passes `min(60, max(1, int(remaining − 6)))` seconds and stops all work 20 minutes after it starts (`TOTAL_JUDGE_TIMEOUT_SEC = 20 * 60`, `PER_INSTANCE_BUDGET_SEC = 60`); instances it cannot start score 0 (`judge_time_limit`). 56 × 60 s = 3,360 s, which is 2.8 times the 1,200 s total.

- The prompt tells the solver "Hidden judge submissions have a 20-minute total wall-clock budget; keep the solver efficient." README §8 lists "时间预算（单实例）：60 秒" (time budget per instance: 60 s) and "总评测预算上限：20 分钟；每实例最多 60 秒，并受剩余总时限截断" (total budget 20 minutes; at most 60 s per instance, cut short by the remaining total). Its last line repeats this in English. `tools/bench.sh` passes 60 s for 100-customer instances. The cap is documented, but no document says how many seconds per instance fit in the total (1,200 / 56 ≈ 21 s).
- A solver that runs until the time argument it is given, as anytime search usually does, is scored on about 20 of the 56 instances, and the rest score 0. At reference quality (100 per instance) its score is at most 21 × 100 / 56 = 37.5 out of 100 (20 instances and 35.7 if the build takes about a minute), and at most 21 × 160 / 56 = 60 even at the per-instance cap of 160. A solver that budgets about 20 s per instance itself is scored on all 56.
- The harness limit (`eval_timeout` 1,200 s) equals the grader's own 20-minute deadline. In this example the grader finishes about 5 s before its deadline, so the result is still reported, but the margin depends on how long the container takes to start.

The task ships with this note. The checker is compiled from the submitted `include/types.h` with the submitted `Makefile`, so solver edits to the distance code, node types or compiler flags also change the checker; the recommended hardening is to build the checker from the original header and flags. The 60-second time argument is capped by the 20-minute total: 56 instances at 60 s would take 3,360 s, so a solver that uses its full argument is scored on only about 20 instances; budget about 20 s per instance. The score averages all 56 instances equally, and the installed instances are fixed and their nodes are not scrambled (the README's three-group weighting and scrambling are not implemented). Despite the README's inclusive "≤ 0.05", a declared cost that differs from the checker's total by exactly 0.05 may be rejected; declaring the computed cost avoids this. Because the test set is the fixed, public Solomon set (a standard benchmark), instances can be identified and published reference routes exist; this is a matter of disclosure and contamination, not a checker defect.

## How much it matters

- The tolerance has no effect for a solver that declares its computed cost. In the hypothetical case of a declared cost off by exactly 0.05, one instance would score 0, so the effect is at most one instance's contribution (see `evidence/scripts/vehicle_routing_time_windows/exact_checks.out` for the boundary cases).
- The text about weighting and scrambling changes no score.
- The header and flags affect only solvers that edit the distance code or node types in `include/types.h`, or the compiler flags in the `Makefile`. We ran no such case, so we have no measured score effect.
- The time argument has no effect on a solver that budgets for the 20-minute total, as the prompt and README §8 say. A solver that uses the full 60-second argument on every instance loses about 36 of 56 instances (computed from the grader's loop; not run). The recorded agent runs on this task score 74.0 to 90.8 out of 100 for the five models (`tasks/README.md`), above the 60-point maximum for 21 scored instances, so those runs did budget for the total.

There is no code change; the note above ships with the task.

## How we checked it

- We read the source of the original evaluation command (build, solve, check, score), `tools/verify.cpp`, `include/types.h` and the task README, for the original grader image, pinned by digest. All 56 example routes passed the original checker and the code that calls it, with the installed 56-row reference table. We make no claim about infeasibility or optimality.
- For an independent exact check, an exact-arithmetic program (`exact_checks.py`, using integer and `Fraction` arithmetic) covered all 56 installed instances. It checked that distances are well defined, the range of values of every instance field, the time-window comparisons, and the boundary of the cost tolerance.
- We bound the binary64 drift with 20,000 random trials of 120-term sums of tenths.
- No formal model applies.

## Limits

- We ran no AI model or solver; the effects shown come only from test submissions and counterexamples we wrote.
- The exact checks used local Python. We built the solver locally with g++ 9.4 (`-march=haswell`), not in the pinned grader image.
- The installed reference (BKS, best known solutions) CSV was absent from the extract; our records give the installed table as 56 rows. The grader scores an instance with no reference row as 100 (`bks.get(name, (nv, td))`). The earlier audit recorded that the installed 56-row table supplies every instance with no fallback (Git tag `earlier-audit-final`, `evidence/selected/vrptw-all56-native-acceptance.json`); we did not re-check this.
- We computed the time-argument effect from the grader's loop and ran no solver that uses the full argument.
- The clarification of the instructions is not yet part of the task prompt, and its files are not included in this repository.
- The header note comes from reading the source; we built and scored no solver with a modified `types.h`.

## Reproduce

- Exact checks: `python3 -I evidence/scripts/vehicle_routing_time_windows/exact_checks.py <internal/cases/raw dir>`.
- Pinned identity: grader image `seededge/edgebench.judge.vehicle_routing_time_windows@sha256:5582f7ec…`; `tools/verify.cpp` sha256 `0adb0ac0…c5e5`, `include/types.h` `9fe467dc…74f1`, `README.md` `26641154…4cda`.
