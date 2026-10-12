# Sphere Eversion Formalization (`sphere_eversion_formalization`)

**Outcome:** Kept, with a note. No scored item is out of reach for an honest, complete solution, and the compiler-generated items are stable; this rests on test submissions and inspection only, and no honest proof was scored.

## What the task asks

The task is a Lean project on sphere eversion, the result that a sphere can be turned inside out smoothly. Lean is a language for machine-checked mathematical proofs, and `sorry` is Lean's placeholder for a missing proof. The task text asks the solver to "finish **all** sorries in this folder" and says "we value minor progress". It warns: "do not modify the signature of existing lemma/theorem/def as these changes will not pass the judge evaluation."

The score is the share of the starting project's declarations that depend on `sorry` and that the submission turns into declarations free of unapproved axioms, with unchanged printed types. Every scored item (target) has the same weight. Category: Formal Math & Theorem Proving.

## What we checked

No defect that changes scores enough to matter was found.

**What was checked.** Lean's compiler generates helper declarations automatically (`X._proof_N`, `X._simp_N`, …). The Lean grader shared by several tasks credits these auxiliary targets only when the exact generated name and printed type match. In the task `lean_analysis_proofs`, this makes at least 49/2901 (1.69%) of targets unreachable for any honest, complete solution, and makes scores depend on proof style. This task does not have that problem:

| Targets | Auxiliary targets | Auxiliary share of score | Fragile auxiliary targets | Targets with `sorry` in the type | Pairs of P and ¬P | Lower bound on unreachable targets |
|---|---|---|---|---|---|---|
| 661 | 119 | 18.0% | **0** | 0 | 0 | **0** |

- **Kinds of auxiliary targets:** 94 `_proof`, 23 `_simp`, and others.
- No auxiliary target holds a placeholder of its own ("fragile"). Each one is marked BAD only because it depends on a parent declaration that uses `sorry`. Honest proofs of those parent declarations should therefore leave it unchanged. This is inferred from a probe inside the grader image; no honest proof was scored.
- **Weighting.** Auxiliary targets are 18.0% of the score. By the probe, they should be earned automatically once the declarations they depend on are proved. This was not tested by scoring.
- **Scorer isolation** is outside this release's scope (an EdgeBench design choice). No scoring defect affecting honest solvers was found.

**Note shipped with the task.** "Census: 0 targets unattainable; aux targets 18.0% and stable (controls only, no honest-proof test)".

## How much it matters

No effect was measured. The lower bound on unreachable targets is 0 of 661.

No change is made; the note above ships with the task.

## How we checked it

- **Original grader in the original public image, pinned by digest** (toolchain v4.28.0). One container ran at a time, with `--network none`. The task's `judge.eval_cmd` ran exactly as written on the unmodified starting sources of the grader, as a test submission. It swaps in the shared starting `.lake` folder, whose Mathlib version differs from the one in the grader's repository, and rebuilds the whole project. The starting project scored 0/661, with no `type_changed` and no `disappeared`.
- **Count inside the image.** The starting `ListDeclAxiom` listing was built. Every target was then classified with the same target rule and auxiliary-name pattern used for `lean_analysis_proofs`. A probe inside the image checked whether each auxiliary target holds a `sorry` of its own. The `ListDeclAxiom.lean` actually in use prints a HASH line for `Gromov`, which was true on the starting project.
- No separate formal model applies; the count is itself a Lean run.

## Limits

- No AI model or solver runs were made. Effects are shown only on test submissions that we wrote.
- Only the unmodified starting project was scored by running the grader. No honest proof was scored. The stable/fragile classification comes from the probe inside the image, not from scoring runs.
- Test submissions were built from the grader's starting sources. Whether the starting project in the agent's work image is identical to them was not checked.
- A solver that edits the bodies of definitions or instances (with signatures unchanged) could still renumber transitive auxiliary declarations. That was not measured.
- Whether each individual target is true was not audited.
- Whether the work image exposes proofs from the source project was not checked.

## Reproduce

- Grader image digest: `sha256:1f6eae1d…486`.
- Census: `evidence/scripts/lean_family_census/pipeline.sh <task_id> <image@digest> <project dir> <root module>`.
- Run of the exact `eval_cmd` on a test submission: `evidence/scripts/lean_family_census/run_native.sh`. Its usage line is in the script header.
- Outputs: `evidence/scripts/lean_family_census/out/sphere_eversion_formalization/`.
- Pinned identity: task JSON sha256 `089f1248…17c4`; `eval_lean.py` sha256 `3319767e…`; effective `ListDeclAxiom.lean` `4b74bf12…`.
- Supporting records: `evidence/reviews/lean_family_aux_census.md`.
