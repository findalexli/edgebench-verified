# New Foundations Consistency (`new_foundations_consistency`)

Status: reviewed by the coordinator, 2026-10-12

- **Domain:** Formal Math & Theorem Proving
- **Decision:** Retain with note. With the judge's network access, the original evaluator grades correctly. It cannot grade offline, and 15 auxiliary targets have an untested exposure of at most 0.67%.

## What the task promises

The prompt asks the solver to "finish **all** sorries in this folder" and says "we value minor progress". It warns: "do not modify the signature of existing lemma/theorem/def as these changes will not pass the judge evaluation." It also says that "we check the axioms transitively, finishing a theorem without completeing precedent lemma will not count."

The score is the share of baseline `sorry`-dependent declarations that the submission turns into axiom-clean declarations with unchanged printed types. It is unweighted. The task card says `internet: false`. In the maintained harness this applies only to the agent container. The judge container has network access.

## What we checked and how

- **Earlier hypothesis.** In `lean_analysis_proofs`, a native test found that the shared grader credits compiler-generated auxiliary targets (`X._proof_N`, `X._simp_N`, …) only when the exact generated name and printed type match. There, at least 49/2901 (1.69%) of targets are unattainable for any honest complete solution, and scores depend on proof style. The hypothesis was that this defect applies to the whole Lean family. We tested it for this task in the pinned judge image.
- **Native runs in the pinned judge image.** The image was pulled by digest. One container ran at a time, with `--memory 4g --cpus 2`. No Lean ran on the host.
- **Offline run.** We ran the task's `judge.eval_cmd` verbatim on the unmodified judge baseline sources with `--network none`.
- **Networked run.** We ran the same verbatim `eval_cmd` on the same starter with network access.
  - It used the default bridge network, `timeout 3600`, and the heavy-job lock.
  - The image was removed afterwards.
- **Census with one setup correction.** Lake cannot build offline in this image, so the census listing was produced differently.
  - We ran the same in-image `ListDeclAxiom` helper with plain `lean`, using a `LEAN_PATH` built from the oleans the image already contains.
  - The grader's target rule was then applied offline with the same classifier used for the other Lean tasks.
- **Proof style and auxiliary names.** A core-Lean check with this image's compiler (4.21.0-rc3) tested an `@[simp]` iff theorem proved by `sorry`, by a term, by `omega` and by `simp`. In every case it got its auxiliary under the same name (`_proof_1`) and the same type.
- **Original identity.**
  - Judge image: `…@sha256:c17cd565…cc4`, toolchain v4.21.0-rc3.
  - Task JSON: sha256 `37ea0a38…5d`. Export tar: sha256 `076b5c9f…196`.
  - `eval_lean.py`: sha256 `3319767e…`.
  - Effective `ListDeclAxiom.lean`: `b585194f…`. It prints no HASH lines, and its project prefix test is `startsWith "ConNF"`.

## What we found

**Grading with the judge's network: works.**
- **What Lake did.** It printed `doc-gen4: URL has changed; deleting … and cloning again`, then `checking out revision '86d735ecf420e0dbaaf84e2fc2221969f9fca097'`.
  - This is the manifest-pinned commit, not a moving `main`.
  - That revision's `lean-toolchain` is `v4.21.0-rc3`.
- **Build.** The build succeeded: `eval_cmd` rc=0, no errors.
- **Unmodified starter.** The grader returned `valid: true` and `score: 0.0`, with `mode=unweighted, repaired=0/2246, remaining_bad=2246, new_bad=301`. There were 0 `type_changed`, 0 `disappeared`, and no HASH checks.
- **The 301 `new_bad` entries** are compiler-internal constants: `_cstage2` 239, `_spec_N` 38, `_elambda_N` 24.
  - They are BAD without being sorry targets, and they carry weight 0.
  - They are present in the baseline as well (2547 BAD lines against 2246 targets).

**Offline grading impossible: Confirmed, narrower.** In the shipped judge image, `lake build` fails under `--network none`. It fails both in the judge baseline repo and in a submission prepared by the verbatim `eval_cmd`.
- **Cause.** The bundled `.lake/packages/doc-gen4` checkout has no `origin` remote. Its HEAD, `0ee5b43…`, does not match the manifest's `86d735ec…`.
- **What happens offline.** Lake deletes the checkout and tries to clone it again, which fails on `git` (exit code 128). `eval_cmd` returns 1 and writes no JSON.
- **Why narrower.** This affects only network-isolated judges. It is not a production defect under the maintained harness.
- **Remaining dependency.** Grading needs GitHub to be reachable and to keep serving commit `86d735ec`.

**Auxiliary-name defect: no unattainable targets; small untested exposure.** The hypothesis that the lean_analysis defect applies here was not confirmed. The census found no target that an honest, complete solution cannot reach.

Census numbers:

| targets | aux targets | aux share of score | fragile aux | `sorry` in type | P/¬P pairs | lower bound on unattainable |
|---|---|---|---|---|---|---|
| 2246 | 370 | 16.5% | **15 (0.67%)** | 0 | 0 | **0** (up to 0.67% exposed) |

- **Auxiliary kinds:** 337 `_proof`, 15 `_sizeOf`, 10 `match`, and others.
- **The 15 fragile auxiliaries:**
  - `BasePerm.instMulActionNearLitter._proof_1/2`
  - `instGroupNewPerm._proof_1…10`
  - `instInvNewPerm._proof_1`
  - `instMulActionNewPermCode._proof_1/2`
- **What they are.** Instance fields that contain holes directly, plus their default-field siblings. An honest fill could renumber them, as happened in lean_analysis.
- **Not tested natively.** 0.67% is an upper bound on exposure, not a measured loss.
- **Stable auxiliaries.** The 96 theorem-parent `_proof_N` auxiliaries are stable.

**Scorer isolation.** Scorer isolation is outside this release's scope (EdgeBench design choice); no good-faith scoring defect was found beyond the notes above.

**Earlier withholding.** An earlier source-only review proposed withholding the original task because of grader-robustness concerns. Under this release's scope, those concerns are scorer isolation.

**Earlier setup records.** An earlier "setup failure" record was a failure of the audit's own infrastructure, not a task defect. The 20th remount command returned exit 32 inside the audit worker, and no task image ran. The offline build behaviour above is a separate result, found by running the original image.

## Note for users

No repair. The note says: "Grades correctly with the judge's network (Lake re-clones doc-gen4 at the manifest-pinned commit 86d735ec, valid result); cannot be graded offline; 15 of 370 aux targets exposed to renumbering (≤0.67%), untested".

## Limits and what was not run

- No model or solver re-runs were done. Effects are shown only on the unmodified-starter control.
- No honest-proof variant was scored, so the 15 exposed targets remain untested.
- The census listing was produced with plain `lean` instead of `lake build ListDeclAxiom`. It used the same helper file and the same oleans.
- The networked result depends on GitHub at run time. It was observed once.
- Submissions were built from the judge baseline sources. We did not check that the work-image starter is identical to them.
- The truth of individual targets was not audited.
- Whether the work image exposes upstream proofs was not checked. That includes the `Old/` directory mentioned in the README.

## Reproduce

- Networked `eval_cmd`: `evidence/scripts/lean_family_census/nf_networked.sh`. The outputs are in `evidence/scripts/lean_family_census/out/new_foundations_consistency/networked/`, including `report.json`.
- Offline `eval_cmd`: `evidence/scripts/lean_family_census/run_native.sh`. The failure log is `out/new_foundations_consistency/native/build_orig.err`.
- Census with the setup correction: `evidence/scripts/lean_family_census/nf_direct.sh`.
- Proof-style check: `evidence/scripts/lean_family_census/auxstyle/run.sh`. The output is in `auxstyle/nf_v4.21.out`.
- Supporting records: `evidence/reviews/lean_family_aux_census.md`, sections "Separate finding" and "Networked judge run".

