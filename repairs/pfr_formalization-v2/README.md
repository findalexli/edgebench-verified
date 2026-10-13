# PFR formalization, fixed version (`pfr_formalization`)

**Validation scope:** The paired controls establish removal of type contamination using analogous added lemmas. They do not prove the five actual affected targets or demonstrate recovered target points. The solver image was not built. Matching two styles for one helper does not establish proof-style fairness for all seven helpers.


## What this fixes

Five of the 423 scored statements carry a real `sorry` in their type, so the original grader can never
credit them. The cause is in how `PFR/WeakPFR.lean` declares two automatic measure arguments, and Lean
reports no error for it. Every later lemma whose proof uses one of the five is marked as depending on
`sorry` too. The fixed version moves those two arguments into the five statements, so their types are
clean. No other statement changes.

## What changes

### The problem in detail

`PFR/WeakPFR.lean` is a `module` file. It declares `(μ : Measure Ω := by volume_tac) (μ' : Measure Ω' := by volume_tac)`
twice in a `variable` command: in section `Torsion` and in section `F2_projection`. The five lemmas
`torsion_free_doubling`, `torsion_dist_shrinking`, `app_ent_PFR`, `PFR_projection'` and `PFR_projection`
take these as automatic arguments.

In a `module` file, a public statement cannot refer to the private helper that holds the
`by volume_tac` tactic. Lean puts an error `sorry` there instead and reports nothing. The printed type
shows `μ : autoParam (Measure Ω) sorry`, and the type contains the constant `sorryAx`.

The grader's `ListDeclAxiom.lean` (`collectAxiomDeps`) collects axioms from a declaration's type as well as
its proof, so these five are always BAD. A solver who changes the statement to remove the `sorry` is scored
"type changed". Evidence:

- `evidence/runs/pfr_formalization-autoparam-probe/`: `sorryAx` is in the type of all five.
- `evidence/runs/pfr_formalization-autoparam-eval/`: a lemma proved by `rfl` under the same binder is
  marked BAD by the task's grader.

The same rule reaches further. The original grader also marks BAD a lemma whose proof only *uses* such a
lemma (`paired/results.md`, variant D, measured).

The upstream PFR proofs build a chain through the five:

- `app_ent_PFR` → `PFR_projection'` → `PFR_projection`;
- `torsion_free_doubling` → `torsion_dist_shrinking`;
- `torsion_dist_shrinking` and `PFR_projection` → `weak_PFR_asymm_prelim` → `weak_PFR_asymm` → `weak_PFR` → `weak_PFR_int`.

A solver who follows those proofs would lose those four later targets as well.

### Exact change

- `PFR/WeakPFR.lean`, in two places:
  - The two measure binders and their `[IsProbabilityMeasure μ] [IsProbabilityMeasure μ']` instances are
    removed from the `variable` commands of sections `Torsion` and `F2_projection`.
  - The same four binders are written at the start of the signature of each of the five lemmas
    (`repair.patch`). `X` and `Y` stay in `variable`, so the order of all binders is unchanged.
- The edit goes into both copies of the file:
  - the grader's baseline repository `/home/workspace/judge/se-bmk-intern/pfr`, the only copy in the grader
    image (`Dockerfile`);
  - the solver's starter `/home/workspace/se-bmk-intern/pfr` (`Dockerfile.work`). In the pinned work
    image, every `PFR/*.lean` file is byte-identical to the grader's (sha256 compared in job
    `pfr_formalization-v2-extract`).
- The grader regenerates its baseline at grading time with `lake build ListDeclAxiom` in the baseline repo.
  The package ships the rebuilt build artifacts (`files/judge/v2-build-artifacts.tar`, 39 files: the
  source and the outputs of `PFR.WeakPFR`, `PFR.Examples`, `PFR` and `ListDeclAxiom`), so that step is a replay.
- `eval_lean.py`, `ListDeclAxiom.lean`, `eval_cmd`, the timeout, the parser and the score scale are unchanged.
- `task.json.in` changes only `work.image_tag` and `judge.image_tag`. They are placeholders until the images
  are published.

**Target set.** It is the same 423 names. In the regenerated listing (`paired/out/listing_compare.txt`),
the only non-helper lines that differ are the five targets. Each type is identical apart from the
auto-param argument: `sorry` becomes `<lemma>._auto_1` and `<lemma>._auto_3`. The HASH checks on `weak_PFR`
and `entropic_PFR_conjecture` still pass.

### Why this is the smallest change

- One file changes. Two `variable` lines are removed, and the same binders are added to five signatures. No statement changes its meaning.
- Nothing in the grader changes.
- The grader-only alternative used in `lean_analysis_proofs-v2` was not needed. That alternative excludes
  targets whose type text contains `sorry`, which would drop the five targets and leave the downstream
  problem in place.

### Are scores comparable? The score scale

- The denominator stays at 423.
- Every submission that does not prove one of the five, or a lemma that uses them, scores exactly as before.
  In the paired run, the 418 other targets have the same status in every variant.
- A submission that proves them can now earn up to 5/423 = 1.18 more points. One that also proves the four
  later `weak_PFR*` targets through them can earn up to 9/423 = 2.13 more points.
- The reference points of the score scale (`rescale`) are kept: `linear`, lower 0.0, upper 1.0. They are the
  exact bounds of the pass rate, not reference points taken from a leaderboard.

Scores below the cap are comparable with the original. Under the original grader, a submission could have
had lemmas silently marked BAD.

### Files

- `Dockerfile`: the fixed grader.
- `Dockerfile.work`: the fixed solver image. It was built once, in the clean-machine rebuild check (`evidence/runs/materialize-check-pfr`); no solver ran in it.
- `repair.patch`: our diff.
- `materialize.sh`: rebuilds `files/` and `orig/`.
- `source-lock.json`.
- `task.json.in`.
- `paired/`: the run scripts, `results.md` and outputs. The raw reports are in
  `evidence/runs/pfr_formalization-v2-paired-v{1,2}/`.

## How it was checked

The side-by-side run of the original and fixed graders is in `paired/results.md`. Each grader ran four
submissions:

- **The unchanged starter.** It scores 0 of 423 under both.
- **Two lemmas stated exactly like the five targets and proved by `rfl`.** The original grader marks
  them as depending on `sorry`. The fixed version credits them.
- **A lemma that only applies one of those.** It is marked as depending on `sorry` in the original and
  credited in the fixed version.
- **A bad control.** It proves a target through a lemma that still uses `sorry`, and adds a lemma proved by
  `sorry`. Both versions reject it.

The fixed-version run rebuilt the whole package from the public image on the worker, including the Lean
rebuild and `docker build`, and graded in the image it built.

## Build and use

```bash
./materialize.sh && docker build -t ebv/pfr_formalization-judge:v2 .
docker build -f Dockerfile.work -t ebv/pfr_formalization-work:v2 .   # built once; no solver run in it
```

`materialize.sh` takes these steps:

1. Pull the pinned grader image.
2. Extract `PFR/WeakPFR.lean` with `docker create` + `docker cp`, and check its sha256.
3. Apply `repair.patch`.
4. Rebuild `files/judge/v2-build-artifacts.tar` inside the original grader image. This runs
   `lake build ListDeclAxiom` and `lake build`, offline, with `--memory 6g --cpus 4`, in about a minute.
   It holds `/tmp/ebv-heavy.lock`.
5. Verify the outputs. The rebuild is accepted when two checks pass:
   - the rewritten file set equals the 39 members locked in `source-lock.json`;
   - the regenerated listing equals `paired/out/v2-listing.txt` byte for byte.

   Oleans are not expected to be byte-identical.
6. Only then pull the pinned work image and check the sha256 of its copy of `PFR/WeakPFR.lean`. The two
   images do not fit together on a 21 GB machine, so the grader image is removed first when this run
   pulled it (`MATERIALIZE_KEEP_IMAGES=1` keeps it; otherwise `docker build .` pulls it again).

`materialize.sh` is adapted by hand from `tools/materialize.sh.in`. The template's Lean rebuild step is
specific to `lean_analysis_proofs`, so `tools/make_materialize.py` has no entry for this package yet.

## Limits

- **No real proof of the five targets was run.** A real proof needs the mathematics of the PFR project.
  The trigger lemmas carry the same binders and are fully proved. The type probe shows that the five
  targets' types are free of `sorryAx` in the fixed version (`paired/out/probe_v2_baseline.out`).
- **Disk deviation.** In both graders, the eval_cmd's 7.0 GB copy of `.lake` was replaced by a copy of
  `.lake/build` plus a symlink to `.lake/packages`, for lack of disk on the workers. Every other step ran
  verbatim.
- **Work-image check skipped on the grading worker.** The work image (about 11 GB on disk) and the grader
  image do not fit on one 21 GB worker. The grading worker therefore ran `materialize.sh` without the
  work-image lines (`paired/out/materialize.nowork.diff`). That check was done separately, in job
  `pfr_formalization-v2-extract`, and again in the clean-machine rebuild check
  (`evidence/runs/materialize-check-pfr`, `status: exit=0`; work-image starter sha256 matched the lock). Since
  2026-10-13 `materialize.sh` itself pulls the work image only after the grader steps (step 6), so the
  unchanged script fits a 21 GB machine. That reordered script has been tested with a stub `docker` only,
  not yet on a real worker.
- **`Dockerfile.work` was built once, but no solver ran in it.** The clean-machine rebuild check built it
  and found the installed `PFR/WeakPFR.lean` with the locked sha256. The solver's first `lake build`
  recompiles `PFR.WeakPFR`, `PFR.Examples` and `PFR`; that was not run.
- **Not verified, and why: credit for the five actual targets.** Checking that a real proof of the five
  repaired targets now earns credit needs real proofs of those theorems, which take the mathematics of the
  PFR project (porting them from teorth/pfr is a project of its own). The trigger lemmas stand in for them.
  This is kept as a documented limitation.
- **Downstream count is inferred.** That the four `weak_PFR*` targets would be lost follows from the upstream
  proof structure (teorth/pfr `master`) and the measured rule (variant D). It was not measured with real
  proofs.
