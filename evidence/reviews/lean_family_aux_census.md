# Census: does the auxiliary-name scoring defect affect the six other Lean tasks?

## Question

`reviews/lean_aux_name_scoring.md` showed, natively for lean_analysis_proofs, that the shared grader
(`eval_lean.py`, sha256 `3319767e…`) gives credit for compiler-generated auxiliary targets
(`X._proof_N`, `X._simp_N`, …) only when the exact name and the printed type match. As a result,
honest complete solutions lose points and scores depend on proof style.

Does the same thing happen, and how much, in these six tasks?
- combinatorial_games_formalization
- carleson_formalization
- flt_regular_formalization
- new_foundations_consistency
- pfr_formalization
- sphere_eversion_formalization

Scope: good-faith scoring only. No tamper or exploit submissions were built.

## Method (scripts: `scripts/lean_family_census/`)

**Images.** Each judge image was pulled by digest, used, then removed with `docker rmi` before the
next was pulled.
- One container at a time, run with `--network none --memory 4g --cpus 2`.
- Free disk was checked before each pull (391 GB or more every time).
- From the restart onwards, every heavy step held `/tmp/ebv-heavy.lock`.
- No Lean ran on the host.
- Public pulls used an empty per-process `DOCKER_CONFIG`. The configured `desktop.exe` credential helper fails under WSL. No global setting was changed.

**Census steps.**
1. `census.sh` → `census_in.sh` runs inside the image. It records the effective `eval_lean.py`,
   `ListDeclAxiom.lean`, lakefile and manifest hashes. It runs `lake build ListDeclAxiom` in the judge
   baseline repo; this is the baseline listing `eval_lean.py --baseline-repo` uses. It then runs the
   grader once with the unmodified baseline as the submission, which should score 0.
2. `classify.py`:
   - Uses the same target rule as the grader (BAD and depends on `sorryAx`; for FLT, the weights-file entries).
   - Uses the same auxiliary-name regex as `scripts/lean_aux_names/classify_baseline.py`.
   - Counts class A (`sorry` in the printed type) and class B (P/¬P auxiliary pairs) with the same logic as `contradictory_aux.py`.
   - Counts class C (duplicate `_proof_N` types) with the same logic as `dup_aux.py`.
   - Self-check on the lean_analysis baseline: it reproduces 2901 / 559 / 35 / 12 / 13.
   - New rule: `autoParam (T) sorry` is how the printer shows an auto-param *tactic*, so it is not counted as a hole.
3. `AuxProbe.lean.tmpl` and `probe.sh`, run in the image. For every auxiliary target they record
   whether its **own value** contains `sorryAx` directly (the hole was abstracted into the auxiliary),
   or whether it reaches `sorry` only transitively through other constants. `probe_summary.py` then
   marks as *fragile* every auxiliary with its own hole, or whose non-theorem parent has a hole. These
   are the only ones exposed to renumbering, deduplication or binder changes when a solver fills a hole.
   The rest are byte-identical declarations that a solver has no reason to edit.
4. `run_native.sh` runs the task's `judge.eval_cmd` **verbatim**, read from `tasks/<id>.json`.
   - The submission is the judge baseline sources without `.lake`. The work-image starter was not pulled.
   - The run includes the `.lake`/manifest swap and the full `lake build`.
   - It runs first on the unmodified sources, then on honest variants of a single file.
5. `auxstyle/AuxStyle.lean`, core Lean only, run with the image's own toolchain. It records which
   auxiliary names an `@[simp]` iff theorem produces under different proof styles.

## Effective grader files (from inside each image)

| task | toolchain | `eval_lean.py` | effective `ListDeclAxiom.lean` | HASH lines printed |
|---|---|---|---|---|
| combinatorial_games | 4.28.0 | `3319767e…` | `5edb20a7…` | none |
| carleson | 4.30.0-rc2 | `3319767e…` | `7ad881a0…` | `classical_carleson_check` (true) |
| flt_regular | 4.28.0 | `3319767e…` | `0eee3e92…` | `flt_regular` (true) |
| new_foundations | 4.21.0-rc3 | `3319767e…` | `b585194f…` | none (prefix test `startsWith "ConNF"`) |
| pfr | 4.29.0 | `3319767e…` | `0ea47b53…` | `weak_PFR`, `entropic_PFR_conjecture` (true) |
| sphere_eversion | 4.28.0 | `3319767e…` | `4b74bf12…` | `Gromov` (true) |

- `eval_lean.py` is the same in all six. Every effective helper differs from the exported copy
  hashed in `_lean-formalization-tasks.md`, so the caveat recorded there was justified.
- Each image contains only one `ListDeclAxiom.lean`.
- The HASH coverage stated in the earlier review is confirmed, now on the effective helpers.

## Census results

Unweighted unless stated otherwise. "Aux" means names matching the regex.

| task | targets (weight) | aux targets | aux share of score | aux kinds | fragile aux (own or same-parent hole) | `sorry` in type | P/¬P pairs | lower bound on unattainable |
|---|---|---|---|---|---|---|---|---|
| combinatorial_games | 3732 | 937 | 25.1% | 450 `_simp`, 432 `_proof`, 25 `_unsafe_rec`, 13 `eq_def`, 8 `eq_N`, … | **0** | 0 | 0 | **0** |
| carleson | 3004 | 151 | 5.0% | 90 `_proof`, 19 `_simp`, 11 `congr_simp`, 10 `eq_def`, … | **0** | 0 | 0 | **0** |
| flt_regular | 25 (weight 87) | **0** | 0% | none | 0 | 0 | 0 | **0** |
| new_foundations | 2246 | 370 | 16.5% | 337 `_proof`, 15 `_sizeOf`, 10 `match`, … | **15 (0.67%)** | 0 | 0 | **0** (up to 0.67% exposed) |
| pfr | 423 | 7 | 1.65% | 7 `_simp` | **0** | 0 (see note) | 0 | **0** |
| sphere_eversion | 661 | 119 | 18.0% | 94 `_proof`, 23 `_simp`, … | **0** | 0 | 0 | **0** |

- **FLT weights.** There are 25 entries and the total weight is 87 (weights 1 to 6). They are exactly
  the 25 BAD+sorry declarations in the listing, and all 25 type texts equal the listing's. None of them is an
  auxiliary name.
- **PFR note.** A plain `sorry` search finds 5 targets (`PFR_projection`, `PFR_projection'`,
  `torsion_free_doubling`, `torsion_dist_shrinking`, `app_ent_PFR`). In all of them the token comes
  from `μ : autoParam (Measure Ω) sorry`, which is the printer's rendering of an auto-param tactic.
  The real-hole probe (`type_sorry`) is false for them. They are not class A.
- **Class C.** A lexical count finds duplicate types for 33 auxiliaries in combinatorial_games and
  8 in carleson. Every one of them is transitive-only: it carries no hole of its own and is never
  re-elaborated by an honest proof. Deduplication only applies when a hole is filled, so these are
  **not** at risk. That is unlike lean_analysis, where the duplicates were copies of a sorried hole.
- **Why the difference from lean_analysis.** These starters were made by replacing *theorem* bodies
  with `sorry`.
  - The probe found no auxiliary whose own value contains `sorryAx` in five of the six tasks. New
    Foundations has 12 own-hole auxiliaries and 3 siblings.
  - Instance and def auxiliaries such as `copy._proof_1` and `instBoundedOrder._proof_2` are BAD only
    because the original upstream proof term they contain calls a sorried theorem.
  - In lean_analysis, by contrast, the holes are inside def and instance fields, so the auxiliary *is* the hole.
- **New Foundations, the fragile 15.** They are `BasePerm.instMulActionNearLitter._proof_1/2`,
  `instGroupNewPerm._proof_1…10`, `instInvNewPerm._proof_1` and `instMulActionNewPermCode._proof_1/2`.
  These are instance fields with direct holes, plus their default-field siblings (`npowRecAuto 0 x = …`).
  An honest fill can renumber them, as in lean_analysis variant W. This was not tested natively,
  because the eval command cannot run offline (see below). So 0.67% is an upper bound on exposure,
  not a measured loss.

## Native tests (exact `eval_cmd`, unmodified grader)

**Controls.** The unmodified starter scores 0 with no `type_changed` and no `disappeared`:
- combinatorial_games 0/3732;
- carleson 0/3004;
- FLT 0/25 (weight 0/87);
- pfr 0/423;
- sphere 0/661.

This holds even where `eval_cmd` swaps in the shared baseline `.lake` (Mathlib `3203991…`, which
differs from the judge repo's Mathlib) and rebuilds the whole project: combinatorial_games, FLT and
sphere. The Mathlib swap does not change any printed target type in these tasks.

**combinatorial_games** (`cg_native/`). `SignExpansion/Basic.lean` is a leaf module. Six sorried
theorems were proved honestly, with no signature change:
- `isUpperSet_preimage_singleton_zero`
- `copy_eq`
- `coe_mk`
- `sign_eq_coe`
- `le_iff_toLex`
- `lt_iff_toLex`

There were two styles: A is term mode (`x.isUpperSet_preimage_singleton_zero'`, `rfl`, `Iff.rfl`) and B
is tactic mode (`cases … exact`, `cases h; cases x; rfl`, `constructor <;> exact id`).
- **A and B both scored 16/3732, with the identical repaired set** (`native/repaired.txt`). That set
  is the 6 theorems plus `copy`, `instBoundedOrder` and 7 auxiliaries:
  - `copy._proof_1`
  - `instBoundedOrder._proof_1/_2`
  - `instCompleteLinearOrder._proof_1…5`
- Nothing was type-changed or disappeared.
- So the auxiliaries are credited, and the credit does not depend on proof style.

**pfr** (`pfr_native/`). `@[simp] mem_symmGroup` in `PFR/HundredPercent.lean` was proved with
`Iff.rfl` (A) and with `constructor <;> intro h <;> exact h` (B). Both scored 2/423:
`mem_symmGroup` and `mem_symmGroup._simp_1`.

**Auxiliary names by proof style** (`auxstyle/`, core Lean, run with each image's own compiler):
- An `@[simp]` iff theorem proved by `sorry`, by a term, by `omega` or by `simp` always gets its
  iff→eq auxiliary under the same name and type: `_proof_1` on 4.21.0-rc3 (New Foundations) and
  `_simp_1` on 4.30.0-rc2 (carleson).
- `omega` adds its own lemmas as `_proof_1_1`/`_proof_1_2`. They do not displace the simp auxiliary.
- So New Foundations' 96 theorem-parent `_proof_N` auxiliaries, and the `_simp_N` auxiliaries elsewhere, are stable.
- Side observation: on 4.21, identical auxiliary types are shared through deduplication. An `@[simp]`
  theorem whose iff→eq type already exists gets no auxiliary of its own.

## Separate finding: new_foundations_consistency cannot be graded offline

In the shipped judge image, `lake build` fails under `--network none`. This happens both in the judge
baseline repo and in a submission prepared by the verbatim `eval_cmd`
(`out/new_foundations_consistency/native/build_orig.err`):
- The `.lake/packages/doc-gen4` checkout has no `origin` remote, and its HEAD `0ee5b43…` does not match
  the manifest's `86d735ec…`.
- Lake reports `doc-gen4: URL has changed; deleting … and cloning again` and then fails on `git` (exit code 128).

Consequences:
- `eval_cmd` returns 1 and produces no JSON, so every submission would be ungradeable unless the judge has network.
- With network access, the result would depend on whatever `doc-gen4@main` is when the judge runs.
- I did not determine whether the production judge has network. The task card says `internet: false`,
  which may refer only to the solver.

To get the census anyway, I made one setup correction (`nf_direct.sh`): I ran the same in-image helper
with plain `lean` and a `LEAN_PATH` built from the already-compiled oleans, bypassing Lake.

## Verdicts

| task | aux-name defect material? | reason |
|---|---|---|
| combinatorial_games | **No** | No fragile auxiliaries. Measured: honest proofs earn the auxiliaries in both styles. 25% of the score is auxiliaries, earned automatically once their dependencies are proved (weighting skew, not unfairness) |
| carleson | **No** | 0 fragile, 0 class A/B. Not tested natively, beyond the control |
| flt_regular | **No (not applicable)** | Weighted; 0 auxiliary targets |
| new_foundations | **No for ceilings; minor exposure** | 0 class A/B. 15 fragile instance-field auxiliaries (≤0.67%) could be renumbered by some proof styles (untested natively). Grading is blocked offline by the Lake/doc-gen4 failure |
| pfr | **No** | 7 `_simp` auxiliaries, stable (measured). The 5 apparent `sorry` types are autoParam rendering |
| sphere_eversion | **No** | 0 fragile, 0 class A/B. Not tested natively, beyond the control |

**Summary.** For these six tasks, no target is unattainable for an honest, complete solution: the
lower bound is 0 in every task. Compare at least 49/2901 (1.69%) for lean_analysis_proofs. The
defect is real but specific to lean_analysis, where the holes sit inside def and instance fields.
The repair recommendation to drop auxiliary names from the target set still applies family-wide:
- it makes no difference to soundness;
- it removes the 5-25% weighting skew toward theorems that many definitions depend on;
- it protects New Foundations' 15 exposed targets.

It is not needed to fix unattainable ceilings in these six.

## Limits

- I did not check that the work-image starter equals the judge baseline sources. The submissions were built from the judge baseline sources.
- The native honest tests cover one leaf module each in combinatorial_games and pfr; carleson and sphere had controls only.
  The fragile/stable classification for carleson, sphere and New Foundations comes from the in-image
  probe, not from scoring runs.
- A solver that edits def or instance bodies (signatures unchanged, which the prompt allows) could
  still renumber transitive auxiliaries. That is outside honest theorem-proving and was not measured.
- The New Foundations listing was produced with plain `lean` instead of `lake build ListDeclAxiom`.
  It used the same helper file and the same oleans.
- The first combinatorial_games full-build run was interrupted by a host out-of-memory restart, caused by
  concurrent jobs. It was rerun under the lock; the interrupted log is kept as `native.attempt1-host-oom.log`.
- The FLT `native.log` shows no-op A/B rows caused by a script default bug, which is now fixed. Those reports were deleted.

## Networked judge run (new_foundations_consistency, follow-up)

The coordinator reports that the maintained harness gives the judge container network access.
`internet:false` applies only to the agent container (`sforge/harness/run_evaluation.py`). To check what
happens in that setting, I re-pulled the image by digest and ran the verbatim `eval_cmd` on the
unmodified starter (the judge baseline sources) **with network**.

**Setup.** Script `scripts/lean_family_census/nf_networked.sh`.
- Default bridge network, `--memory 4g --cpus 2`, `timeout 3600`, run under the heavy-job lock.
- The image was removed afterwards.
- Outputs are in `out/new_foundations_consistency/networked/`.
  `report.json` has sha256 `72004d24c20c6b3130239ad6c669ff9bb6f31c147ccc5a4881818e429b99c55a`.

**What Lake did.**
- It printed `doc-gen4: URL has changed; deleting … and cloning again`.
- It then printed `checking out revision '86d735ecf420e0dbaaf84e2fc2221969f9fca097'`.
- This is the **manifest-pinned** commit, not a moving `main`. After the run, both the submission's and the
  judge repo's `doc-gen4` are at `86d735ec…`, with origin `https://github.com/leanprover/doc-gen4`. That
  revision's `lean-toolchain` is `v4.21.0-rc3`.

**Result.**
- The build succeeded (`eval_cmd` rc=0, no errors, 07:29:15 to 07:30:07 UTC).
- The grader returned `valid: true`, `score: 0.0`:
  `mode=unweighted, repaired=0/2246, remaining_bad=2246, new_bad=301`.
  It reported 0 `type_changed`, 0 `disappeared`, and no HASH checks.
- The 301 `new_bad` entries are compiler-internal constants (`_cstage2` 239, `_spec_N` 38, `_elambda_N` 24).
  They are BAD without being sorry targets, carry weight 0, and are present in the baseline as well
  (2547 BAD lines against 2246 targets).

**Conclusion.** With network access, grading works today and is reproducible: the clone is pinned to
the manifest commit. The offline failure recorded above affects only network-isolated judges. It is not a
production defect under the maintained harness. One residual dependency remains: grading needs GitHub to
be reachable and to keep serving commit `86d735ec`.
