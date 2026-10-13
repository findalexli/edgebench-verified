# ordinal_notation_well_foundedness: fresh good-faith triage

> **Note (2026-10-12).** Superseded statement below: that targets 2–9 are open. The targets form a chain (each reaches the one below it), and the publisher's results show 21/85, the weight of tasks 1–6, so closed proofs of tasks 1–6 exist; tasks 7–9 remain open. See `cases/ordinal_notation_well_foundedness.md`.

## Claim under review

Earlier state (TASKS.md): "Review pending | Historical formal-source facts retained (L). | Held |
Held; no follow-up." Earlier `audit/reviews/formal_tasks.txt` lines 191-225 inventoried the 9 exact
targets and gave a hand-derived plan for a task1 positive control. It stated: "All proof-checker
runtime work remains unexecuted", and "This audit does not establish well-foundedness of the
high-weight targets."

Questions for this review: what is graded, does the prompt match the grader, does the grader credit
honest proofs and reject non-proofs, and are the target statements true?

## Pinned artifacts

- Task `tasks/ordinal_notation_well_foundedness.json`: eval_cmd `python3 /opt/sebench/ordinal_notation_wf_eval.py`,
  rescale linear 0..85, `submit_exclude` includes `eval_task*.v`, `ChildOf.v`, `test*.v`, `check*.v`,
  `debug*.v`, `explore*.v`, `tmp*.v` and `scratch*.v`.
- Judge image `seededge/edgebench.judge.ordinal_notation_well_foundedness@sha256:272b80aa65542b24a19ecca09f4a3156f927c6eba15aeb484c76b921ec8c46a8`
  (pulled locally). It contains **Coq 8.20.1** (OCaml 4.13.1).
- File sha256 values in the image: `ordinal_notation_wf_eval.py` 0dd7c0a0…, `ChildOf.v` e002fc97…,
  `eval_task1.v` 74993975… through `eval_task9.v` dc50634d… (full list in the session log). These
  match the earlier source export.

## Contract

README: "A target receives credit only if the hidden checker's `Print Assumptions` output is closed
under the global context. Proofs that rely on `Admitted`, new axioms, parameters, or other open
assumptions … will not receive credit." Weights: task1 = 1, task2 = 2, task3 = 2, task4 = 4,
task5 = 4, task6 = 8, task7 = 16, task8 = 16, task9 = 32 (maximum 85). "You may … add extra `.v`
helper libraries … Shared helper libraries are submitted."

Each target is `Acc (fun child parent => child_step parent child) L`, for L =
[0;1], [0;1;0;0;3], [0;1;0;0;3;3], [0;1;0;0;4], [0;1;0;1], [0;1;0;2], [0;1;0;2;0;0;2],
[0;1;0;2;0;0;2;0;0;2] and [0;1;0;2;0;3]. The last list equals `start` in ChildOf.v.

## What the grader does

The grader removes compiled artifacts and compiles every non-case `.v` file (support libraries
first, retrying until no further file compiles). Then, for each target in order, it runs
`coqc taskN.v` and `coqc eval_taskN.v`. Credit requires both to compile and the eval output to
contain "Closed under the global context". Each `eval_taskN.v` restates the exact target
(`WF_def`), proves `WF'` by `apply taskN.WF`, and prints its assumptions. A changed statement in
taskN.v therefore cannot get credit. Each `coqc` call has a 300 s timeout.

## Independent reproduction (original evaluator, judge image, `--network none --memory 2g --cpus 2`)

`scripts/ordinal_notation_well_foundedness/run_native.sh <submission_dir>` copies the submission
files over the workspace and runs the original evaluator.

| Submission | task1 | task2, task4–task9 (Admitted stubs) | task3 | Total |
|---|---|---|---|---|
| `sub_controls/` (honest task1 proof; task3 proved from a new `Axiom`) | **PASSED (1)** | FAILED: "assumptions were not closed", lists `taskN.WF` | **FAILED**, lists `task3.all_acc` | 1/85 |
| `sub_helper/` (the same task1 proof with its lemmas moved into a helper library `OrdHelpers.v`) | **PASSED (1)** | FAILED | FAILED | 1/85 |

Outputs: `native_controls_output.txt`, `native_helper_output.txt`. The task1 proof shows that
`childOf [0;1] N` reduces to `repeat 0 (S N)`, and that every all-zero list steps only to its
`removelast`. It then concludes by induction. Its `Print Assumptions` is closed. The grader therefore
credits an honest closed proof, including one that uses a submitted helper library, and rejects
`Admitted` and new axioms.

## Truth of the target statements

- `explore.py` is a direct Python transcription of ChildOf.v. It agrees with Coq's own `Compute`
  output on six non-trivial expansions (`coq_check.v`, `coq_check_output.txt`).
- **All 8 other targets are descendants of `start` = task9's list.** A BFS with N ≤ 3 and length ≤ 30
  reaches each of them, for example `childOf [0;1;0;0;4] 2 = [0;1;0;0;3;3]`. `Acc` is closed under
  descendants, so task9 implies every other target. If task9 is true, all targets are true.
- Bounded cycle search (N ≤ 2, length ≤ 24, 200k nodes per target) found **no cycle**. A cycle would
  refute `Acc`. task1 and task2 are exhausted within the bounds. The others hit the node budget.
- task1 is now **kernel-checked true**.
- Tasks 2–9 are open. ChildOf.v ships no ordinal interpretation and no reference proof. Whether this
  pointer-sequence system is well-founded at `start` is a research-level question (task9 has weight
  32 of 85). Bounded exploration can refute such a claim but cannot confirm it. I found no evidence
  that any target is false.

## Refutation attempts and good-faith pitfalls

- *Could the grader credit a non-proof?* Not through honest paths: `Admitted` and `Axiom` are both
  rejected. Tampering is out of scope.
- *Could it fail an honest proof?* Yes, in two ways the README does not document. Neither was
  reproduced end-to-end, because they concern the harness's file-copy step and its timeouts.
  - (a) `submit_exclude` silently drops helper files named `test*.v`, `check*.v`, `debug*.v`,
    `explore*.v`, `tmp*.v` or `scratch*.v`. The README says helper libraries are submitted, but a
    task that `Require`s such a file would fail to compile in the judge.
  - (b) Each `coqc` call is capped at 300 s, which is also undocumented. Computation-heavy honest
    proofs could hit it.

  Both are documentation issues, not grading errors.
- *Does `eval_taskN.v` need to be hidden?* The eval files are visible to the solver. This does not
  matter, because they restate the target exactly.

## Formal check

- Coq 8.20.1 kernel, inside the judge image. task1 `WF'` reports "Closed under the global context"
  (no axioms).
- The negative controls list exactly the expected assumptions (`taskN.WF` for `Admitted`,
  `task3.all_acc` for the axiom).
- Lean was not used, because the task is in Coq.

## Verdict

- **Grader: no good-faith defect found.** Native positive and negative controls behave as the README
  promises.
- **Statements:** task1 is proved true. task2–task9 are unresolved but consistent: no cycles found,
  and all of them lie below `start`, so task9 implies the rest.
- **Minor documentation gaps:** the helper-name exclusions and the 300 s per-file limit.

## Disposition assessment

Recommended: **retain-eligible with a note**, pending a domain reference for the notation's
well-foundedness or, ideally, a reference proof for task9. Until then the maximum score of 85 is
unverified (the attainable maximum is unknown). Since task9 implies all the others, one reference
proof of task9 would settle the whole task. A plain note will also do if the benchmark accepts
open-problem targets: graders credit only real proofs, so a false target would only cap scores and
would never reward wrong work.

## Recommended publishable wording

"The Coq grader credits exactly the proofs whose `Print Assumptions` is closed. A kernel-checked
honest proof of task1 is credited, and `Admitted` and axiom-based proofs are rejected. All nine
targets are descendants of task9's list, so task9 implies the rest. Their well-foundedness beyond
task1 has not been independently established."

## Repair note

No defect needs repair. Suggested documentation additions: list the helper-file name patterns that
are excluded from submissions, and state the 300 s per-file compile limit.

## Limits

- Only task1 was proved. No reference proofs for tasks 2–9 exist in the shipped materials.
- The submission copy step (`submit_exclude`) was read from the task JSON and not executed.
- Bounded searches are not proofs.
