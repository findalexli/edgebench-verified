# Ordinal Notation Well-Foundedness (`ordinal_notation_well_foundedness`)

Status: reviewed by the coordinator, 2026-10-12

- **Domain:** Formal Math & Theorem Proving
- **Decision:** Retain with note — the Coq grader credits honest closed proofs and rejects `Admitted` and axiom-based proofs. Two limits are not documented (the helper file-name filter and the 300 s compile limit), and targets 2–9 remain unproven.

## What the task promises

The prompt says: "Read `README.md` in the workspace, then complete as many Coq proof targets as possible." The README says: "A target receives credit only if the hidden checker's `Print Assumptions` output is closed under the global context. Proofs that rely on `Admitted`, new axioms, parameters, or other open assumptions … will not receive credit." It also says that solvers may add extra `.v` helper libraries and that "Shared helper libraries are submitted."

There are nine targets, weighted 1, 2, 2, 4, 4, 8, 16, 16 and 32 (maximum 85). Each target is `Acc (fun child parent => child_step parent child) L` for a fixed list L. task9's list equals `start` in `ChildOf.v`.

## What we checked and how

- **Source reading of the grader.** It removes compiled artifacts, then compiles every non-case `.v` file, support libraries first, retrying until no further file compiles. For each target it then runs `coqc taskN.v` and `coqc eval_taskN.v`. Credit requires both to compile and the eval output to contain "Closed under the global context". Each `eval_taskN.v` restates the exact target, so a changed statement cannot get credit. Each `coqc` call has a 300 s timeout.
- **Native runs of the original evaluator** in the pinned judge image (Coq 8.20.1, OCaml 4.13.1) with `--network none --memory 2g --cpus 2`.
  - An honest kernel-checked task1 proof.
  - The same proof with its lemmas moved into a helper library, `OrdHelpers.v`.
  - task3 proved from a new `Axiom`, as a negative control.
  - `Admitted` stubs for the other targets.
- **An independent transcription.** `explore.py` is a Python transcription of `ChildOf.v`. It agrees with Coq's own `Compute` output on six non-trivial expansions.
- **Searches.** A BFS (N ≤ 3, length ≤ 30) for descendant relations between targets, and a bounded cycle search (N ≤ 2, length ≤ 24, 200k nodes per target).
- Original identity: judge image `seededge/edgebench.judge.ordinal_notation_well_foundedness@sha256:272b80aa6554…`; key files `ordinal_notation_wf_eval.py` sha256 `0dd7c0a0…`, `ChildOf.v` `e002fc97…`, `eval_task1.v` `74993975…` through `eval_task9.v` `dc50634d…`. These match the earlier source export.

## What we found

**No grader defect found (the grader works as the README promises).**

| Submission | task1 | task2, task4–task9 (Admitted stubs) | task3 | Total |
|---|---|---|---|---|
| `sub_controls/` (honest task1 proof; task3 proved from a new `Axiom`) | **PASSED (1)** | FAILED: "assumptions were not closed", lists `taskN.WF` | **FAILED**, lists `task3.all_acc` | 1/85 |
| `sub_helper/` (the same task1 proof with its lemmas moved into a helper library `OrdHelpers.v`) | **PASSED (1)** | FAILED | FAILED | 1/85 |

- The task1 proof shows that `childOf [0;1] N` reduces to `repeat 0 (S N)`, and that every all-zero list steps only to its `removelast`. It then concludes by induction. Its `Print Assumptions` is "Closed under the global context".
- The negative controls list exactly the expected assumptions.

**Truth of the targets: task1 is true; tasks 2–9 are open.**

- All 8 other targets are descendants of `start` (task9's list). For example, `childOf [0;1;0;0;4] 2 = [0;1;0;0;3;3]`. `Acc` is closed under descendants, so task9 implies every other target.
- The bounded cycle search found **no cycle**, and a cycle would refute `Acc`. task1 and task2 were exhausted within the bounds; the others hit the node budget.
- `ChildOf.v` ships no ordinal interpretation and no reference proof. Whether the system is well-founded at `start` is a research-level question (task9 carries weight 32 of 85). No evidence was found that any target is false. Until a reference proof exists, the maximum score of 85 is unverified.

**Not material to scoring, but undocumented.** These were read from the task JSON and the grader. Neither was reproduced end to end.

- (a) `submit_exclude` silently drops helper files named `test*.v`, `check*.v`, `debug*.v`, `explore*.v`, `tmp*.v` or `scratch*.v`. The README says helper libraries are submitted. A proof that `Require`s such a file would fail to compile in the judge.
- (b) The 300 s per-`coqc` limit is not stated. A computation-heavy honest proof could hit it.

The eval files are visible to the solver. This does not matter, because they restate each target exactly.

An earlier audit inventoried the targets but left all proof-checker runtime work unexecuted and the task on hold. Re-checking in this release supplied the first native positive and negative controls.

## Note for users

No repair. The note says:

- The grader credits exactly the proofs whose `Print Assumptions` is closed. A kernel-checked honest proof of task1 is credited, and `Admitted` and axiom-based proofs are rejected.
- All nine targets are descendants of task9's list, so task9 implies the rest. Their well-foundedness beyond task1 has not been independently established. A false target would only cap scores and would never reward wrong work.
- Helper files whose names match `test*`, `check*`, `debug*`, `explore*`, `tmp*` or `scratch*` (`.v`) are excluded from submissions.
- Each Coq file has a 300 s compile limit.

## Limits and what was not run

- No model or solver re-runs. Effects are shown on authored controls only.
- Only task1 was proved. No reference proofs for tasks 2–9 exist in the shipped materials.
- The `submit_exclude` copy step was read from the task JSON, not executed.
- Bounded searches are not proofs.

## Reproduce

- `evidence/scripts/ordinal_notation_well_foundedness/run_native.sh <submission_dir>`, with `sub_controls/` and `sub_helper/` in the same folder. Expected outputs: `native_controls_output.txt` and `native_helper_output.txt`.
- `evidence/scripts/ordinal_notation_well_foundedness/explore.py` (output `explore_output.txt`) and `coq_check.v` (output `coq_check_output.txt`).
- Review: `evidence/reviews/ordinal_notation_well_foundedness.md`.
