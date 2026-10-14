# Sphere Eversion Formalization (`sphere_eversion_formalization`)

**Outcome:** Kept, with a note. <mark>We found no scored item that the grader's naming of compiler-generated items puts out of reach, and those items are stable; this rests on test submissions and inspection only, we scored no real proof, and we did not check whether every item is true.</mark>

## What the task asks

The task is a Lean project on sphere eversion, the result that a sphere can be turned inside out smoothly. Lean is a language for machine-checked mathematical proofs, and `sorry` is Lean's placeholder for a missing proof. The task text asks the solver to "finish **all** sorries in this folder" and says "we value minor progress". It also warns "do not modify the signature of existing lemma/theorem/def as these changes will not pass the judge evaluation."

The score is the share of the starting project's declarations that depend on `sorry` and that the submission turns into declarations free of unapproved axioms, with unchanged printed types. Every scored item (target) has the same weight. Category: Formal Math & Theorem Proving.

## What we checked

We found no defect that changes scores.

Lean's compiler generates helper declarations automatically (`X._proof_N`, `X._simp_N`, …). The Lean grader shared by several tasks credits these auxiliary targets only when the exact generated name and printed type match. In the task `lean_analysis_proofs`, this makes at least 44 helper targets (49 of 2901 targets in total, 1.69%, counting also 3 placeholder and 2 false statements) unreachable for any complete, correct solution, and makes scores depend on proof style. This task does not have that problem.

| Targets | Auxiliary targets | Auxiliary share of score | Fragile auxiliary targets | Targets with `sorry` in the type | Pairs of P and ¬P | Lower bound on unreachable targets |
|---|---|---|---|---|---|---|
| 661 | 119 | 18.0% | **0** | 0 | 0 | **0** |

- The auxiliary targets are 94 `_proof`, 23 `_simp`, and others.
- No auxiliary target holds a placeholder of its own ("fragile"). Each one is marked BAD only because it depends on a parent declaration that uses `sorry`. Correct proofs of those parent declarations should therefore leave it unchanged. We infer this from a probe inside the grader image and scored no real proof.
- Auxiliary targets are 18.0% of the score. By the probe, a solver should earn them automatically once it proves the declarations they depend on. We did not test this by scoring.
- Scorer isolation is outside this release's scope (an EdgeBench design choice). We found no scoring defect that affects solvers who follow the rules.

The task ships with this note: "Census: 0 targets unattainable; aux targets 18.0% and stable (controls only, no correct-proof test)".

## How much it matters

We observed no effect. The lower bound on targets unreachable because of compiler-generated names is 0 of 661. This does not show that every target is true or provable.

The task does not change; the note above ships with it.

## How we checked it

- We ran the original grader in the original public image, pinned by digest (toolchain v4.28.0), one container at a time with `--network none`. The task's `judge.eval_cmd` ran exactly as written on the grader's unmodified starting sources, as a test submission. It copies `/home/workspace/baseline/.lake` and `/home/workspace/baseline/lake-manifest.json` into the submission and rebuilds the whole project. The two manifests differ. In the grader image, `baseline/lake-manifest.json` has sha256 `af7adc71…` and the grader repository's `sphere-eversion/lake-manifest.json` has `c2b475de…` (`out/sphere_eversion_formalization/census.log`). We did not record the Mathlib revisions inside them. The starting project scored 0/661 under this swap, with no `type_changed` and no `disappeared`. The full grading run, build included, took about 5.8 minutes with every proof a `sorry` (`native.log`, 07:07:18 to 07:13:06) against the 2,400 s limit.
- For the count inside the image, we built the starting `ListDeclAxiom` listing and classified every target with the same target rule and auxiliary-name pattern we used for `lean_analysis_proofs`. A probe inside the image checked whether each auxiliary target holds a `sorry` of its own. The `ListDeclAxiom.lean` actually in use prints a HASH line for `Gromov`, which was true on the starting project.
- No separate formal model applies; the count is itself a Lean run.

## Limits

- We ran no AI model or solver. The effects shown come only from test submissions that we wrote.
- The only project we scored by running the grader is the unmodified starting project; we scored no real proof. The stable/fragile classification comes from the probe inside the image, not from scoring runs.
- We built test submissions from the grader's starting sources and did not check whether the starting project in the agent's work image is identical to them.
- We did not check whether the work image builds against the same Mathlib as `/home/workspace/baseline`. If it does not, a proof that compiles in the work image can fail to build at grading, and a failed build scores 0. We built only the starter, whose proofs are all `sorry`, under the swap. Recorded agent runs on this task score up to 58.5 out of 100 (`tasks/README.md`), so their proofs did build under the swap.
- We did not measure build time with complete proofs; the starter's full rebuild already takes about 5.8 minutes, and a run over the 2,400 s limit scores 0.
- A solver that edits the bodies of definitions or instances (with signatures unchanged) could still renumber transitive auxiliary declarations. We did not measure that.
- We did not audit whether each individual target is true.
- We did not check whether the work image exposes proofs from the source project.

## Reproduce

- Grader image digest: `sha256:1f6eae1d…486`.
- Census: `evidence/scripts/lean_family_census/pipeline.sh <task_id> <image@digest> <project dir> <root module>`.
- Run of the exact `eval_cmd` on a test submission: `evidence/scripts/lean_family_census/run_native.sh`. Its usage line is in the script header.
- The outputs are in `evidence/scripts/lean_family_census/out/sphere_eversion_formalization/`.
- Pinned identity: task JSON sha256 `089f1248…17c4`; `eval_lean.py` sha256 `3319767e…`; effective `ListDeclAxiom.lean` `4b74bf12…`.
- Supporting records: `evidence/reviews/lean_family_aux_census.md`.
