# Carleson Formalization (`carleson_formalization`)

Status: reviewed by the coordinator, 2026-10-12

- **Domain:** Formal Math & Theorem Proving
- **Decision:** Retain with note. The native census found no target that an honest, complete solution cannot reach. The note covers a sorried data definition and the unfinished upstream project.

## What the task promises

The prompt asks the solver to "finish **all** sorries in this folder" and says "we value minor progress". It warns: "do not modify the signature of existing lemma/theorem/def as these changes will not pass the judge evaluation." It also says "we check the axioms transitively, finishing a theorem without completeing precedent lemma will not count."

The score is the share of baseline `sorry`-dependent declarations that the submission turns into axiom-clean declarations with unchanged printed types. It is unweighted.

## What we checked and how

- **Earlier hypothesis.** In `lean_analysis_proofs`, a native test found that the shared grader credits compiler-generated auxiliary targets (`X._proof_N`, `X._simp_N`, …) only when the exact generated name and printed type match. There, at least 49/2901 (1.69%) of targets are unattainable for any honest complete solution, and scores depend on proof style. The hypothesis was that this defect applies to the whole Lean family. We tested it natively for this task.
- **Native runs in the pinned judge image.** The image was pulled by digest and removed afterwards. One container ran at a time, with `--network none --memory 4g --cpus 2`. No Lean ran on the host.
- **Census inside the image.**
  - We recorded the effective grader files.
  - We built the baseline `ListDeclAxiom` listing.
  - We classified every target with the same target rule and auxiliary-name regex as the lean_analysis study.
  - An in-image probe checked whether each auxiliary target holds a `sorry` of its own ("fragile").
- **Exact `eval_cmd`.** We ran the task's `judge.eval_cmd` verbatim on the unmodified judge baseline sources as a control. No honest-proof variant was scored for this task.
- **Proof style and auxiliary names.** A core-Lean check with this image's compiler (4.30.0-rc2) tested an `@[simp]` iff theorem proved by `sorry`, by a term, by `omega` and by `simp`. In every case it got its auxiliary under the same name (`_simp_1`) and the same type.
- **Original identity.**
  - Judge image: `…judge.carleson_formalization@sha256:dd9aab33…a2f`, toolchain v4.30.0-rc2.
  - Task JSON: sha256 `361cef52…8526`. Export tar: sha256 `58553216…7e5`.
  - `eval_lean.py`: sha256 `3319767e…`.
  - Effective `ListDeclAxiom.lean`: `7ad881a0…`. It prints a HASH line for `classical_carleson_check`, which was true on the baseline.

## What we found

**Auxiliary-name defect: Refuted for this task.** The hypothesis that the lean_analysis defect applies here was tested natively and rejected.

Census numbers:

| targets | aux targets | aux share of score | fragile aux | `sorry` in type | P/¬P pairs | lower bound on unattainable |
|---|---|---|---|---|---|---|
| 3004 | 151 | 5.0% | **0** | 0 | 0 | **0** |

- **Auxiliary kinds:** 90 `_proof`, 19 `_simp`, 11 `congr_simp`, 10 `eq_def`, and others.
- **Duplicate types.** A lexical count finds duplicate types for 8 auxiliaries. All of them are transitive-only and not at risk.
- **Control.** The unmodified starter scored 0/3004, with no `type_changed` and no `disappeared`.

**Sorried data definition: Not material to scoring fairness.** `ToMathlib/RealInterpolation/LorentzInterpolation.lean` contains a *data* definition, `C_LorentzInterpolation := sorry`.
- Any value earns that target's credit, and downstream bounds may become easier.
- This looks like unfinished upstream work.
- The finding comes from the source review and was not tested natively.

**Upstream completeness: Not checked.** The upstream project completed its main theorem, but the project is unfinished. Some targets may have no upstream proof.

**Scorer isolation.** Scorer isolation is outside this release's scope (EdgeBench design choice); no good-faith scoring defect was found. The sorried data definition above is recorded as a note.

**Earlier withholding.** An earlier source-only review proposed withholding the original task because of grader-robustness concerns. Under this release's scope, those concerns are scorer isolation. The native census found no good-faith defect that would justify withholding.

**Earlier setup records.** An earlier "setup failure" record was a failure of the audit's own infrastructure, not a task defect.
- It was a signal 11 during `lean --version`, inside the audit's own selectively restored root filesystem. That route did not use `docker run`.
- The saved records themselves call it an "own selective-environment failure, not upstream defect".

## Note for users

No repair. The note says: "Census: 0 targets unattainable, aux targets 5.0% and stable; a sorried data definition (C_LorentzInterpolation) admits any value; upstream project unfinished, so some targets may lack upstream proofs".

## Limits and what was not run

- No model or solver re-runs were done. Effects are shown only on authored controls.
- Only the unmodified-starter control was scored natively. The stable/fragile classification comes from the in-image probe, not from scoring honest proofs.
- Submissions were built from the judge baseline sources. We did not check that the work-image starter is identical to them.
- A solver that edits def or instance bodies (signatures unchanged) could still renumber transitive auxiliaries. That was not measured.
- The truth of individual targets was not audited.
- Whether the work image exposes upstream proofs or the blueprint was not checked.

## Reproduce

- Census: `evidence/scripts/lean_family_census/pipeline.sh <task_id> <image@digest> <project dir> <root module>`.
- Exact `eval_cmd` control: `evidence/scripts/lean_family_census/run_native.sh`. Its usage line is in the script header.
- Proof-style check: `evidence/scripts/lean_family_census/auxstyle/run.sh`. The output is in `auxstyle/carleson_v4.30.out`.
- Outputs: `evidence/scripts/lean_family_census/out/carleson_formalization/`.
- Supporting records: `evidence/reviews/lean_family_aux_census.md`.

