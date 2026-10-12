# Vehicle Routing Time Windows (`vehicle_routing_time_windows`)

Status: reviewed by the coordinator, 2026-10-12

- **Domain:** Combinatorial Optimization
- **Decision:** Retain with note — the decimal-tolerance concern is immaterial under an exact check; adopt the instruction clarification on weighting and the fixed suite; note that the verifier is compiled from the submitted `include/types.h`.

## What the task promises

The solver is asked to "optimize the C++17 CVRPTW solver", to "Modify only src/, include/, and Makefile" and to "Preserve the cvrptw_solver binary name and CLI". The task README describes three-group weighting of instances and per-deployment node scrambling "防硬编码答案" (to prevent hard-coded answers), and states a cost tolerance of "≤ 0.05".

## What we checked and how

- Source reading of the original eval command (build, solve, verify, score) and of `tools/verify.cpp`, `include/types.h` and the task README.
- An exact-arithmetic oracle (`exact_checks.py`, integer and `Fraction` arithmetic) over all 56 installed instances: distance well-definedness, the numeric domain of every instance field, time-window comparisons, and the cost-tolerance boundary.
- 20,000 random trials of 120-term sums of tenths to bound binary64 drift.
- Review of the proposed instruction clarification (`reproductions/vrptw-instruction-clarification/`) against the evaluator.
- Earlier accepted evidence, reused and not re-run: all 56 route witnesses passed the original checker and caller, with the installed 56-row reference table.
- Original identity: judge image `seededge/edgebench.judge.vehicle_routing_time_windows@sha256:5582f7ec…`; key files `tools/verify.cpp` sha256 `0adb0ac0…c5e5`, `include/types.h` `9fe467dc…74f1`, `README.md` `26641154…4cda`.

## What we found

**Refuted as material: decimal tolerance.** An earlier audit recorded two saved disagreements between the README's inclusive "≤ 0.05" cost tolerance and the verifier's binary64 check. Re-checking showed:

- All coordinates and time-window/service values in the 56 instances are integers. Across 282,800 node pairs, the task's binary64 rounded distance equals the exact integer oracle every time (0 mismatches), so every distance and arrival time is exactly a multiple of 0.1.
- Binary64 drift is at most 1.13e-11, so the verifier's time-window test with a 1e-6 margin returns exactly the exact-rational verdict. No feasible/infeasible verdict depends on floating point.
- The cost-line check does behave inconsistently at exactly 0.05: it rejects a declared 12.05 or 11.95 against a true 12, but accepts 4.05 and 3.95 against 4. This reproduces the two saved disagreements exactly.
- It only matters if a solver declares a cost off by exactly 0.05. A solver printing its own sum is within about 1e-11 of the verifier's total, and the distance used for scoring is the verifier's recomputation, not the declared cost. In that hypothetical case one instance would flip to 0: at most 286 raw points, 2.86% of the 0–10000 scale. The decision record gives the effect as none.

**Confirmed, documentation only: README describes scoring the evaluator does not implement.** The README describes three-group weighting and per-deployment scrambling, and an internal README describes a scrambled copy of the cases. The evaluator averages all 56 cases equally over a fixed, unscrambled suite. The proposed clarification states this accurately. No score changes.

**Confirmed, good-faith note: the verifier is compiled from the submitted header.** `tools/verify.cpp` includes `../include/types.h`, which is in a path the solver may modify and defines `dist_x10` and the `Node`/`Instance` structs. A solver that edits the distance code or changes `Node` field types for speed, with no intent to cheat, therefore also changes the checker's feasibility and distance semantics. No such case was run, so no score effect is measured. Recommended hardening: build the verifier from the original (judge-owned) header, outside the candidate tree.

**Still valid from earlier work:** the 56 feasibility witnesses stand. No infeasibility or optimality claim is made.

Apart from the header note above, no good-faith scoring defect was found.

## Note for users

No repair. The note says: the verifier is compiled from the submitted `include/types.h`, so solver edits to the distance code or node types also change the checker; the recommended hardening is to build the verifier from the original header. The score averages all 56 instances equally, and the installed instances are fixed and not node-scrambled (the README's three-group weighting and scrambling are not implemented). Despite the README's inclusive "≤ 0.05", a declared cost that differs from the verifier's total by exactly 0.05 may be rejected; declaring the computed cost avoids this. Because the suite is the fixed, public Solomon set, instances are identifiable and published reference routes exist; this is a disclosure and contamination matter, not a checker defect.

## Limits and what was not run

- No model or solver re-runs; effects are shown on authored controls and counterexamples only.
- Exact checks used local Python; the solver was built locally with g++ 9.4 (`-march=haswell`), not in the pinned judge image.
- The installed reference (BKS) CSV was absent from the extract; earlier accepted evidence records a 56-row installed table.
- The instruction clarification is a proposal; it has not been bound to a task record.
- The header note is from source reading; no solver with a modified `types.h` was built or scored.

## Reproduce

- Exact checks: `python3 -I evidence/scripts/vehicle_routing_time_windows/exact_checks.py <internal/cases/raw dir>`.
- Clarification proposal: `reproductions/vrptw-instruction-clarification/` (`agent-query.patch`, `checks.json`).
- Supporting records: the science/systems triage record (internal) §8.

