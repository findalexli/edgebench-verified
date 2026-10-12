# PFR Formalization (`pfr_formalization`)

**Decision:** Retain with note. Honest proofs of one theorem in two styles score identically, and no target was found that an honest, complete solution cannot reach.

## What the task asks for

The prompt asks the solver to "finish **all** sorries in this folder" and says "we value minor progress". It warns: "do not modify the signature of existing lemma/theorem/def as these changes will not pass the judge evaluation", and "we check the axioms transitively, finishing a theorem without completeing precedent lemma will not count." The score is the unweighted share of baseline `sorry`-dependent declarations that the submission turns into axiom-clean declarations with unchanged printed types. Category: Formal Math & Theorem Proving.

## What goes wrong

No material defect. Two possible problems were checked and ruled out.

**Compiler-generated targets are scored fairly here.** The same grader in `lean_analysis_proofs` credits compiler-generated helper targets (`X._proof_N`, `X._simp_N`, …) only when the exact generated name and printed type match; there, at least 49/2901 (1.69%) of targets are unattainable for any honest complete solution, and scores depend on proof style. In this task:

| targets | aux targets | aux share of score | fragile aux | `sorry` in type | P/¬P pairs | lower bound on unattainable |
|---|---|---|---|---|---|---|
| 423 | 7 | 1.65% | **0** | 0 (see below) | 0 | **0** |

The helper targets are 7 `_simp` lemmas, and none holds its own hole. An honest-proof test on one theorem:

| Submission | Original judge result |
|---|---|
| unmodified starter (control) | 0/423, no `type_changed`, no `disappeared` |
| style A (`Iff.rfl`) | 2/423: `mem_symmGroup` and `mem_symmGroup._simp_1` |
| style B (tactic) | 2/423: `mem_symmGroup` and `mem_symmGroup._simp_1` |

The `_simp` helper is credited, and the credit does not depend on proof style. The other six `_simp` helpers were not scored.

**Apparent `sorry` types are not holes.** A plain `sorry` search finds 5 targets: `PFR_projection`, `PFR_projection'`, `torsion_free_doubling`, `torsion_dist_shrinking` and `app_ent_PFR`. In all five, the token comes from `μ : autoParam (Measure Ω) sorry`, which is how the printer shows an auto-param tactic. An in-image probe confirms none of the five is a real hole, so none is an unattainable target.

The note that ships with the task: "Census: honest proofs in two styles score identically (2/423); 0 unattainable; 5 autoParam types print as sorry but are not holes".

## Impact

No score effect was found. The lower bound on unattainable targets is 0 of 423.

## Fix (v2)

No change; the note above ships with the task.

## How we know

- **Original evaluator in the pinned image.** The task's `judge.eval_cmd` ran verbatim in the judge image (`sha256:07b51e8e…09cc4`, toolchain v4.29.0), one container at a time with `--network none --memory 4g --cpus 2`. It scored the unmodified judge baseline sources, then two honest variants of `PFR/HundredPercent.lean` that prove `@[simp] mem_symmGroup` with `Iff.rfl` (A) and with `constructor <;> intro h <;> exact h` (B). The effective `ListDeclAxiom.lean` also checks HASH lines for `weak_PFR` and `entropic_PFR_conjecture`, which were true on the baseline.
- **Census inside the image.** The baseline `ListDeclAxiom` listing was built, and every target was classified with the same target rule and helper-name regex used for `lean_analysis_proofs`. An in-image probe checked whether each helper target holds a `sorry` of its own and whether a printed `sorry` in a type is a real hole.

## Limits

- No model or solver runs. Effects are shown only on authored controls and honest variants.
- The honest-proof test covers one theorem in one module.
- Submissions were built from the judge baseline sources. It was not checked that the work-image starter is identical to them.
- A solver that edits def or instance bodies (signatures unchanged) could still renumber transitive helpers. That was not measured.
- How much the `AddCombi` dependency overlaps the PFR content was not checked.
- The truth of individual targets was not checked.
- Whether the work image exposes upstream proofs was not checked.

## Reproduce

- Census: `evidence/scripts/lean_family_census/pipeline.sh <task_id> <image@digest> <project dir> <root module>`.
- Exact `eval_cmd` with honest variants: `evidence/scripts/lean_family_census/run_native.sh <task_id> <image@digest> evidence/scripts/lean_family_census/pfr_native PFR/HundredPercent.lean`.
- Outputs: `evidence/scripts/lean_family_census/out/pfr_formalization/`. The repaired set is in `native/repaired.txt`.
- Supporting records: `evidence/reviews/lean_family_aux_census.md`.
