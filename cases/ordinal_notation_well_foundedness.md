# Ordinal Notation Well-Foundedness (`ordinal_notation_well_foundedness`)

**Outcome:** Kept, with a note. <mark>The Coq grader credits complete, correct proofs and rejects `Admitted` and axiom-based proofs, but the task does not document two limits (the filter on helper file names and the 300 s compile limit). The publisher's results show closed proofs of targets 1 to 6; whether targets 7 to 9 (64 of 85 points) can be proved is not known.</mark>

## What the task asks

The solver proves statements in Coq, a language for machine-checked mathematical proofs. Each statement says that a step-by-step list-rewriting process always terminates from a given starting list. The task text says: "Read `README.md` in the workspace, then complete as many Coq proof targets as possible." The README says: "A target receives credit only if the hidden checker's `Print Assumptions` output is closed under the global context. Proofs that rely on `Admitted`, new axioms, parameters, or other open assumptions … will not receive credit." Solvers may add extra `.v` helper libraries, and "Shared helper libraries are submitted."

There are nine targets, weighted 1, 2, 2, 4, 4, 8, 16, 16 and 32 (maximum 85). Each target is `Acc (fun child parent => child_step parent child) L` for a fixed list L. `Acc` is Coq's accessibility predicate, which holds when every chain of steps from L is finite. task9's list equals `start` in `ChildOf.v`. Category: Formal Math & Theorem Proving.

## What we checked

We found no grader defect. The grader removes compiled files, then compiles every `.v` file that is not a target file, support libraries first, retrying until no further file compiles. For each target it runs `coqc taskN.v` and `coqc eval_taskN.v`. A target gets credit only if both compile and the output of the eval file contains "Closed under the global context". Each `eval_taskN.v` restates the exact target, so a changed statement cannot get credit. The solver can see the eval files, which does no harm because they restate each target exactly.

| Submission | task1 | task2, task4 to task9 (`Admitted` placeholders) | task3 | Total |
|---|---|---|---|---|
| `sub_controls/` (genuine task1 proof; task3 proved from a new `Axiom`) | **PASSED (1)** | FAILED: "assumptions were not closed", lists `taskN.WF` | **FAILED**, lists `task3.all_acc` | 1/85 |
| `sub_helper/` (the same task1 proof with its lemmas moved into a helper library `OrdHelpers.v`) | **PASSED (1)** | FAILED | FAILED | 1/85 |

The test submissions that should fail list exactly the expected assumptions.

Tasks 1 to 6 are true, and whether tasks 7 to 9 are true is open.

- The targets form a chain, in which each target's list is reachable from the next one's (task k+1 reaches task k for every k; breadth-first search with N ≤ 3 and lists of length ≤ 30, `chain_check.py`). For example, `childOf [0;1;0;0;4] 2 = [0;1;0;0;3;3]` (task4 to task3). `Acc` carries over to descendants, so a proof of task k implies tasks 1 to k, and task9 implies every target.
- We prove task1 here (below). The publisher's per-task results (`tasks/README.md`, ordinal row) show Opus 4.8 and GPT-5.5 at 24.7 out of 100 from 4 to 6 hours on, which is 21/85. Because proofs carry down the chain, a solver's credited targets are in practice a prefix of the chain, and the prefix weights are 1, 3, 5, 9, 13, 21, 37, 53, 85. 21 is the weight of exactly tasks 1 to 6. The grader credits only proofs whose `Print Assumptions` is closed (checked below), so closed proofs of tasks 1 to 6 exist.
- A bounded search for cycles, any one of which would disprove `Acc`, found **no cycle**. For task1 and task2 the search exhausted the space within the bounds; for the others it hit the limit on nodes.
- `ChildOf.v` ships no interpretation as ordinals and no reference proof. Whether the system is well-founded at task7, task8 and `start` (task9) is open; these carry 16 + 16 + 32 = 64 of the 85 points. We found no evidence that any target is false. Until proofs of task7 to task9 exist, the maximum score of 85 is unverified.

Two limits are undocumented. We read both from the task JSON and the grader and reproduced neither end to end.

- (a) `submit_exclude` silently drops helper files named `test*.v`, `check*.v`, `debug*.v`, `explore*.v`, `tmp*.v` or `scratch*.v`. The README says helper libraries are submitted. A proof that `Require`s such a file would fail to compile in the grader.
- (b) The task does not state the 300 s limit on each `coqc` call. A correct proof that relies on heavy computation could hit it.

The task ships with this note.

- The grader credits exactly the proofs whose `Print Assumptions` is closed. It credits a kernel-checked proof of task1 and rejects `Admitted` and axiom-based proofs.
- The nine targets form a chain, so each target implies all lower ones. Published results show closed proofs of tasks 1 to 6 (21 of 85 points); tasks 7 to 9 (64 points) have no known proof. A false target would only cap scores and would never reward wrong work.
- Submissions leave out helper files whose names match `test*`, `check*`, `debug*`, `explore*`, `tmp*` or `scratch*` (`.v`).
- Each Coq file has a 300 s compile limit.

## How much it matters

We found no effect on the scores of correct proofs. The file-name filter affects only solvers who give a required helper file one of the excluded prefixes, and their proofs that depend on it fail to compile. The time limit affects only proofs that rely on heavy computation. If task7, task8 or task9 were false, every solver's maximum would drop by that target's weight and the weights above it. No such target is known.

The task does not change; the note above ships with it.

## How we checked it

- We ran the original grader in the original public image, pinned by digest (Coq 8.20.1, OCaml 4.13.1), with `--network none --memory 2g --cpus 2` on the two submissions above. They contain a kernel-checked task1 proof, the same proof with its lemmas in `OrdHelpers.v`, task3 proved from a new `Axiom` as a test submission that should fail, and `Admitted` placeholders for the other targets.
- As a formal check in Coq, the task1 proof shows that `childOf [0;1] N` reduces to `repeat 0 (S N)`, and that every all-zero list steps only to its `removelast`. It then concludes by induction. Its `Print Assumptions` is "Closed under the global context", so it uses no axioms.
- As an independent transcription, `explore.py` reimplements `ChildOf.v` in Python and agrees with Coq's own `Compute` output on six non-trivial expansions. It drove a breadth-first search (BFS; N ≤ 3, length ≤ 30) for descendant relations between targets, and the bounded cycle search (N ≤ 2, length ≤ 24, 200k nodes per target).

## Limits

- We ran no AI model or solver. The effects shown come only from test submissions that we wrote.
- We proved only task1. That tasks 2 to 6 are provable rests on the publisher's results (21/85) and on the grader's closed-assumptions check; no proof of them is in the shipped materials or in this repository. The leaderboard values that are not multiples of 1/85 (for example 18.4) suggest averages over several runs, which the publisher does not state.
- We read the `submit_exclude` copy step from the task JSON and did not execute it.
- Bounded searches are not proofs.

## Reproduce

- Grader image digest: `sha256:272b80aa6554…`.
- `evidence/scripts/ordinal_notation_well_foundedness/run_native.sh <submission_dir> <out_file>`, with `sub_controls/` and `sub_helper/` in the same folder. Expected outputs: `native_controls_output.txt` and `native_helper_output.txt`.
- `evidence/scripts/ordinal_notation_well_foundedness/explore.py` (output `explore_output.txt`), `chain_check.py` (output `chain_check_output.txt`) and `coq_check.v` (output `coq_check_output.txt`).
- Review: `evidence/reviews/ordinal_notation_well_foundedness.md`.
