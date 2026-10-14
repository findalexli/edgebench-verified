# New Foundations Consistency (`new_foundations_consistency`)

**Outcome:** Kept, with a note. <mark>With network access, the original grader builds the project and returns a valid result for the unmodified starting project, but it cannot grade offline, and 15 compiler-generated scored items have an untested exposure of at most 0.67%.</mark>

## What the task asks

The task is a Lean project on the consistency of New Foundations, a set theory. Lean is a language for machine-checked mathematical proofs, and `sorry` is Lean's placeholder for a missing proof. The task text asks the solver to "finish **all** sorries in this folder" of the project, and says "we value minor progress". It also warns "do not modify the signature of existing lemma/theorem/def as these changes will not pass the judge evaluation", and "we check the axioms transitively, finishing a theorem without completeing precedent lemma will not count."

The score is the share of the starting project's declarations that depend on `sorry` and that the submission turns into declarations free of unapproved axioms, with unchanged printed types. Every scored item (target) has the same weight. The task card says `internet: false`. In the harness (`sforge/harness/run_evaluation.py`) this applies only to the agent's container; the grader's container is created without network restrictions. Category: Formal Math & Theorem Proving.

## What we checked

With network access, the grader builds and returns a valid result for the unmodified starting project. We did not score a real proof this way.

- Lake, Lean's build tool, printed `doc-gen4: URL has changed; deleting … and cloning again`, then `checking out revision '86d735ecf420e0dbaaf84e2fc2221969f9fca097'`. That is the commit pinned in the project's manifest, not a moving `main` branch, and its `lean-toolchain` is `v4.21.0-rc3`.
- The build succeeded, with `eval_cmd` rc=0 and no errors.
- The unmodified starting project got `valid: true` and `score: 0.0`, with `mode=unweighted, repaired=0/2246, remaining_bad=2246, new_bad=301`, 0 `type_changed`, 0 `disappeared`, and no HASH checks.
- The 301 `new_bad` entries are constants internal to the compiler (`_cstage2` 239, `_spec_N` 38, `_elambda_N` 24). They are not `sorry` targets and carry weight 0. They are also present in the starting project (2547 BAD lines against 2246 targets).

Grading offline is impossible. In the shipped grader image, `lake build` fails under `--network none`, both in the grader's starting repository and in a submission prepared by the exact `eval_cmd`.

- The cause is that Lake prints `doc-gen4: URL has changed; deleting '…/.lake/packages/doc-gen4' and cloning again` (`build_orig.err`). Our records also show the bundled checkout with no `origin` remote and with HEAD `0ee5b43…` instead of the manifest's `86d735ec…`. That state has no saved raw log; only `lean_family_aux_census.md` and a comment in `nf_direct.sh` record it.
- Offline, Lake deletes the checkout and tries to clone it again, which fails in `git` (exit code 128). `eval_cmd` then returns 1 and writes no JSON.
- The grader should give a valid result offline and gives none.

No compiler-generated target is unreachable, and a few carry a small untested exposure. Lean's compiler generates helper declarations automatically (`X._proof_N`, `X._simp_N`, …). In the task `lean_analysis_proofs`, the same grader credits these helper targets only when the exact generated name and printed type match, which makes some targets unreachable there. Here, we counted every target and found none that is provably out of reach for a complete, correct solution (lower bound 0).

| Targets | Helper targets | Helper share of score | Fragile helper targets | Targets with `sorry` in the type | Pairs of P and ¬P | Lower bound on unreachable targets |
|---|---|---|---|---|---|---|
| 2246 | 370 | 16.5% | **15 (0.67%)** | 0 | 0 | **0** (up to 0.67% exposed) |

- Kinds of helper targets: 337 `_proof`, 15 `_sizeOf`, 10 `match`, and others.
- The 15 fragile helpers are `BasePerm.instMulActionNearLitter._proof_1/2`, `instGroupNewPerm._proof_1…10`, `instInvNewPerm._proof_1` and `instMulActionNewPermCode._proof_1/2`. They are fields of instances that contain the placeholders directly, plus their sibling fields filled by default. A correct proof could renumber them.
- The 96 `_proof_N` helpers whose parent is a theorem are expected to be stable. In a check in core Lean with this image's compiler (4.21.0-rc3), we proved four `@[simp]` iff theorems that differ only by a constant in four ways (by `sorry`, by a term, by `omega` and by `simp`). In every style the helper is named `_proof_1` and its type is the theorem's own statement written as an equality (`auxstyle/nf_v4.21.out`). The `omega` proof also adds `_proof_1_1` and `_proof_1_2`, which are not targets. We did not score any of the 96 by running the grader.

The task ships with this note: "Builds and returns a valid result with the judge's network, shown on the unmodified starter only (Lake re-clones doc-gen4 at the manifest-pinned commit 86d735ec); cannot be graded offline; 15 of 370 aux targets exposed to renumbering (≤0.67%), untested".

## How much it matters

- The offline failure affects only graders without network access, which then give no score at all. EdgeBench's harness gives the grader network access, so in production it does not occur. Grading still needs GitHub to be reachable and to keep serving commit `86d735ec`.
- Renumbered helpers can cost at most 0.67% of the score, and only for solvers who fill the affected instance fields. This is an upper bound on exposure, not a measured loss.

The task does not change; the note above ships with it.

## How we checked it

- We ran the original grader in the original public image, pinned by digest (toolchain v4.21.0-rc3). The task's `judge.eval_cmd` ran exactly as written on the grader's unmodified starting sources, one container at a time, with `--memory 4g --cpus 2`: once with `--network none` and once on the default bridge network with `timeout 3600`.
- To count targets, we had to work around Lake, which cannot build offline in this image. We produced the target listing with the same `ListDeclAxiom` helper from the image, run through plain `lean`, with a `LEAN_PATH` built from the compiled files (oleans) already in the image. We then applied the grader's target rule with the same classifier we used for the other Lean tasks.
- The check that proof style does not change names is the core Lean check described above, run with the image's compiler.

## Limits

- We ran no AI model or solver. The effects shown come only from the unmodified starting project.
- We scored no real proof, so the 15 exposed targets remain untested.
- We produced the target listing with plain `lean` instead of `lake build ListDeclAxiom`, using the same helper file and the same oleans.
- The result with network access depends on GitHub at run time, and we observed it once.
- We built test submissions from the grader's starting sources and did not check that the starting project in the agent's work image is identical to them.
- We did not check whether each individual target is true.
- We did not check whether the work image exposes proofs from the source project, including the `Old/` directory mentioned in the README.

## Reproduce

- Grader image digest: `sha256:c17cd565…cc4`.
- `eval_cmd` with network access: `evidence/scripts/lean_family_census/nf_networked.sh`. It writes its outputs, including `report.json`, to `evidence/scripts/lean_family_census/out/new_foundations_consistency/networked/`.
- `eval_cmd` offline: `evidence/scripts/lean_family_census/run_native.sh`. The failure log is `out/new_foundations_consistency/native/build_orig.err`.
- Count of targets: `evidence/scripts/lean_family_census/nf_direct.sh`.
- Proof-style check: `evidence/scripts/lean_family_census/auxstyle/run.sh`. The output is in `auxstyle/nf_v4.21.out`.
- Supporting records: `evidence/reviews/lean_family_aux_census.md`, sections "Separate finding" and "Networked judge run".
