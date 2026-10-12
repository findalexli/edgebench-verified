# Combinatorial Games Formalization (`combinatorial_games_formalization`)

**Decision:** Retain with note. Honest proofs in two styles earn identical credit on a native test, and the in-image census found no target out of reach for an honest, complete solution.

## What the task asks for

The prompt asks the solver to "finish **all** sorries in this folder", says "we value minor progress", and warns: "do not modify the signature of existing lemma/theorem/def as these changes will not pass the judge evaluation." The score is the share of baseline `sorry`-dependent declarations that the submission turns into axiom-clean declarations with unchanged printed types. It is unweighted. Category: Formal Math & Theorem Proving.

## What goes wrong

No material defect. What was checked:

- **Auxiliary targets.** The shared Lean grader credits compiler-generated auxiliary targets (`X._proof_N`, `X._simp_N`, …) only when the exact generated name and printed type match. In `lean_analysis_proofs` this makes at least 49/2901 (1.69%) of targets unreachable for any honest complete solution, and scores depend on proof style. That does not happen here:

| targets | aux targets | aux share of score | fragile aux | `sorry` in type | P/¬P pairs | lower bound on unattainable |
|---|---|---|---|---|---|---|
| 3732 | 937 | 25.1% | **0** | 0 | 0 | **0** |

  - Auxiliary kinds: 450 `_simp`, 432 `_proof`, 25 `_unsafe_rec`, 13 `eq_def`, 8 `eq_N`, and others.
  - A lexical count finds duplicate types for 33 auxiliaries (the classifier lists them as "likely unattainable"). The probe classes every one as transitive-only: it carries no hole of its own, so an honest proof never re-elaborates it. This was not tested by scoring beyond the one-module test below.
- **Why.** This starter was made by replacing *theorem* bodies with `sorry`. Auxiliary targets are BAD only because their upstream proof terms call a sorried theorem. They are earned automatically once those theorems are proved.

Note: auxiliaries are 25.1% of the score. They are earned automatically once their dependencies are proved, so this is a weighting skew, not unfairness.

The note says: "Shared Lean grader: native census shows honest term- and tactic-style proofs earn identical credit (16/3732); 0 targets unattainable; aux targets 25.1% of weight but stable".

## Impact

No target is out of reach for an honest, complete solution (lower bound on unattainable targets: 0). Proof style did not change credit in the native test.

## Fix (v2)

No change; the note above ships with the task.

## How we know

- **Original evaluator in the pinned judge image** (`sha256:3e1062c6…`, toolchain v4.28.0), one container at a time with `--network none --memory 4g --cpus 2`. The task's `judge.eval_cmd` ran verbatim, including the `.lake`/manifest swap and the full `lake build`. Six sorried theorems in `SignExpansion/Basic.lean` were proved honestly, with no signature change: `isUpperSet_preimage_singleton_zero`, `copy_eq`, `coe_mk`, `sign_eq_coe`, `le_iff_toLex`, `lt_iff_toLex`. Two styles were used: term mode (A) and tactic mode (B).

| Submission | Original judge result |
|---|---|
| unmodified starter (control) | 0/3732, no `type_changed`, no `disappeared` |
| style A (term mode) | 16/3732 |
| style B (tactic mode) | 16/3732, identical repaired set |

  - The 16 targets are the 6 theorems, `copy`, `instBoundedOrder`, and 7 auxiliaries (`copy._proof_1`, `instBoundedOrder._proof_1/_2`, `instCompleteLinearOrder._proof_1…5`). Nothing was type-changed or disappeared.
  - The control score of 0 also holds after `eval_cmd` swaps in the shared baseline `.lake` and rebuilds the whole project. That `.lake` holds a Mathlib that differs from the judge repo's.
- **Census inside the image.** We recorded the effective grader files, built the baseline `ListDeclAxiom` listing (it prints no HASH lines), and classified every target with the same target rule and auxiliary-name regex as the lean_analysis study. An in-image probe checked whether each auxiliary target holds a `sorry` of its own ("fragile") or reaches `sorry` only through other constants.
- **Axioms.** Credit requires axiom-clean declarations, checked through `ListDeclAxiom`.

## Limits

- No model or solver runs. Effects are shown only on authored controls and honest variants.
- The native honest test covers one leaf module only.
- Submissions were built from the judge baseline sources. Whether the work-image starter is identical to them was not checked.
- A solver that edits def or instance bodies (signatures unchanged) could still renumber transitive auxiliaries. That was not measured.
- Whether every sorried item has an upstream proof is unknown, because the upstream library is still under development. The truth of individual targets was not audited.
- Whether the work image exposes upstream proofs was not checked.
- Scorer isolation is outside this release's scope (EdgeBench design choice).

## Reproduce

- Census: `evidence/scripts/lean_family_census/pipeline.sh <task_id> <image@digest> <project dir> <root module>`.
- Exact `eval_cmd` with honest variants: `evidence/scripts/lean_family_census/run_native.sh <task_id> <image@digest> evidence/scripts/lean_family_census/cg_native SignExpansion/Basic.lean`.
- Outputs: `evidence/scripts/lean_family_census/out/combinatorial_games_formalization/`. The repaired set is in `native/repaired.txt`.
- Supporting records: `evidence/reviews/lean_family_aux_census.md`.
