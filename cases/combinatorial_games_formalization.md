# Combinatorial Games Formalization (`combinatorial_games_formalization`)

**Outcome:** Kept, with a note. Honest proofs in two styles earn the same credit in a test on the original grader, and a full count inside the grader image finds no graded item out of reach for an honest, complete solution.

## What the task asks

The task is written in Lean, a language for machine-checked mathematical proofs. In Lean, `sorry` is a placeholder for a missing proof. The prompt asks the solver to "finish **all** sorries in this folder", says "we value minor progress", and warns: "do not modify the signature of existing lemma/theorem/def as these changes will not pass the judge evaluation."

The grader starts from the list of declarations that depend on `sorry` in the starter project. The score is the share of these that the submission turns into declarations that use only the allowed axioms ("axiom-clean") and keep the same printed type. Every declaration counts equally. Category: Formal Math & Theorem Proving.

## What we checked

There is no problem that changes scores enough to matter. The checks:

- **Helper items.** When Lean compiles a definition, it can create helper declarations of its own (`X._proof_N`, `X._simp_N`, …). The grader shared by EdgeBench's Lean tasks credits these helper items only when the exact generated name and printed type match. In the task `lean_analysis_proofs`, this makes at least 49/2901 (1.69%) of graded items out of reach for any honest complete solution, and scores depend on proof style. That does not happen here:

| Graded items | Helper items | Helper share of score | Fragile helper items | `sorry` in type | Statement/negation (P/¬P) pairs | Lower bound on items out of reach |
|---|---|---|---|---|---|---|
| 3732 | 937 | 25.1% | **0** | 0 | 0 | **0** |

  - Kinds of helper item: 450 `_simp`, 432 `_proof`, 25 `_unsafe_rec`, 13 `eq_def`, 8 `eq_N`, and others.
  - A text-based count finds duplicate types for 33 helper items, and the classifier lists them as "likely unattainable". The in-image probe classes every one as transitive-only: it has no `sorry` of its own, so an honest proof never rebuilds it. Beyond the one-module test below, this was not tested by scoring.
- **Why.** This starter was made by replacing *theorem* bodies with `sorry`. Helper items fail only because their proof terms, taken from the upstream library, call a theorem that now holds `sorry`. They are earned automatically once those theorems are proved.

Note: helper items are 25.1% of the score. They are earned automatically once the items they depend on are proved, so this skews the weighting but is not unfair.

The note says: "Shared Lean grader: native census shows honest term- and tactic-style proofs earn identical credit (16/3732); 0 targets unattainable; aux targets 25.1% of weight but stable".

## How much it matters

No graded item is out of reach for an honest, complete solution (lower bound on items out of reach: 0). Proof style did not change credit in the test on the original grader.

There is no code change. The note above ships with the task.

## How we checked it

- **Original grader in the pinned grader image** (`sha256:3e1062c6…`, Lean toolchain v4.28.0). One container ran at a time, with `--network none --memory 4g --cpus 2`. The task's `judge.eval_cmd` ran word for word, including the `.lake`/manifest swap and the full `lake build`. Six theorems with `sorry` in `SignExpansion/Basic.lean` were proved honestly, with no signature change: `isUpperSet_preimage_singleton_zero`, `copy_eq`, `coe_mk`, `sign_eq_coe`, `le_iff_toLex`, `lt_iff_toLex`. Two proof styles were used: term mode (A), which writes the proof as an expression, and tactic mode (B), which writes it as a sequence of proof steps.

| Test submission | Original grader result |
|---|---|
| unmodified starter (correct baseline) | 0/3732, no `type_changed`, no `disappeared` |
| style A (term mode) | 16/3732 |
| style B (tactic mode) | 16/3732, same set of items credited |

  - The 16 items are the 6 theorems, `copy`, `instBoundedOrder`, and 7 helper items (`copy._proof_1`, `instBoundedOrder._proof_1/_2`, `instCompleteLinearOrder._proof_1…5`). No item changed type or disappeared.
  - The starter's score of 0 also holds after `eval_cmd` swaps in the shared baseline `.lake` and rebuilds the whole project. That `.lake` holds a Mathlib (Lean's main mathematics library) that differs from the one in the grader's repository.
- **Count inside the image.** We recorded the grader files actually in use and built the baseline `ListDeclAxiom` listing (it prints no HASH lines). We then classified every graded item with the same rule for graded items and the same helper-name pattern as the `lean_analysis_proofs` study. A probe inside the image checked whether each helper item holds a `sorry` of its own ("fragile") or reaches `sorry` only through other constants.
- **Axioms.** Credit requires axiom-clean declarations, checked through `ListDeclAxiom`.

## Limits

- No AI model or solver was run. Effects are shown only on test submissions we wrote and on honest proof variants.
- The honest test on the original grader covers one leaf module only.
- Test submissions were built from the grader's baseline sources. Whether the starter in the work image is identical to them was not checked.
- A solver that edits the bodies of definitions or instances (signatures unchanged) could still renumber transitive helper items. That was not measured.
- Whether every item with `sorry` has an upstream proof is unknown, because the upstream library is still under development. Whether each individual statement is true was not audited.
- Whether the work image exposes upstream proofs was not checked.
- Whether the scorer is isolated from the submission is outside this release's scope (an EdgeBench design choice).

## Reproduce

- Count: `evidence/scripts/lean_family_census/pipeline.sh <task_id> <image@digest> <project dir> <root module>`.
- Exact `eval_cmd` with honest variants: `evidence/scripts/lean_family_census/run_native.sh <task_id> <image@digest> evidence/scripts/lean_family_census/cg_native SignExpansion/Basic.lean`.
- Outputs: `evidence/scripts/lean_family_census/out/combinatorial_games_formalization/`. The set of credited items is in `native/repaired.txt`.
- Supporting records: `evidence/reviews/lean_family_aux_census.md`.
