# FLT Regular Formalization (`flt_regular_formalization`)

Status: reviewed by the coordinator, 2026-10-12

- **Domain:** Formal Math & Theorem Proving
- **Decision:** Retain with note. The weighted target list matches the baseline listing exactly. It contains no auxiliary names, and no target is out of reach for an honest, complete solution.

## What the task promises

The prompt asks the solver to "finish **all** sorries in this folder" and says "we value minor progress". It warns: "Do not modify the signature of existing lemma/theorem/def as these changes will not pass the judge evaluation." It also says that "finishing `fermatLastTheoremSeven` without completeing `isRegularPrime_seven` and `flt_regular` will not count."

Unlike the other Lean tasks, this one is scored in weighted mode. A weights file lists 25 declarations with total weight 87.

## What we checked and how

- **Earlier hypothesis.** In `lean_analysis_proofs`, a native test found that the shared grader credits compiler-generated auxiliary targets (`X._proof_N`, `X._simp_N`, …) only when the exact generated name and printed type match. There, at least 49/2901 (1.69%) of targets are unattainable for any honest complete solution, and scores depend on proof style. The hypothesis was that this defect applies to the whole Lean family. We tested it natively for this task.
- **Native runs in the pinned judge image.** The image was pulled by digest and removed afterwards. One container ran at a time, with `--network none --memory 4g --cpus 2`. No Lean ran on the host.
- **Census inside the image.**
  - We recorded the effective grader files.
  - We built the baseline `ListDeclAxiom` listing.
  - We compared the weights-file entries with the listing's BAD+`sorry` declarations and their printed types.
- **Exact `eval_cmd`.** We ran the task's `judge.eval_cmd` verbatim on the unmodified judge baseline sources as a control. The command includes the swap to the shared baseline `.lake` and a full rebuild.
- **Original identity.**
  - Judge image: `…@sha256:c8b50a05…50fc`, toolchain v4.28.0.
  - Task JSON: sha256 `57950a57…a61`. Export tar: sha256 `c04d3085…8e1b`.
  - `eval_lean.py`: sha256 `3319767e…`.
  - Effective `ListDeclAxiom.lean`: `0eee3e92…`. It prints a HASH line for `flt_regular`, which was true on the baseline.
  - Weights file `task/FltRegular_weight.json`: sha256 `943b624f…15ce`.

## What we found

**Auxiliary-name defect: Refuted (not applicable) for this task.** The hypothesis that the lean_analysis defect applies here was tested natively and rejected.

Census numbers:

| targets (weight) | aux targets | aux share of score | fragile aux | `sorry` in type | P/¬P pairs | lower bound on unattainable |
|---|---|---|---|---|---|---|
| 25 (weight 87) | **0** | 0% | 0 | 0 | 0 | **0** |

- The weights file has 25 entries, with weights from 1 to 6 and a total of 87.
- Those entries are exactly the 25 BAD+sorry declarations in the listing, and all 25 type texts equal the listing's.
- None of them is an auxiliary name.

**Control.** The unmodified starter scored 0/25 (weight 0/87), with no `type_changed` and no `disappeared`. This holds even though `eval_cmd` swaps in the shared baseline `.lake`, whose Mathlib differs from the judge repo's, and rebuilds the whole project.

**README point grouping: Not material.** The README groups the score into 100 points. The grader uses weights totalling 87. This is a documentation mismatch only.

**Scorer isolation.** Scorer isolation is outside this release's scope (EdgeBench design choice); no good-faith scoring defect was found.

**Earlier withholding.** An earlier source-only review proposed withholding the original task because of grader-robustness concerns. Under this release's scope, those concerns are scorer isolation. The native census found no good-faith defect.

**Earlier setup records.** An earlier "setup failure" record was a failure of the audit's own infrastructure, not a task defect. It was a signal 11 during `lean --version`, in the audit's own selective-restoration route, not in the original image.

## Note for users

No repair. The note says: "Census: 25 weighted targets (total weight 87) match the listing exactly; no aux targets; 0 unattainable".

## Limits and what was not run

- No model or solver re-runs were done. Effects are shown only on authored controls.
- Only the unmodified-starter control was scored natively. No honest-proof variant was scored for this task.
  - The saved `native.log` shows no-op A/B rows, caused by a script default bug that is now fixed.
  - Those reports were deleted and are not evidence.
- Submissions were built from the judge baseline sources. We did not check that the work-image starter is identical to them.
- The truth of individual targets was not audited.
- Whether the work image exposes upstream proofs was not checked. The upstream project is complete and public, and parts of it are in Mathlib.

## Reproduce

- Census: `evidence/scripts/lean_family_census/pipeline.sh <task_id> <image@digest> <project dir> <root module> FltRegular_weight.json`.
- Exact `eval_cmd` control: `evidence/scripts/lean_family_census/run_native.sh`. Its usage line is in the script header.
- Outputs: `evidence/scripts/lean_family_census/out/flt_regular_formalization/`. The census copy of the weights file is included.
- Supporting records: `evidence/reviews/lean_family_aux_census.md`.

