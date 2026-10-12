# Sphere Eversion Formalization (`sphere_eversion_formalization`)

Status: reviewed by the coordinator, 2026-10-12

- **Domain:** Formal Math & Theorem Proving
- **Decision:** Retain with note. The native census found no target that an honest, complete solution cannot reach, and the auxiliary targets are stable. This rests on controls only; no honest-proof test was scored.

## What the task promises

The prompt asks the solver to "finish **all** sorries in this folder" and says "we value minor progress". It warns: "do not modify the signature of existing lemma/theorem/def as these changes will not pass the judge evaluation."

The score is the share of baseline `sorry`-dependent declarations that the submission turns into axiom-clean declarations with unchanged printed types. It is unweighted.

## What we checked and how

- **Earlier hypothesis.** In `lean_analysis_proofs`, a native test found that the shared grader credits compiler-generated auxiliary targets (`X._proof_N`, `X._simp_N`, …) only when the exact generated name and printed type match. There, at least 49/2901 (1.69%) of targets are unattainable for any honest complete solution, and scores depend on proof style. The hypothesis was that this defect applies to the whole Lean family. We tested it natively for this task.
- **Native runs in the pinned judge image.** The image was pulled by digest and removed afterwards. One container ran at a time, with `--network none --memory 4g --cpus 2`. No Lean ran on the host.
- **Census inside the image.**
  - We recorded the effective grader files.
  - We built the baseline `ListDeclAxiom` listing.
  - We classified every target with the same target rule and auxiliary-name regex as the lean_analysis study.
  - An in-image probe checked whether each auxiliary target holds a `sorry` of its own ("fragile").
- **Exact `eval_cmd`.** We ran the task's `judge.eval_cmd` verbatim on the unmodified judge baseline sources as a control. The command includes the swap to the shared baseline `.lake` and a full rebuild.
- **Original identity.**
  - Judge image: `…@sha256:1f6eae1d…486`, toolchain v4.28.0.
  - Task JSON: sha256 `089f1248…17c4`. Export tar: sha256 `d788f01b…ade8`.
  - `eval_lean.py`: sha256 `3319767e…`.
  - Effective `ListDeclAxiom.lean`: `4b74bf12…`. It prints a HASH line for `Gromov`, which was true on the baseline.

## What we found

**Auxiliary-name defect: Refuted for this task.** The hypothesis that the lean_analysis defect applies here was tested natively and rejected.

Census numbers:

| targets | aux targets | aux share of score | fragile aux | `sorry` in type | P/¬P pairs | lower bound on unattainable |
|---|---|---|---|---|---|---|
| 661 | 119 | 18.0% | **0** | 0 | 0 | **0** |

- **Auxiliary kinds:** 94 `_proof`, 23 `_simp`, and others.
- No auxiliary target carries its own hole. Each is BAD only because it depends on a sorried parent declaration, so honest proofs of those declarations should leave it unchanged. This is inferred from the in-image probe; no honest-proof variant was scored.

**Control.** The unmodified starter scored 0/661, with no `type_changed` and no `disappeared`. This holds even though `eval_cmd` swaps in the shared baseline `.lake`, whose Mathlib differs from the judge repo's, and rebuilds the whole project.

**Weighting skew: Not material.** Auxiliaries are 18.0% of the score. By the probe, they should be earned automatically once their dependencies are proved; this was not tested by scoring.

**Scorer isolation.** Scorer isolation is outside this release's scope (EdgeBench design choice); no good-faith scoring defect was found.

**Earlier withholding.** An earlier source-only review proposed withholding the original task because of grader-robustness concerns. Under this release's scope, those concerns are scorer isolation. The native census found no good-faith defect.

**Earlier setup records.** An earlier "setup failure" record was a failure of the audit's own infrastructure, not a task defect. It was a Python `ValueError` in the audit worker's cap-metadata guard, raised before any Lean ran.

## Note for users

No repair. The note says: "Census: 0 targets unattainable; aux targets 18.0% and stable (controls only, no honest-proof test)".

## Limits and what was not run

- No model or solver re-runs were done. Effects are shown only on authored controls.
- Only the unmodified-starter control was scored natively. No honest-proof variant was scored. The stable/fragile classification comes from the in-image probe, not from scoring runs.
- Submissions were built from the judge baseline sources. We did not check that the work-image starter is identical to them.
- A solver that edits def or instance bodies (signatures unchanged) could still renumber transitive auxiliaries. That was not measured.
- The truth of individual targets was not audited.
- Whether the work image exposes upstream proofs was not checked.

## Reproduce

- Census: `evidence/scripts/lean_family_census/pipeline.sh <task_id> <image@digest> <project dir> <root module>`.
- Exact `eval_cmd` control: `evidence/scripts/lean_family_census/run_native.sh`. Its usage line is in the script header.
- Outputs: `evidence/scripts/lean_family_census/out/sphere_eversion_formalization/`.
- Supporting records: `evidence/reviews/lean_family_aux_census.md`.

