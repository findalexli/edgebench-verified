# Sphere Eversion Formalization (`sphere_eversion_formalization`)

**Decision:** Retain with note. No target is out of reach for an honest, complete solution, and the auxiliary targets are stable; this rests on controls only, and no honest-proof variant was scored.

## What the task asks for

The prompt asks the solver to "finish **all** sorries in this folder" and says "we value minor progress". It warns: "do not modify the signature of existing lemma/theorem/def as these changes will not pass the judge evaluation." The score is the share of baseline `sorry`-dependent declarations that the submission turns into axiom-clean declarations with unchanged printed types. It is unweighted. Category: Formal Math & Theorem Proving.

## What goes wrong

No material defect was found.

**What was checked.** The shared Lean grader credits compiler-generated auxiliary targets (`X._proof_N`, `X._simp_N`, …) only when the exact generated name and printed type match. In `lean_analysis_proofs` this makes at least 49/2901 (1.69%) of targets unattainable for any honest complete solution, and makes scores depend on proof style. This task does not have that problem:

| targets | aux targets | aux share of score | fragile aux | `sorry` in type | P/¬P pairs | lower bound on unattainable |
|---|---|---|---|---|---|---|
| 661 | 119 | 18.0% | **0** | 0 | 0 | **0** |

- **Auxiliary kinds:** 94 `_proof`, 23 `_simp`, and others.
- No auxiliary target carries its own hole ("fragile"). Each is BAD only because it depends on a sorried parent declaration, so honest proofs of those declarations should leave it unchanged. This is inferred from an in-image probe; no honest-proof variant was scored.
- **Weighting.** Auxiliaries are 18.0% of the score. By the probe, they should be earned automatically once their dependencies are proved; this was not tested by scoring.
- **Scorer isolation** is outside this release's scope (an EdgeBench design choice); no good-faith scoring defect was found.

**Note shipped with the task.** "Census: 0 targets unattainable; aux targets 18.0% and stable (controls only, no honest-proof test)".

## Impact

None measured. The lower bound on unattainable targets is 0 of 661.

## Fix (v2)

No change; the note above ships with the task.

## How we know

- **Original evaluator in the pinned image.** The judge image (`sha256:1f6eae1d…486`, toolchain v4.28.0) ran one container at a time with `--network none`. The task's `judge.eval_cmd`, verbatim, ran on the unmodified judge baseline sources as a control. It swaps in the shared baseline `.lake`, whose Mathlib differs from the judge repo's, and rebuilds the whole project. The starter scored 0/661, with no `type_changed` and no `disappeared`.
- **Census inside the image.** The baseline `ListDeclAxiom` listing was built, and every target was classified with the same target rule and auxiliary-name regex used for `lean_analysis_proofs`. An in-image probe checked whether each auxiliary target holds a `sorry` of its own. The effective `ListDeclAxiom.lean` prints a HASH line for `Gromov`, which was true on the baseline.
- No separate formal model applies; the census is itself a Lean run.

## Limits

- No model or solver was run. Effects are shown only on authored controls.
- Only the unmodified-starter control was scored natively. No honest-proof variant was scored. The stable/fragile classification comes from the in-image probe, not from scoring runs.
- Submissions were built from the judge baseline sources. That the work-image starter is identical to them was not checked.
- A solver that edits def or instance bodies (signatures unchanged) could still renumber transitive auxiliaries. That was not measured.
- The truth of individual targets was not audited.
- Whether the work image exposes upstream proofs was not checked.

## Reproduce

- Census: `evidence/scripts/lean_family_census/pipeline.sh <task_id> <image@digest> <project dir> <root module>`.
- Exact `eval_cmd` control: `evidence/scripts/lean_family_census/run_native.sh`. Its usage line is in the script header.
- Outputs: `evidence/scripts/lean_family_census/out/sphere_eversion_formalization/`.
- Pinned identity: task JSON sha256 `089f1248…17c4`; `eval_lean.py` sha256 `3319767e…`; effective `ListDeclAxiom.lean` `4b74bf12…`.
- Supporting records: `evidence/reviews/lean_family_aux_census.md`.
