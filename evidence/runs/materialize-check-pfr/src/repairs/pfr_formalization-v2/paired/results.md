# Paired results: pfr_formalization-v2

## Setup

- **Where it ran.** On E2B workers (template `harbor-worker-v4`, 8 GiB, 21 GB disk), one worker per grader.
  Each grader ran in one container, offline, with `--network none --memory 6g --cpus 4`.
  - Original grader: `evidence/runs/pfr_formalization-v2-paired-v1/` (worker `i62dm5op893bgfth83j3k`,
    ledger `status: exit=0`). It used the pinned image
    `seededge/edgebench.judge.pfr_formalization@sha256:07b51e8e…cc4`.
  - Fixed version: `evidence/runs/pfr_formalization-v2-paired-v2/` (worker `igly5o4x6zy1rk90fl51h`,
    ledger `status: exit=0`). This worker rebuilt the package from scratch. It ran `materialize.sh`: it pulled
    the pinned image, extracted the original, checked its sha256, applied `repair.patch`, rebuilt the
    build artifacts inside the original image, and checked that the regenerated listing equals
    `out/v2-listing.txt` byte for byte. It then ran `docker build` with the unchanged `Dockerfile`,
    and graded in the image that build produced.
  - Two earlier attempts of the fixed-version job are kept for the record. `result-attempt1-disk/` failed
    because the work image and the grader image do not fit on one disk together. `result-attempt2-nopatch/`
    failed because the worker had no GNU `patch`. The ledger records `exit=` and `exit=0` for these two
    attempts, but neither graded anything.
- **Grader steps.** `grade_variants.sh` runs the task's `judge.eval_cmd`. It is read from `task.json`, a copy of
  `tasks/pfr_formalization.json`. For each submission it copies the starter, applies
  `make_variant.py`, removes `.lake`, runs `eval_cmd`, then lists the submission with `lake build ListDeclAxiom`.
  - **Deviation (disk).** Each worker had about 7.7 GB free (`mode.txt`), which is not enough for the
    eval_cmd's 7.0 GB `cp -r <judge>/.lake .`. Only that copy was replaced. The run copies `.lake/build` and
    symlinks the read-only, already built `.lake/packages`. Every other step ran verbatim. This is the same
    substitution as `evidence/runs/pfr_formalization-autoparam-eval/`, where the starter scored as in the
    verbatim local run.
- **Same inputs.** `make_variant.py` adds the same lemmas to each version's own starter. The trigger lemmas
  differ in one way only: where their measure binders come from. In the original they come from the
  section `variable`. In the fixed version they are written in the signature, as the fixed file states
  the five targets. Their printed types are identical apart from the auto-param argument
  (`out/variant_listing_compare.txt`). The downstream lemma `ebv_down_f2` has identical text in both versions.
- **Normalized score.** `rescale` is `linear` 0..1, so the normalized score is 100 × the raw score.

## Baseline (regenerated with the task's own tooling)

Source: `out/listing_compare.txt` (from `out/v1-listing.txt` and `out/v2-listing.txt`, job
`pfr_formalization-v2-build`, worker `ikwukudl3v2ka6ybgw4nb`, `status: exit=0`).

| | original grader | fixed version |
|---|---|---|
| `ListDeclAxiom` SUMMARY | checked=1124 bad=423 | checked=1120 bad=423 |
| scored targets | 423 | 423 (same 423 names) |
| lines that differ, other than auto-param helpers | – | exactly the 5 targets; each type is identical apart from the auto-param argument (`sorry` → `<lemma>._auto_1` / `._auto_3`) |
| auto-param helper declarations (`*._auto_N`, all OK, `axioms=[]`, never scored) | 39 | 35 |
| HASH checks (`weak_PFR`, `entropic_PFR_conjecture`) | true, true | true, true |

Type probe in the fixed baseline (`out/probe_v2_baseline.out`, `EbvProbe.lean`). All five targets give
`type_sorry=false`, and the axioms of their type alone are `[propext, Quot.sound, Classical.choice]`. Their
only `sorryAx` now comes from their own `sorry` proofs (`own_value_sorry=true`). In the original image the
same probe gave `type_sorry=true` for all five (`evidence/runs/pfr_formalization-autoparam-probe/result/out/probe_baseline.out`).

The rebuild rewrote 39 files (`out/v2-changed-files.txt`): the source plus the artifacts of `PFR.WeakPFR`,
`PFR.Examples`, `PFR` and `ListDeclAxiom`. Replaying `lake build ListDeclAxiom` in the built v2 image rebuilt
0 modules, and its listing was byte-identical to `out/v2-listing.txt` (`run.log` of the fixed-version job).

## Paired table

Source: `out/paired_table.md`, produced by `summarize.py` from the `report_*.json` and `listdecl_*.txt` files of the two jobs.

| variant | what it is | version | score | repaired / targets | new BAD declarations | added lemmas |
|---|---|---|---|---|---|---|
| starter | unchanged starter | original | 0.0 | 0/423 | – | – |
| | | fixed | 0.0 | 0/423 | – | – |
| T (trigger) | two lemmas proved by `rfl`, stated like the five targets (`ebv_trig_torsion`, `ebv_trig_f2`) | original | 0.0 | 0/423 | ebv_trig_f2, ebv_trig_torsion | both **BAD** `unexpected=[sorryAx]` |
| | | fixed | 0.0 | 0/423 | – | both **OK** `[propext, Classical.choice, Quot.sound]` |
| D (downstream) | T plus `ebv_down_f2`: ordinary binders, no auto-param, proof applies `ebv_trig_f2` | original | 0.0 | 0/423 | ebv_down_f2, ebv_trig_f2, ebv_trig_torsion | all three **BAD** `unexpected=[sorryAx]` |
| | | fixed | 0.0 | 0/423 | – | all three **OK** |
| BAD (bad control) | target `app_ent_PFR` proved from the still-sorried `app_ent_PFR'` (upstream proof); `ebv_bad_sorry` proved by `sorry` | original | 0.0 | 0/423 | ebv_bad_sorry | `app_ent_PFR` BAD, `ebv_bad_sorry` BAD |
| | | fixed | 0.0 | 0/423 | ebv_bad_sorry | `app_ent_PFR` BAD, `ebv_bad_sorry` BAD |

In every variant, `type_changed` = 0 and `disappeared` = 0 in both versions. The HASH checks are true, and no
penalty is applied. `eval_cmd` exited 0 in all 8 runs.

The 418 unaffected targets have the same status and the same type text in both versions in every
variant (`out/variant_listing_compare.txt`). The only non-helper lines that differ are the five targets
and the added lemmas.

The scores stay at 0 because no variant proves one of the five real targets. A real proof needs the
mathematics of the PFR project. The trigger lemmas carry exactly the same binders, so they show what such
a proof would earn. In the original grader, a lemma proved by `rfl` is still marked as depending on
`sorry`. In the fixed version it is credited.

## Downstream finding

`ebv_down_f2` has no auto-param, and its own type contains no `sorry` (`listdecl_v1_D.txt`). Its proof is a
single application of a lemma proved by `rfl`. The original grader marks it **BAD** `unexpected=[sorryAx]`.
`collectAxiomDeps` (`ListDeclAxiom.lean`) collects the axioms of the *type* of every constant a proof uses,
so the `sorry` in the auto-param spreads to every later declaration that uses one of the five lemmas.
The fixed version marks it OK.

## Acceptance

1. **Trigger: passes.** Lemmas stated like the five targets and fully proved are BAD in the original
   grader and OK in the fixed version. The five targets' types no longer contain `sorryAx`.
2. **Valid controls: pass.** The unchanged starter scores 0/423 in both versions. All 418 other targets are
   unchanged. The HASH checks pass. The downstream lemma is credited only in the fixed version.
3. **Invalid controls: pass.** A target proved through a sorried lemma, and a lemma proved by `sorry`, are
   BAD in both versions.

**Accepted.** The limits are in `../README.md`: the disk deviation in `eval_cmd`, the work image not built,
and no real proof of the five targets.

## Repeatability (2026-10-13)

| job | arms | runs | identical? |
| --- | --- | --- | --- |
| `evidence/runs/pfr_formalization-v2-paired-v1`, `-v1-rep2`, `-v1-rep3` (original grader) | starter, T, D, BAD | 3 | yes |
| `evidence/runs/pfr_formalization-v2-paired-v2`, `-v2-rep2`, `-v2-rep3` (fixed version, rebuilt from the package on each worker) | starter, T, D, BAD | 3 | yes |

Each rerun used the job's `run.sh`, `grade_variants.sh`, `make_variant.py` and `task.json` unchanged, on a fresh E2B worker. Every run has `status: exit=0`, and its worker was killed. In all three fixed-version runs, the rebuilt image's listing equals `out/v2-listing.txt` byte for byte (`built image listing == saved v2 listing` in `run.log`). Every variant gives the same result in all three runs under both graders: `valid` true, score 0.0, repaired 0/423, and the same OK/BAD status for `app_ent_PFR` and every added lemma (`report_*.json`, `listdecl_*.txt`). The reruns' submission copies (`WeakPFR_*.lean.sub`) and their `out.tar.gz` contain the image's starter. Like those of run 1, they were moved to `.internal/runs/<job>-sub/`.
