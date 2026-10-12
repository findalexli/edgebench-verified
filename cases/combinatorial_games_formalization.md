# Combinatorial Games Formalization (`combinatorial_games_formalization`)

Status: reviewed by the coordinator, 2026-10-12

- **Domain:** Formal Math & Theorem Proving
- **Decision:** Retain with note. A native test on one module shows that honest proofs in two styles earn identical credit, and the in-image census found no target out of reach for an honest, complete solution.

## What the task promises

The prompt asks the solver to "finish **all** sorries in this folder", says "we value minor progress", and warns: "do not modify the signature of existing lemma/theorem/def as these changes will not pass the judge evaluation."

The score is the share of baseline `sorry`-dependent declarations that the submission turns into axiom-clean declarations with unchanged printed types. It is unweighted.

## What we checked and how

- **Earlier hypothesis.** In `lean_analysis_proofs`, a native test found that the shared grader credits compiler-generated auxiliary targets (`X._proof_N`, `X._simp_N`, …) only when the exact generated name and printed type match. There, at least 49/2901 (1.69%) of targets cannot be reached by any honest complete solution, and scores depend on proof style. The hypothesis was that this defect applies to the whole Lean family. We tested it natively for this task.
- **Native runs in the pinned judge image.** The image was pulled by digest. One container ran at a time, with `--network none --memory 4g --cpus 2`. No Lean ran on the host.
- **Census inside the image.**
  - We recorded the effective grader files.
  - We built the baseline `ListDeclAxiom` listing.
  - We classified every target with the same target rule and auxiliary-name regex as the lean_analysis study.
  - An in-image probe checked whether each auxiliary target holds a `sorry` of its own ("fragile") or reaches `sorry` only through other constants.
- **Exact `eval_cmd`.** We ran the task's `judge.eval_cmd` verbatim. This included the `.lake`/manifest swap and the full `lake build`.
  - First run: the unmodified judge baseline sources.
  - Then two honest variants of one leaf module, `SignExpansion/Basic.lean`.
- **Original identity.**
  - Judge image: `…@sha256:3e1062c6…7efa`, toolchain v4.28.0.
  - Task JSON: sha256 `fca494f2…f531`. Export tar: sha256 `81ee62f9…7835`.
  - `eval_lean.py`: sha256 `3319767e…`, the same in all Lean tasks.
  - Effective `ListDeclAxiom.lean`: `5edb20a7…`. It prints no HASH lines.

## What we found

**Auxiliary-name defect: Refuted for this task.** The hypothesis that the lean_analysis defect applies here was tested natively and rejected.

Census numbers:

| targets | aux targets | aux share of score | fragile aux | `sorry` in type | P/¬P pairs | lower bound on unattainable |
|---|---|---|---|---|---|---|
| 3732 | 937 | 25.1% | **0** | 0 | 0 | **0** |

- **Auxiliary kinds:** 450 `_simp`, 432 `_proof`, 25 `_unsafe_rec`, 13 `eq_def`, 8 `eq_N`, and others.
- **Duplicate types.** A lexical count finds duplicate types for 33 auxiliaries (the classifier lists them as "likely unattainable"). The probe classes every one of them as transitive-only: it carries no hole of its own, so by the census's reasoning an honest proof never re-elaborates it and they are not at risk. This was not tested by scoring beyond the one-module test below.

**Native honest-proof test.** Six sorried theorems in `SignExpansion/Basic.lean` were proved honestly, with no signature change:
- `isUpperSet_preimage_singleton_zero`
- `copy_eq`
- `coe_mk`
- `sign_eq_coe`
- `le_iff_toLex`
- `lt_iff_toLex`

There were two styles: term mode (A) and tactic mode (B).

| Submission | Original judge result |
|---|---|
| unmodified starter (control) | 0/3732, no `type_changed`, no `disappeared` |
| style A (term mode) | 16/3732 |
| style B (tactic mode) | 16/3732, identical repaired set |

- **What the 16 targets are:** the 6 theorems, `copy`, `instBoundedOrder`, and 7 auxiliaries (`copy._proof_1`, `instBoundedOrder._proof_1/_2`, `instCompleteLinearOrder._proof_1…5`).
- Nothing was type-changed or disappeared.
- Auxiliary targets are credited, and the credit does not depend on proof style.
- **Mathlib swap.** The control score of 0 also holds after `eval_cmd` swaps in the shared baseline `.lake` and rebuilds the whole project. That `.lake` holds a Mathlib that differs from the judge repo's.
- **Why this differs from lean_analysis.** This starter was made by replacing *theorem* bodies with `sorry`. Auxiliary targets are BAD only because their upstream proof terms call a sorried theorem. They are earned automatically once those theorems are proved.

**Weighting skew: Not material.** Auxiliaries are 25.1% of the score. They are earned automatically once their dependencies are proved, so this is a weighting skew, not unfairness.

**Scorer isolation.** Scorer isolation is outside this release's scope (EdgeBench design choice); no good-faith scoring defect was found.

**Earlier withholding.** An earlier source-only review proposed withholding the original task because of grader-robustness concerns. Under this release's scope, those concerns are scorer isolation. The native re-check of the good-faith question found no defect that affects an honest submission.

**Earlier setup records.** The family's earlier "setup failures" were failures of the audit's own infrastructure, not task defects. No setup failure specific to this task was recorded, only pending controls.

## Note for users

No repair. The note says: "Shared Lean grader: native census shows honest term- and tactic-style proofs earn identical credit (16/3732); 0 targets unattainable; aux targets 25.1% of weight but stable".

## Limits and what was not run

- No model or solver re-runs were done. Effects are shown only on authored controls and honest variants.
- The native honest test covers one leaf module only.
- Submissions were built from the judge baseline sources. We did not check that the work-image starter is identical to them.
- A solver that edits def or instance bodies (signatures unchanged) could still renumber transitive auxiliaries. That was not measured.
- Whether every sorried item has an upstream proof is unknown, because the upstream library is still under development. The truth of individual targets was not audited.
- Whether the work image exposes upstream proofs was not checked.
- The first full-build run was interrupted by a host out-of-memory restart caused by concurrent jobs. It was rerun under the heavy-job lock.

## Reproduce

- Census: `evidence/scripts/lean_family_census/pipeline.sh <task_id> <image@digest> <project dir> <root module>`.
- Exact `eval_cmd` with honest variants: `evidence/scripts/lean_family_census/run_native.sh <task_id> <image@digest> evidence/scripts/lean_family_census/cg_native SignExpansion/Basic.lean`.
- Outputs: `evidence/scripts/lean_family_census/out/combinatorial_games_formalization/`. The repaired set is in `native/repaired.txt`.
- Supporting records: `evidence/reviews/lean_family_aux_census.md`.

