# Carleson Formalization (`carleson_formalization`)

**Outcome:** Kept, with a note. A count of every scored item inside the grader image finds none that an honest, complete solution cannot reach; the note covers one placeholder data definition and the unfinished source project.

## What the task asks

The task is a large Lean project on Carleson's theorem about Fourier series. Lean is a language for machine-checked mathematical proofs, and `sorry` is Lean's placeholder for a missing proof. The task text asks the solver to "finish **all** sorries in this folder" and says "we value minor progress". It warns: "do not modify the signature of existing lemma/theorem/def as these changes will not pass the judge evaluation." It also says "we check the axioms transitively, finishing a theorem without completeing precedent lemma will not count."

The score is the share of the starting project's declarations that depend on `sorry` and that the submission turns into declarations free of unapproved axioms, with unchanged printed types. Every scored item (target) has the same weight. Category: Formal Math & Theorem Proving.

## What we checked

No defect that changes scores enough to matter was found. These parts were checked:

- **Auxiliary targets.** Lean's compiler generates helper declarations automatically (`X._proof_N`, `X._simp_N`, …). The Lean grader shared by several tasks credits these auxiliary targets only when the exact generated name and printed type match. In the task `lean_analysis_proofs`, this makes at least 49/2901 (1.69%) of targets unreachable for any honest, complete solution, and scores depend on proof style. In this task no auxiliary target is exposed to that problem:

| Targets | Auxiliary targets | Auxiliary share of score | Fragile auxiliary targets | Targets with `sorry` in the type | Pairs of P and ¬P | Lower bound on unreachable targets |
|---|---|---|---|---|---|---|
| 3004 | 151 | 5.0% | **0** | 0 | 0 | **0** |

  - Kinds of auxiliary targets: 90 `_proof`, 19 `_simp`, 11 `congr_simp`, 10 `eq_def`, and others.
  - A text-based count finds duplicate types for 8 auxiliary targets, and the classifier lists them as "likely unattainable". The probe inside the image classes all of them as transitive-only: they hold no `sorry` of their own and only inherit it. By the census's reasoning they are therefore not at risk. This was not tested by scoring.
- **Proof style.** With this image's compiler (4.30.0-rc2), an `@[simp]` iff theorem was proved four ways: by `sorry`, by a term, by `omega` and by `simp`. In every case its auxiliary declaration got the same name (`_simp_1`) and the same type.

Notes:

- **Placeholder data definition.** `ToMathlib/RealInterpolation/LorentzInterpolation.lean` contains a *data* definition, `C_LorentzInterpolation := sorry`, that is, a defined value rather than a proof. Any value earns that target's credit, and later bounds that use it may become easier. This looks like unfinished work in the source project. It comes from reading the source and was not tested by running the grader.
- **Completeness of the source project.** The source project is reported to have completed its main theorem (not checked here), but the project is unfinished. Some targets may have no proof in the source project.

The note says: "Census: 0 targets unattainable, aux targets 5.0% and stable; a sorried data definition (C_LorentzInterpolation) admits any value; upstream project unfinished, so some targets may lack upstream proofs".

## How much it matters

No target is out of reach for an honest, complete solution: the lower bound on unreachable targets is 0. The placeholder data definition affects one target, and possibly the difficulty of later bounds. Its effect on the score was not measured.

## How we checked it

- **Original grader in the original public image, pinned by digest** (toolchain v4.30.0-rc2). One container ran at a time, with `--network none --memory 4g --cpus 2`. The task's `judge.eval_cmd` ran exactly as written on the unmodified starting sources of the grader. The unmodified starting project scored 0/3004, with no `type_changed` and no `disappeared`.
- **Count inside the image.** We recorded the grader files actually in use and built the starting `ListDeclAxiom` listing. It prints a HASH line for `classical_carleson_check`, which was true on the starting project. We then classified every target with the same target rule and auxiliary-name pattern as the `lean_analysis_proofs` study. A probe inside the image checked whether each auxiliary target holds a `sorry` of its own ("fragile").
- **Formal check that proof style does not change names.** A check in core Lean with the image's compiler, described above.
- **Axioms.** Credit requires declarations free of unapproved axioms. The grader checks axioms transitively, through everything a declaration depends on, using `ListDeclAxiom`.

## Limits

- No AI model or solver runs were made. Effects are shown only on test submissions that we wrote.
- Only the unmodified starting project was scored by running the grader. No honest proof was scored for this task. The stable/fragile classification comes from the probe inside the image.
- Test submissions were built from the grader's starting sources. Whether the starting project in the agent's work image is identical to them was not checked.
- A solver that edits the bodies of definitions or instances (with signatures unchanged) could still renumber transitive auxiliary declarations. That was not measured.
- Whether each individual target is true was not audited.
- Whether the work image exposes proofs from the source project or its blueprint was not checked.
- Scorer isolation is outside this release's scope (EdgeBench design choice).

## Reproduce

- Grader image digest: `sha256:dd9aab33…`.
- Census: `evidence/scripts/lean_family_census/pipeline.sh <task_id> <image@digest> <project dir> <root module>`.
- Run of the exact `eval_cmd` on a test submission: `evidence/scripts/lean_family_census/run_native.sh`. Its usage line is in the script header.
- Proof-style check: `evidence/scripts/lean_family_census/auxstyle/run.sh`. The output is in `auxstyle/carleson_v4.30.out`.
- Outputs: `evidence/scripts/lean_family_census/out/carleson_formalization/`.
- Supporting records: `evidence/reviews/lean_family_aux_census.md`.
