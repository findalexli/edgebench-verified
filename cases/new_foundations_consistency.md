# New Foundations Consistency (`new_foundations_consistency`)

**Decision:** Retain with note. With the judge's network access, the original evaluator builds and returns a valid result for the unmodified starter, but it cannot grade offline, and 15 compiler-generated targets have an untested exposure of at most 0.67%.

## What the task asks for

The prompt asks the solver to "finish **all** sorries in this folder" of a Lean project, and says "we value minor progress". It warns: "do not modify the signature of existing lemma/theorem/def as these changes will not pass the judge evaluation", and "we check the axioms transitively, finishing a theorem without completeing precedent lemma will not count." The score is the unweighted share of baseline `sorry`-dependent declarations that the submission turns into axiom-clean declarations with unchanged printed types. The task card says `internet: false`; in the harness (`sforge/harness/run_evaluation.py`) this applies only to the agent container; the judge container is created without network restrictions. Category: Formal Math & Theorem Proving.

## What goes wrong

**Grading with the judge's network works.**

- Lake printed `doc-gen4: URL has changed; deleting … and cloning again`, then `checking out revision '86d735ecf420e0dbaaf84e2fc2221969f9fca097'`. This is the manifest-pinned commit, not a moving `main`, and its `lean-toolchain` is `v4.21.0-rc3`.
- The build succeeded: `eval_cmd` rc=0, no errors.
- The unmodified starter got `valid: true` and `score: 0.0`, with `mode=unweighted, repaired=0/2246, remaining_bad=2246, new_bad=301`, 0 `type_changed`, 0 `disappeared`, and no HASH checks.
- The 301 `new_bad` entries are compiler-internal constants (`_cstage2` 239, `_spec_N` 38, `_elambda_N` 24). They are not sorry targets and carry weight 0. They are also present in the baseline (2547 BAD lines against 2246 targets).

**Offline grading is impossible.** In the shipped judge image, `lake build` fails under `--network none`, both in the judge baseline repo and in a submission prepared by the verbatim `eval_cmd`.

- Cause: the bundled `.lake/packages/doc-gen4` checkout has no `origin` remote, and its HEAD, `0ee5b43…`, does not match the manifest's `86d735ec…`.
- Offline, Lake deletes the checkout and tries to clone it again, which fails on `git` (exit code 128). `eval_cmd` returns 1 and writes no JSON.
- Expected: a valid result offline. Observed: no result.

**Compiler-generated targets: no unattainable targets, small untested exposure.** The same grader in `lean_analysis_proofs` credits compiler-generated helper targets (`X._proof_N`, `X._simp_N`, …) only when the exact generated name and printed type match, which makes some targets unattainable there. Here, the census found no target that is provably out of reach for an honest, complete solution (lower bound 0).

| targets | aux targets | aux share of score | fragile aux | `sorry` in type | P/¬P pairs | lower bound on unattainable |
|---|---|---|---|---|---|---|
| 2246 | 370 | 16.5% | **15 (0.67%)** | 0 | 0 | **0** (up to 0.67% exposed) |

- Helper kinds: 337 `_proof`, 15 `_sizeOf`, 10 `match`, and others.
- The 15 fragile helpers are `BasePerm.instMulActionNearLitter._proof_1/2`, `instGroupNewPerm._proof_1…10`, `instInvNewPerm._proof_1` and `instMulActionNewPermCode._proof_1/2`. They are instance fields that contain holes directly, plus their default-field siblings. An honest fill could renumber them.
- The 96 theorem-parent `_proof_N` helpers are expected to be stable. In a core-Lean check with this image's compiler (4.21.0-rc3), an `@[simp]` iff theorem proved by `sorry`, by a term, by `omega` and by `simp` got its helper under the same name (`_proof_1`) and the same type every time. None of the 96 was scored natively.

The note that ships with the task: "Grades correctly with the judge's network (Lake re-clones doc-gen4 at the manifest-pinned commit 86d735ec, valid result); cannot be graded offline; 15 of 370 aux targets exposed to renumbering (≤0.67%), untested".

## Impact

- Offline grading: affects only network-isolated judges, which get no score at all. Under the maintained harness it is not a production defect. Grading still needs GitHub to be reachable and to keep serving commit `86d735ec`.
- Helper renumbering: at most 0.67% of the score, only for solvers who fill the affected instance fields. This is an upper bound on exposure, not a measured loss.

## Fix (v2)

No change; the note above ships with the task.

## How we know

- **Original evaluator in the pinned image.** The task's `judge.eval_cmd` ran verbatim on the unmodified judge baseline sources in the judge image (`sha256:c17cd565…cc4`, toolchain v4.21.0-rc3), one container at a time with `--memory 4g --cpus 2`: once with `--network none` and once on the default bridge network with `timeout 3600`.
- **Census.** Because Lake cannot build offline in this image, the target listing was produced with the same in-image `ListDeclAxiom` helper run through plain `lean`, using a `LEAN_PATH` built from the oleans the image already contains. The grader's target rule was then applied with the same classifier used for the other Lean tasks.
- **Proof-style check.** The core-Lean check described above, run with the image's compiler.

## Limits

- No model or solver runs. Effects are shown only on the unmodified-starter control.
- No honest-proof variant was scored, so the 15 exposed targets remain untested.
- The census listing was produced with plain `lean` instead of `lake build ListDeclAxiom`, using the same helper file and the same oleans.
- The networked result depends on GitHub at run time. It was observed once.
- Submissions were built from the judge baseline sources. It was not checked that the work-image starter is identical to them.
- The truth of individual targets was not checked.
- Whether the work image exposes upstream proofs, including the `Old/` directory mentioned in the README, was not checked.

## Reproduce

- Networked `eval_cmd`: `evidence/scripts/lean_family_census/nf_networked.sh`. Outputs are in `evidence/scripts/lean_family_census/out/new_foundations_consistency/networked/`, including `report.json`.
- Offline `eval_cmd`: `evidence/scripts/lean_family_census/run_native.sh`. The failure log is `out/new_foundations_consistency/native/build_orig.err`.
- Census: `evidence/scripts/lean_family_census/nf_direct.sh`.
- Proof-style check: `evidence/scripts/lean_family_census/auxstyle/run.sh`. The output is in `auxstyle/nf_v4.21.out`.
- Supporting records: `evidence/reviews/lean_family_aux_census.md`, sections "Separate finding" and "Networked judge run".
