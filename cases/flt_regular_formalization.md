# FLT Regular Formalization (`flt_regular_formalization`)

**Decision:** Retain with note. The weighted target list matches the baseline listing exactly, contains no auxiliary names, and the census lower bound on targets out of reach for an honest, complete solution is 0.

## What the task asks for

The prompt asks the solver to "finish **all** sorries in this folder" and says "we value minor progress". It warns: "Do not modify the signature of existing lemma/theorem/def as these changes will not pass the judge evaluation." It also says that "finishing `fermatLastTheoremSeven` without completeing `isRegularPrime_seven` and `flt_regular` will not count." Unlike the other Lean tasks, this one is scored in weighted mode: a weights file lists 25 declarations with total weight 87. Category: Formal Math & Theorem Proving.

## What goes wrong

No material defect. What was checked:

- **Auxiliary targets.** The shared Lean grader credits compiler-generated auxiliary targets (`X._proof_N`, `X._simp_N`, …) only when the exact generated name and printed type match. In `lean_analysis_proofs` this makes at least 49/2901 (1.69%) of targets unattainable for any honest complete solution. It does not apply here, because no target is an auxiliary:

| targets (weight) | aux targets | aux share of score | fragile aux | `sorry` in type | P/¬P pairs | lower bound on unattainable |
|---|---|---|---|---|---|---|
| 25 (weight 87) | **0** | 0% | 0 | 0 | 0 | **0** |

- **Weights file.** It has 25 entries, with weights from 1 to 6 and a total of 87. Those entries are exactly the 25 BAD+sorry declarations in the listing, and all 25 type texts equal the listing's.

Note: the README groups the score into 100 points, but the grader uses weights totalling 87. This is a documentation mismatch only.

The note says: "Census: 25 weighted targets (total weight 87) match the listing exactly; no aux targets; 0 unattainable".

## Impact

No target is out of reach for an honest, complete solution (lower bound 0). The README grouping does not change any score.

## Fix (v2)

No change; the note above ships with the task.

## How we know

- **Original evaluator in the pinned judge image** (`sha256:c8b50a05…`, toolchain v4.28.0), one container at a time with `--network none --memory 4g --cpus 2`. The task's `judge.eval_cmd` ran verbatim on the unmodified judge baseline sources. The command includes the swap to the shared baseline `.lake` and a full rebuild. The unmodified starter scored 0/25 (weight 0/87), with no `type_changed` and no `disappeared`. This holds even though the swapped-in `.lake` holds a Mathlib that differs from the judge repo's.
- **Census inside the image.** We recorded the effective grader files, built the baseline `ListDeclAxiom` listing (it prints a HASH line for `flt_regular`, which was true on the baseline), and compared the weights-file entries with the listing's BAD+`sorry` declarations and their printed types.
- **Axioms.** Credit requires axiom-clean declarations, checked through `ListDeclAxiom`.

## Limits

- No model or solver runs. Effects are shown only on authored controls.
- Only the unmodified-starter control was scored natively. No honest-proof variant was scored for this task.
- Submissions were built from the judge baseline sources. Whether the work-image starter is identical to them was not checked.
- The truth of individual targets was not audited.
- Whether the work image exposes upstream proofs was not checked. The upstream project is complete and public, and parts of it are in Mathlib.
- Scorer isolation is outside this release's scope (EdgeBench design choice).

## Reproduce

- Census: `evidence/scripts/lean_family_census/pipeline.sh <task_id> <image@digest> <project dir> <root module> FltRegular_weight.json`.
- Exact `eval_cmd` control: `evidence/scripts/lean_family_census/run_native.sh`. Its usage line is in the script header.
- Outputs: `evidence/scripts/lean_family_census/out/flt_regular_formalization/`. The weights-file entries and their weights are listed in `classify.txt`; the weights file itself is not included.
- Supporting records: `evidence/reviews/lean_family_aux_census.md`.
