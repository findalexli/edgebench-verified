# Carleson Formalization (`carleson_formalization`)

**Decision:** Retain with note. The in-image census found no target that an honest, complete solution cannot reach; the note covers a sorried data definition and the unfinished upstream project.

## What the task asks for

The prompt asks the solver to "finish **all** sorries in this folder" and says "we value minor progress". It warns: "do not modify the signature of existing lemma/theorem/def as these changes will not pass the judge evaluation." It also says "we check the axioms transitively, finishing a theorem without completeing precedent lemma will not count." The score is the share of baseline `sorry`-dependent declarations that the submission turns into axiom-clean declarations with unchanged printed types. It is unweighted. Category: Formal Math & Theorem Proving.

## What goes wrong

No material defect. What was checked:

- **Auxiliary targets.** The shared Lean grader credits compiler-generated auxiliary targets (`X._proof_N`, `X._simp_N`, …) only when the exact generated name and printed type match. In `lean_analysis_proofs` this makes at least 49/2901 (1.69%) of targets unattainable for any honest complete solution, and scores depend on proof style. For this task no auxiliary target is exposed:

| targets | aux targets | aux share of score | fragile aux | `sorry` in type | P/¬P pairs | lower bound on unattainable |
|---|---|---|---|---|---|---|
| 3004 | 151 | 5.0% | **0** | 0 | 0 | **0** |

  - Auxiliary kinds: 90 `_proof`, 19 `_simp`, 11 `congr_simp`, 10 `eq_def`, and others.
  - A lexical count finds duplicate types for 8 auxiliaries (the classifier lists them as "likely unattainable"). The probe classes all of them as transitive-only, so by the census's reasoning they are not at risk. This was not tested by scoring.
- **Proof style.** With this image's compiler (4.30.0-rc2), an `@[simp]` iff theorem proved by `sorry`, by a term, by `omega` and by `simp` got its auxiliary under the same name (`_simp_1`) and the same type in every case.

Notes:

- **Sorried data definition.** `ToMathlib/RealInterpolation/LorentzInterpolation.lean` contains a *data* definition, `C_LorentzInterpolation := sorry`. Any value earns that target's credit, and downstream bounds may become easier. This looks like unfinished upstream work. It comes from source reading and was not tested natively.
- **Upstream completeness.** The upstream project is reported to have completed its main theorem (not checked here), but the project is unfinished. Some targets may have no upstream proof.

The note says: "Census: 0 targets unattainable, aux targets 5.0% and stable; a sorried data definition (C_LorentzInterpolation) admits any value; upstream project unfinished, so some targets may lack upstream proofs".

## Impact

No target is out of reach for an honest, complete solution (lower bound on unattainable targets: 0). The sorried data definition affects one target and possibly the difficulty of downstream bounds; its score effect was not measured.

## Fix (v2)

No change; the note above ships with the task.

## How we know

- **Original evaluator in the pinned judge image** (`sha256:dd9aab33…`, toolchain v4.30.0-rc2), one container at a time with `--network none --memory 4g --cpus 2`. The task's `judge.eval_cmd` ran verbatim on the unmodified judge baseline sources. The unmodified starter scored 0/3004, with no `type_changed` and no `disappeared`.
- **Census inside the image.** We recorded the effective grader files, built the baseline `ListDeclAxiom` listing (it prints a HASH line for `classical_carleson_check`, which was true on the baseline), and classified every target with the same target rule and auxiliary-name regex as the lean_analysis study. An in-image probe checked whether each auxiliary target holds a `sorry` of its own ("fragile").
- **Formal check of proof-style stability.** A core-Lean check with the image's compiler, described above.
- **Axioms.** Credit requires axiom-clean declarations; the grader checks axioms transitively through `ListDeclAxiom`.

## Limits

- No model or solver runs. Effects are shown only on authored controls.
- Only the unmodified-starter control was scored natively. No honest proof was scored for this task. The stable/fragile classification comes from the in-image probe.
- Submissions were built from the judge baseline sources. Whether the work-image starter is identical to them was not checked.
- A solver that edits def or instance bodies (signatures unchanged) could still renumber transitive auxiliaries. That was not measured.
- The truth of individual targets was not audited.
- Whether the work image exposes upstream proofs or the blueprint was not checked.
- Scorer isolation is outside this release's scope (EdgeBench design choice).

## Reproduce

- Census: `evidence/scripts/lean_family_census/pipeline.sh <task_id> <image@digest> <project dir> <root module>`.
- Exact `eval_cmd` control: `evidence/scripts/lean_family_census/run_native.sh`. Its usage line is in the script header.
- Proof-style check: `evidence/scripts/lean_family_census/auxstyle/run.sh`. The output is in `auxstyle/carleson_v4.30.out`.
- Outputs: `evidence/scripts/lean_family_census/out/carleson_formalization/`.
- Supporting records: `evidence/reviews/lean_family_aux_census.md`.
