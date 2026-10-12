# FLT Regular Formalization (`flt_regular_formalization`)

**Outcome:** Kept, with a note. The weighted list of scored statements matches the task's own list exactly and contains no compiler-generated names, so no statement was found out of reach for an honest, complete solution.

## What the task asks

The solver works in a project on Fermat's Last Theorem written in Lean 4, a language for machine-checked math proofs. The prompt asks the solver to "finish **all** sorries in this folder" (a `sorry` is a placeholder for a missing proof) and says "we value minor progress". It warns: "Do not modify the signature of existing lemma/theorem/def as these changes will not pass the judge evaluation." It also says that "finishing `fermatLastTheoremSeven` without completeing `isRegularPrime_seven` and `flt_regular` will not count." Unlike the other Lean tasks, this one is scored in weighted mode: a weights file lists 25 declarations with total weight 87. Category: Formal Math & Theorem Proving.

## What we checked

There is no problem that changes scores enough to matter. What was checked:

- **Compiler-generated targets.** The Lean grader shared by several tasks credits targets that the compiler generates (names such as `X._proof_N`, `X._simp_N`, …) only when the exact generated name and printed type match. In `lean_analysis_proofs` this puts at least 49/2901 (1.69%) of targets out of reach for any honest, complete solution. It does not apply here, because no target is compiler-generated:

| Targets (weight) | Compiler-generated targets | Their share of the score | Fragile generated targets | `sorry` in type | P/¬P pairs | Lower bound on targets out of reach |
|---|---|---|---|---|---|---|
| 25 (weight 87) | **0** | 0% | 0 | 0 | 0 | **0** |

- **Weights file.** It has 25 entries, with weights from 1 to 6 and a total of 87. Those entries are exactly the 25 declarations marked BAD and containing `sorry` in the starting listing, and all 25 type texts equal the listing's.

Note: the README groups the score into 100 points, but the grader uses weights totalling 87. This is a mismatch in the documentation only.

The note says: "Census: 25 weighted targets (total weight 87) match the listing exactly; no aux targets; 0 unattainable".

The task is not changed; the note above ships with it.

## How much it matters

No target is out of reach for an honest, complete solution (lower bound 0). The README's grouping into 100 points does not change any score.

## How we checked it

- **Original grader, from the public image pinned by digest** (toolchain v4.28.0). It ran one container at a time with `--network none --memory 4g --cpus 2`. The task's `judge.eval_cmd` ran verbatim on the unmodified baseline sources in the grader image. The command includes the swap to the shared baseline `.lake` and a full rebuild. The unmodified starter scored 0/25 (weight 0/87), with no `type_changed` and no `disappeared`. This holds even though the swapped-in `.lake` holds a Mathlib (Lean's math library) that differs from the one in the grader's repository.
- **Count inside the image.** We recorded the grader files actually used and built the baseline `ListDeclAxiom` listing. The listing prints a HASH line for `flt_regular`, which was true on the baseline. We compared the weights-file entries with the listing's BAD declarations that contain `sorry`, and with their printed types.
- **Axioms.** Credit requires declarations that use no extra axioms, checked through `ListDeclAxiom`.

## Limits

- No AI model or solver was run. Effects are shown only on the test submissions we wrote.
- Only the unmodified starter was scored on the grader. No variant with honest proofs was scored for this task.
- Submissions were built from the baseline sources in the grader image. Whether the starter in the work image is identical to them was not checked.
- Whether each individual target is true was not checked.
- Whether the work image exposes the upstream proofs was not checked. The upstream project is complete and public, and parts of it are in Mathlib.
- Scorer isolation is outside this release's scope (EdgeBench design choice).

## Reproduce

- Grader image: `sha256:c8b50a05…`.
- Count of targets: `evidence/scripts/lean_family_census/pipeline.sh <task_id> <image@digest> <project dir> <root module> FltRegular_weight.json`.
- Exact `eval_cmd` run: `evidence/scripts/lean_family_census/run_native.sh`. Its usage line is in the script header.
- Outputs: `evidence/scripts/lean_family_census/out/flt_regular_formalization/`. The weights-file entries and their weights are listed in `classify.txt`; the weights file itself is not included.
- Supporting records: `evidence/reviews/lean_family_aux_census.md`.
