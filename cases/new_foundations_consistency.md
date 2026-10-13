# New Foundations Consistency (`new_foundations_consistency`)

**Outcome:** Kept, with a note. <mark>With network access, the original grader builds the project and returns a valid result for the unmodified starting project, but it cannot grade offline, and 15 compiler-generated scored items have an untested exposure of at most 0.67%.</mark>

## What the task asks

The task is a Lean project on the consistency of New Foundations, a set theory. Lean is a language for machine-checked mathematical proofs, and `sorry` is Lean's placeholder for a missing proof. The task text asks the solver to "finish **all** sorries in this folder" of the project, and says "we value minor progress". It warns: "do not modify the signature of existing lemma/theorem/def as these changes will not pass the judge evaluation", and "we check the axioms transitively, finishing a theorem without completeing precedent lemma will not count."

The score is the share of the starting project's declarations that depend on `sorry` and that the submission turns into declarations free of unapproved axioms, with unchanged printed types. Every scored item (target) has the same weight. The task card says `internet: false`. In the harness (`sforge/harness/run_evaluation.py`) this applies only to the agent's container; the grader's container is created without network restrictions. Category: Formal Math & Theorem Proving.

## What we checked

**With network access, the grader builds and returns a valid result for the unmodified starting project.** No honest proof was scored this way.

- Lake, Lean's build tool, printed `doc-gen4: URL has changed; deleting … and cloning again`, then `checking out revision '86d735ecf420e0dbaaf84e2fc2221969f9fca097'`. This is the commit pinned in the project's manifest, not a moving `main` branch, and its `lean-toolchain` is `v4.21.0-rc3`.
- The build succeeded: `eval_cmd` rc=0, no errors.
- The unmodified starting project got `valid: true` and `score: 0.0`, with `mode=unweighted, repaired=0/2246, remaining_bad=2246, new_bad=301`, 0 `type_changed`, 0 `disappeared`, and no HASH checks.
- The 301 `new_bad` entries are constants internal to the compiler (`_cstage2` 239, `_spec_N` 38, `_elambda_N` 24). They are not `sorry` targets and carry weight 0. They are also present in the starting project (2547 BAD lines against 2246 targets).

**Grading offline is impossible.** In the shipped grader image, `lake build` fails under `--network none`. It fails both in the grader's starting repository and in a submission prepared by the exact `eval_cmd`.

- Cause: Lake prints `doc-gen4: URL has changed; deleting '…/.lake/packages/doc-gen4' and cloning again` (`build_orig.err`). The bundled checkout was also recorded as having no `origin` remote and HEAD `0ee5b43…` rather than the manifest's `86d735ec…`; that state has no saved raw log (`lean_family_aux_census.md` and a comment in `nf_direct.sh` only).
- Offline, Lake deletes the checkout and tries to clone it again. That fails in `git` (exit code 128). `eval_cmd` returns 1 and writes no JSON.
- Expected: a valid result offline. Observed: no result.

**Compiler-generated targets: none unreachable, a small untested exposure.** Lean's compiler generates helper declarations automatically (`X._proof_N`, `X._simp_N`, …). In the task `lean_analysis_proofs`, the same grader credits these helper targets only when the exact generated name and printed type match, which makes some targets unreachable there. Here, a count of every target found none that is provably out of reach for an honest, complete solution (lower bound 0).

| Targets | Helper targets | Helper share of score | Fragile helper targets | Targets with `sorry` in the type | Pairs of P and ¬P | Lower bound on unreachable targets |
|---|---|---|---|---|---|---|
| 2246 | 370 | 16.5% | **15 (0.67%)** | 0 | 0 | **0** (up to 0.67% exposed) |

- Kinds of helper targets: 337 `_proof`, 15 `_sizeOf`, 10 `match`, and others.
- The 15 fragile helpers are `BasePerm.instMulActionNearLitter._proof_1/2`, `instGroupNewPerm._proof_1…10`, `instInvNewPerm._proof_1` and `instMulActionNewPermCode._proof_1/2`. They are fields of instances that contain the placeholders directly, plus their sibling fields filled by default. An honest proof could renumber them.
- The 96 `_proof_N` helpers whose parent is a theorem are expected to be stable. In a check in core Lean with this image's compiler (4.21.0-rc3), four `@[simp]` iff theorems that differ only by a constant were proved four ways: by `sorry`, by a term, by `omega` and by `simp`. In every style the helper is named `_proof_1` and its type is the theorem's own statement written as an equality (`auxstyle/nf_v4.21.out`). The `omega` proof also adds `_proof_1_1` and `_proof_1_2`, which are not targets. None of the 96 was scored by running the grader.

The note that ships with the task: "Builds and returns a valid result with the judge's network, shown on the unmodified starter only (Lake re-clones doc-gen4 at the manifest-pinned commit 86d735ec); cannot be graded offline; 15 of 370 aux targets exposed to renumbering (≤0.67%), untested".

## How much it matters

- Offline grading: affects only graders without network access, which then give no score at all. Under EdgeBench's harness, which gives the grader network access, this is not a defect in production. Grading still needs GitHub to be reachable and to keep serving commit `86d735ec`.
- Renumbered helpers: at most 0.67% of the score, and only for solvers who fill the affected instance fields. This is an upper bound on exposure, not a measured loss.

No change is made; the note above ships with the task.

## How we checked it

- **Original grader in the original public image, pinned by digest** (toolchain v4.21.0-rc3). The task's `judge.eval_cmd` ran exactly as written on the unmodified starting sources of the grader. One container ran at a time, with `--memory 4g --cpus 2`. It ran once with `--network none` and once on the default bridge network with `timeout 3600`.
- **Count of targets.** Lake cannot build offline in this image. The target listing was therefore produced with the same `ListDeclAxiom` helper from the image, run through plain `lean`, with a `LEAN_PATH` built from the compiled files (oleans) already in the image. The grader's target rule was then applied with the same classifier used for the other Lean tasks.
- **Check that proof style does not change names.** The check in core Lean described above, run with the image's compiler.

## Limits

- No AI model or solver runs were made. Effects are shown only on the unmodified starting project.
- No honest proof was scored, so the 15 exposed targets remain untested.
- The target listing was produced with plain `lean` instead of `lake build ListDeclAxiom`, using the same helper file and the same oleans.
- The result with network access depends on GitHub at run time. It was observed once.
- Test submissions were built from the grader's starting sources. It was not checked that the starting project in the agent's work image is identical to them.
- Whether each individual target is true was not checked.
- Whether the work image exposes proofs from the source project, including the `Old/` directory mentioned in the README, was not checked.

## Reproduce

- Grader image digest: `sha256:c17cd565…cc4`.
- `eval_cmd` with network access: `evidence/scripts/lean_family_census/nf_networked.sh`. Outputs are in `evidence/scripts/lean_family_census/out/new_foundations_consistency/networked/`, including `report.json`.
- `eval_cmd` offline: `evidence/scripts/lean_family_census/run_native.sh`. The failure log is `out/new_foundations_consistency/native/build_orig.err`.
- Count of targets: `evidence/scripts/lean_family_census/nf_direct.sh`.
- Proof-style check: `evidence/scripts/lean_family_census/auxstyle/run.sh`. The output is in `auxstyle/nf_v4.21.out`.
- Supporting records: `evidence/reviews/lean_family_aux_census.md`, sections "Separate finding" and "Networked judge run".
