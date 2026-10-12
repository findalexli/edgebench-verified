# Vehicle Routing Time Windows (`vehicle_routing_time_windows`)

**Outcome:** Kept, with a note. The concern about the decimal tolerance does not change scores under an exact check; the note explains the weighting and the fixed test set, and says that the checker is compiled from the submitted `include/types.h`.

## What the task asks

The solver is asked to "optimize the C++17 CVRPTW solver", to "Modify only src/, include/, and Makefile" and to "Preserve the cvrptw_solver binary name and CLI". CVRPTW is the capacitated vehicle routing problem with time windows: plan routes for vehicles of limited capacity so that each customer is visited within a set time window. The task README describes weighting the instances in three groups and scrambling the nodes for each deployment "防硬编码答案" (to prevent hard-coded answers). It states a cost tolerance of "≤ 0.05". Category: Combinatorial Optimization.

## What we checked

No scoring problem that changes scores enough to matter was found. Three points are noted.

**1. Decimal tolerance (checked; does not change scores).** The README states an inclusive "≤ 0.05" cost tolerance. The checker tests it in binary64 (standard double-precision floating point).

- All coordinates and time-window and service values in the 56 instances are integers. Across 282,800 pairs of nodes, the task's rounded binary64 distance equals an exact integer calculation every time (0 mismatches). So every distance and arrival time is exactly a multiple of 0.1.
- The largest binary64 drift seen in 20,000 random trials of 120-term sums of tenths was 1.13e-11. The checker's time-window test uses a 1e-6 margin, so it returns exactly the verdict that exact rational arithmetic gives. No feasible/infeasible verdict depends on floating point.
- **Example.** The check of the declared cost behaves inconsistently at exactly 0.05. It rejects a declared 12.05 or 11.95 against a true 12, but accepts 4.05 and 3.95 against 4.
- This matters only if a solver declares a cost off by exactly 0.05. A solver that prints its own sum is within about 1e-11 of the checker's total. The distance used for scoring is the checker's own recomputation, not the declared cost.

**2. The README describes scoring the grader does not implement (documentation only).** The README describes weighting in three groups and scrambling for each deployment, and an internal README describes a scrambled copy of the cases. The grader averages all 56 cases equally over a fixed, unscrambled test set. No score changes.

**3. The checker is compiled from the submitted header.** `tools/verify.cpp` includes `../include/types.h`. That file is in a path the solver may modify, and it defines `dist_x10` and the `Node`/`Instance` structs. A solver that edits the distance code or changes `Node` field types for speed, with no intent to cheat, therefore also changes how the checker computes feasibility and distance. Recommended hardening: build the checker from the original header owned by the grader, outside the submitted code.

**Note shipped with the task.** The checker is compiled from the submitted `include/types.h`, so solver edits to the distance code or node types also change the checker; the recommended hardening is to build the checker from the original header. The score averages all 56 instances equally, and the installed instances are fixed and their nodes are not scrambled (the README's three-group weighting and scrambling are not implemented). Despite the README's inclusive "≤ 0.05", a declared cost that differs from the checker's total by exactly 0.05 may be rejected; declaring the computed cost avoids this. Because the test set is the fixed, public Solomon set (a standard benchmark), instances can be identified and published reference routes exist; this is a matter of disclosure and contamination, not a checker defect.

## How much it matters

- Tolerance: no effect for a solver that declares its computed cost. In the hypothetical case of a declared cost off by exactly 0.05, one instance would score 0, so the effect is at most one instance's contribution (see `evidence/scripts/vehicle_routing_time_windows/exact_checks.out` for the boundary cases).
- Text about weighting and scrambling: no score change.
- Header: affects only solvers that edit the distance code or node types in `include/types.h`. No such case was run, so no score effect is measured.

There is no code change. The note above ships with the task.

## How we checked it

- **Original grader.** We read the source of the original evaluation command (build, solve, check, score), `tools/verify.cpp`, `include/types.h` and the task README, for the original grader image, pinned by digest. All 56 example routes passed the original checker and the code that calls it, with the installed 56-row reference table. No claim is made about infeasibility or optimality.
- **Independent exact check.** An exact-arithmetic program (`exact_checks.py`, using integer and `Fraction` arithmetic) covered all 56 installed instances. It checked that distances are well defined, the range of values of every instance field, the time-window comparisons, and the boundary of the cost tolerance.
- **Drift bound.** 20,000 random trials of 120-term sums of tenths bound the binary64 drift.
- No formal model applies.

## Limits

- No AI model or solver was run; effects are shown only on test submissions and counterexamples we wrote.
- The exact checks used local Python. The solver was built locally with g++ 9.4 (`-march=haswell`), not in the pinned grader image.
- The output of `exact_checks.py` is not saved in this repository.
- The installed reference (BKS, best known solutions) CSV was absent from the extract; the installed table is recorded as 56 rows.
- The clarification of the instructions is not yet part of the task prompt, and its files are not included in this repository.
- The header note comes from reading the source; no solver with a modified `types.h` was built or scored.

## Reproduce

- Exact checks: `python3 -I evidence/scripts/vehicle_routing_time_windows/exact_checks.py <internal/cases/raw dir>`.
- Pinned identity: grader image `seededge/edgebench.judge.vehicle_routing_time_windows@sha256:5582f7ec…`; `tools/verify.cpp` sha256 `0adb0ac0…c5e5`, `include/types.h` `9fe467dc…74f1`, `README.md` `26641154…4cda`.
