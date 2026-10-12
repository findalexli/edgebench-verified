# Vehicle Routing Time Windows (`vehicle_routing_time_windows`)

**Decision:** Retain with note. The decimal-tolerance concern is immaterial under an exact check; the note clarifies weighting and the fixed suite, and says that the verifier is compiled from the submitted `include/types.h`.

## What the task asks for

The solver is asked to "optimize the C++17 CVRPTW solver", to "Modify only src/, include/, and Makefile" and to "Preserve the cvrptw_solver binary name and CLI". The task README describes three-group weighting of instances and per-deployment node scrambling "防硬编码答案" (to prevent hard-coded answers), and states a cost tolerance of "≤ 0.05". Category: Combinatorial Optimization.

## What goes wrong

No material scoring defect was found. Three points are noted.

**1. Decimal tolerance (checked, immaterial).** The README states an inclusive "≤ 0.05" cost tolerance; the verifier checks it in binary64.

- All coordinates and time-window/service values in the 56 instances are integers. Across 282,800 node pairs, the task's binary64 rounded distance equals the exact integer oracle every time (0 mismatches), so every distance and arrival time is exactly a multiple of 0.1.
- The largest binary64 drift seen in 20,000 random trials of 120-term sums of tenths was 1.13e-11, so the verifier's time-window test with a 1e-6 margin returns exactly the exact-rational verdict. No feasible/infeasible verdict depends on floating point.
- **Example.** The cost-line check behaves inconsistently at exactly 0.05: it rejects a declared 12.05 or 11.95 against a true 12, but accepts 4.05 and 3.95 against 4.
- This matters only if a solver declares a cost off by exactly 0.05. A solver printing its own sum is within about 1e-11 of the verifier's total, and the distance used for scoring is the verifier's recomputation, not the declared cost.

**2. README describes scoring the evaluator does not implement (documentation only).** The README describes three-group weighting and per-deployment scrambling, and an internal README describes a scrambled copy of the cases. The evaluator averages all 56 cases equally over a fixed, unscrambled suite. No score changes.

**3. The verifier is compiled from the submitted header.** `tools/verify.cpp` includes `../include/types.h`, which is in a path the solver may modify and defines `dist_x10` and the `Node`/`Instance` structs. A solver that edits the distance code or changes `Node` field types for speed, with no intent to cheat, therefore also changes the checker's feasibility and distance semantics. Recommended hardening: build the verifier from the original (judge-owned) header, outside the candidate tree.

**Note shipped with the task.** The verifier is compiled from the submitted `include/types.h`, so solver edits to the distance code or node types also change the checker; the recommended hardening is to build the verifier from the original header. The score averages all 56 instances equally, and the installed instances are fixed and not node-scrambled (the README's three-group weighting and scrambling are not implemented). Despite the README's inclusive "≤ 0.05", a declared cost that differs from the verifier's total by exactly 0.05 may be rejected; declaring the computed cost avoids this. Because the suite is the fixed, public Solomon set, instances are identifiable and published reference routes exist; this is a disclosure and contamination matter, not a checker defect.

## Impact

- Tolerance: none for a solver that declares its computed cost. In the hypothetical case of a declared cost off by exactly 0.05, one instance would score 0, so the effect is bounded by one instance's contribution (see `evidence/scripts/vehicle_routing_time_windows/exact_checks.out` for the boundary cases).
- Weighting and scrambling text: no score change.
- Header: affects only solvers that edit `include/types.h` distance code or node types. No such case was run, so no score effect is measured.

## Fix (v2)

No change; the note above ships with the task.

## How we know

- **Original evaluator.** Source reading of the original eval command (build, solve, verify, score), `tools/verify.cpp`, `include/types.h` and the task README, for the pinned judge image `sha256:5582f7ec…`. All 56 route witnesses passed the original checker and caller, with the installed 56-row reference table. No infeasibility or optimality claim is made.
- **Independent oracle.** An exact-arithmetic oracle (`exact_checks.py`, integer and `Fraction` arithmetic) over all 56 installed instances: distance well-definedness, the numeric domain of every instance field, time-window comparisons, and the cost-tolerance boundary.
- **Drift bound.** 20,000 random trials of 120-term sums of tenths bound binary64 drift.
- No formal model applies.

## Limits

- No model or solver was run; effects are shown on authored controls and counterexamples only.
- Exact checks used local Python; the solver was built locally with g++ 9.4 (`-march=haswell`), not in the pinned judge image.
- The output of `exact_checks.py` is not saved in this repository.
- The installed reference (BKS) CSV was absent from the extract; the installed table is recorded as 56 rows.
- The instruction clarification is not yet part of the task prompt, and its files are not included in this repository.
- The header note is from source reading; no solver with a modified `types.h` was built or scored.

## Reproduce

- Exact checks: `python3 -I evidence/scripts/vehicle_routing_time_windows/exact_checks.py <internal/cases/raw dir>`.
- Pinned identity: judge image `seededge/edgebench.judge.vehicle_routing_time_windows@sha256:5582f7ec…`; `tools/verify.cpp` sha256 `0adb0ac0…c5e5`, `include/types.h` `9fe467dc…74f1`, `README.md` `26641154…4cda`.
