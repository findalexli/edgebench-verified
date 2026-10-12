# PFR Formalization (`pfr_formalization`)

Status: reviewed by the coordinator, 2026-10-12

- **Domain:** Formal Math & Theorem Proving
- **Decision:** Retain with note. Native tests show that honest proofs of one theorem in two styles score identically. The census lower bound on targets out of reach for an honest, complete solution is 0 (the truth of individual targets was not audited).

## What the task promises

The prompt asks the solver to "finish **all** sorries in this folder" and says "we value minor progress". It warns: "do not modify the signature of existing lemma/theorem/def as these changes will not pass the judge evaluation." It also says that "we check the axioms transitively, finishing a theorem without completeing precedent lemma will not count."

The score is the share of baseline `sorry`-dependent declarations that the submission turns into axiom-clean declarations with unchanged printed types. It is unweighted.

## What we checked and how

- **Earlier hypothesis.** In `lean_analysis_proofs`, a native test found that the shared grader credits compiler-generated auxiliary targets (`X._proof_N`, `X._simp_N`, …) only when the exact generated name and printed type match. There, at least 49/2901 (1.69%) of targets are unattainable for any honest complete solution, and scores depend on proof style. The hypothesis was that this defect applies to the whole Lean family. We tested it natively for this task.
- **Native runs in the pinned judge image.** The image was pulled by digest and removed afterwards. One container ran at a time, with `--network none --memory 4g --cpus 2`. No Lean ran on the host.
- **Census inside the image.**
  - We recorded the effective grader files.
  - We built the baseline `ListDeclAxiom` listing.
  - We classified every target with the same target rule and auxiliary-name regex as the lean_analysis study.
  - An in-image probe checked whether each auxiliary target holds a `sorry` of its own ("fragile") and whether a printed `sorry` in a type is a real hole.
- **Exact `eval_cmd`.** We ran the task's `judge.eval_cmd` verbatim.
  - First run: the unmodified judge baseline sources.
  - Then two honest variants of `PFR/HundredPercent.lean`. Each proves `@[simp] mem_symmGroup`, one with `Iff.rfl` (A) and one with `constructor <;> intro h <;> exact h` (B).
- **Original identity.**
  - Judge image: `…@sha256:07b51e8e…09cc4`, toolchain v4.29.0.
  - Task JSON: sha256 `d26b45a9…77d0`. Export tar: sha256 `61f3cc08…584` (not recorded in the saved evidence).
  - `eval_lean.py`: sha256 `3319767e…`.
  - Effective `ListDeclAxiom.lean`: `0ea47b53…`. It prints HASH lines for `weak_PFR` and `entropic_PFR_conjecture`, which were true on the baseline.

## What we found

**Auxiliary-name defect: Refuted for this task.** The hypothesis that the lean_analysis defect applies here was tested natively and rejected.

Census numbers:

| targets | aux targets | aux share of score | fragile aux | `sorry` in type | P/¬P pairs | lower bound on unattainable |
|---|---|---|---|---|---|---|
| 423 | 7 | 1.65% | **0** | 0 (see below) | 0 | **0** |

The auxiliary targets are 7 `_simp` lemmas. The probe found that none holds its own hole. One of them, `mem_symmGroup._simp_1`, was credited natively; the other six were not scored.

**Native honest-proof test.**

| Submission | Original judge result |
|---|---|
| unmodified starter (control) | 0/423, no `type_changed`, no `disappeared` |
| style A (`Iff.rfl`) | 2/423: `mem_symmGroup` and `mem_symmGroup._simp_1` |
| style B (tactic) | 2/423: `mem_symmGroup` and `mem_symmGroup._simp_1` |

The `_simp` auxiliary is credited, and the credit does not depend on proof style.

**Apparent `sorry` types: Refuted as holes.** A plain `sorry` search finds 5 targets:
- `PFR_projection`
- `PFR_projection'`
- `torsion_free_doubling`
- `torsion_dist_shrinking`
- `app_ent_PFR`

In all five, the token comes from `μ : autoParam (Measure Ω) sorry`, which is how the printer shows an auto-param tactic. The in-image real-hole probe is false for all five. They are not unattainable targets.

**Scorer isolation.** Scorer isolation is outside this release's scope (EdgeBench design choice); no good-faith scoring defect was found.

**Earlier withholding.** An earlier source-only review proposed withholding the original task because of grader-robustness concerns. Under this release's scope, those concerns are scorer isolation. The native re-check of the good-faith question found no defect that affects an honest submission.

**Earlier setup records.** An earlier "setup failure" record was a failure of the audit's own infrastructure, not a task defect. A fixed-version step returned -11 in the audit's own restoration route, not in the original image. No log of that earlier record is saved in this repository.

## Note for users

No repair. The note says: "Census: honest proofs in two styles score identically (2/423); 0 unattainable; 5 autoParam types print as sorry but are not holes".

## Limits and what was not run

- No model or solver re-runs were done. Effects are shown only on authored controls and honest variants.
- The native honest test covers one theorem in one module.
- Submissions were built from the judge baseline sources. We did not check that the work-image starter is identical to them.
- A solver that edits def or instance bodies (signatures unchanged) could still renumber transitive auxiliaries. That was not measured.
- We did not check how much the `AddCombi` dependency overlaps the PFR content.
- The truth of individual targets was not audited.
- Whether the work image exposes upstream proofs was not checked.

## Reproduce

- Census: `evidence/scripts/lean_family_census/pipeline.sh <task_id> <image@digest> <project dir> <root module>`.
- Exact `eval_cmd` with honest variants: `evidence/scripts/lean_family_census/run_native.sh <task_id> <image@digest> evidence/scripts/lean_family_census/pfr_native PFR/HundredPercent.lean`.
- Outputs: `evidence/scripts/lean_family_census/out/pfr_formalization/`. The repaired set is in `native/repaired.txt`.
- Supporting records: `evidence/reviews/lean_family_aux_census.md`.

