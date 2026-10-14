# Applying the fixes

Each repair package defines a new version of an original EdgeBench task, in EdgeBench's own
format. The packages are validated to different depths, and the status table and each package's
limits are the authoritative record. The original release is left as it is. Its task definitions stay
in `tasks/`, and each fix uses the original software images, unchanged, as its base.

## What a fix contains

Each fix lives in its own folder, `repairs/<task_id>-v2/` ("v2" marks the fixed version).

| File | What it is |
| --- | --- |
| `README.md` | What the fix changes, how it was tested, and its limits |
| `repair.patch` | The change itself, as a standard diff against the original files |
| `materialize.sh` | Rebuilds the changed files: downloads the original public image, extracts the original files, applies the patch, and checks every result against the fingerprints in `source-lock.json` |
| `Dockerfile` (and `Dockerfile.work` when the agent's starting files change) | Builds the fixed image on top of the exact original image, adding only the changed files |
| `task.json.in` | The fixed task definition: a copy of `tasks/<task_id>.json` with only the necessary fields changed |
| `paired/` | The side-by-side test, in which the original and the fixed grader grade the same test submissions |

The packages contain only the patch and no copies of the original files, so we can publish the fixes
without redistributing EdgeBench's images.

## Build and use one fix

```bash
cd repairs/<task_id>-v2
./materialize.sh                     # regenerate the changed files from the public image
TAG=$(python3 -c "import json;print(json.load(open('task.json.in'))['judge']['image_tag'])")
docker build -t edgebench.judge.<task_id>:$TAG .
# if the package has Dockerfile.work, also build edgebench.work.<task_id>:<work image_tag> from it
# Arc Compiler Runtime and Borden Source Inversion change only the agent's environment: their Dockerfile
# builds edgebench.work.<task_id>:<work image_tag> (Arc: docker build -f Dockerfile files)
cp task.json.in <your EdgeBench checkout>/tasks/<task_id>.json   # not this repository's tasks/, which is locked to the original
```

EdgeBench's runner finds images by the names `edgebench.judge.<task_id>:<image_tag>` (the grader)
and `edgebench.work.<task_id>:<image_tag>` (the agent's environment), reading the tags from the task
definition. These tags name images you build locally; we publish no fixed image to a registry.
Warehouse also needs the host-side final-drain overlay described below. Replacing only its task
definition and grader image leaves the 900-second defect in final-result collection.
Maintainers who build images from source can apply `repair.patch` to their source tree instead.
The paths in the patch are the paths inside the image.

## Warehouse host-side integration

The [final-drain overlay](repairs/harness-final-drain-v1/README.md) is separate from the Warehouse
judge-image patch. It polls until every recorded job is in a terminal state, waits for a bounded
time that takes the queue into account, and reports a failure instead of returning an incomplete
final score. Materialize it into a new source directory and run the harness from that directory;
this repository's locked `sforge/` mirror stays unchanged. Its paired deterministic tests exercise
the real patched drain and result assembly, including a long evaluation and a serial queue (a
conservative model, since the upstream judge server grades submissions concurrently). We have not
verified full Docker/Kubernetes integration. The overlay changes final-result collection for every
task run through the materialized tree. It can wait up to `300 + n·(eval_timeout + 300)` seconds for
`n` pending submissions and keeps the work sandbox allocated meanwhile, so use it for Warehouse runs
or accept that change.

## Test a fix yourself

`paired/run.sh` reruns the side-by-side test. Most published runs used E2B cloud sandboxes with 8
virtual CPUs and 8 GiB of memory, with the grader limited to the CPU count each case page states
(1 to 8). These fixes use other scripts:
- Lean Analysis uses `paired/run_local.sh`, which we ran on a local host with 16 CPUs and 15 GB.
- OpenRCT2 has no run script, because its fix changes only the instructions and nothing that runs.
- Git in Zig uses `paired/run_gates.sh` and `paired/run_oracle.sh`.
- PFR Formalization uses `paired/build_v2.sh` and `paired/grade_variants.sh`.
- Rust Multicrate uses the templates `paired/run-paired.sh.in` and `paired/run-failfast.sh.in`.
- Triangulation and Warehouse Routing also have `paired/run-cpu4.sh` for the 4-CPU tests.
- The separate host overlay uses `python3 repairs/harness-final-drain-v1/test_drain.py` from the repository root (deterministic component tests, no cloud calls).

Each package's results are in its `paired/results.md`, and all of them are in
[data/paired-results.csv](data/paired-results.csv). The status table separates demonstrated controls
from incomplete release validation, component tests and documentation-only changes. The acceptance
criteria are:
- the test submission that shows the problem is now graded correctly;
- correct test submissions keep their scores, or the change is explained;
- wrong test submissions are still rejected.

## Scores are not comparable across versions

A score from a fixed version cannot be compared with a score from the original task or the original
leaderboard. Regrade submissions with the fixed version instead of mixing the two. Each fix's
README says which submissions' scores change.

## What each fix changes

| Task | What changes | Fixed grader image tag | Fixed work image tag | Status |
| --- | --- | --- | --- | --- |
| [Apple Incremental Game](repairs/apple_incremental_game-v2/README.md) | grader | `16968d8ec7f2-ebv-v2` | unchanged | CPU-share controls validated: three identical paired native runs at 4 CPUs plus a pair at 8 CPUs (each ledger exit=0); package rebuilt from scratch on a clean machine (materialize-check-g1). Not tested in a Kubernetes pod or at 3 or 5-7 CPUs; below 3 CPUs a submission that reaches eval_timeout loses its whole output. |
| [Arc Compiler Runtime](repairs/arc_compiler_runtime-v2/README.md) | agent's starting files | `200e176a8e30` | `v2-analyze-contract-docs` | Documentation repair with the judge unchanged: three paired runs (exit=0) give byte-identical per-suite results under v1 and v2; v2 work image built in the worker and in the clean-machine rebuild (materialize-check-g3). Blind-solver benefit not shown; the work image tag is a local build tag, not a published image. |
| [Borden Source Inversion](repairs/borden_source_inversion-v2/README.md) | agent's starting files, task instructions, score scale | `cc54d4fd7006` | `f389fcf94240-ebv-v2.1` | Two side-by-side native runs and their repeats (all finished) give identical raw results under the original and fixed versions; the shipped forward model equals the grader's; 109 is the exact computable maximum; package rebuilt from scratch on a clean machine (materialize-check-g3). No agent run on v2; the effect rests on one textbook variant. |
| [College English Exam Bank](repairs/college_english_exam_bank-v2/README.md) | grader | `6628b6d3f834-ebv-v2.2` | unchanged | v2.2 validated by three identical paired runs of the original, v2.1 and v2.2 graders on 29 responses (college_english_exam_bank-v2-paired-fix3, -fix3-rep2, -fix3-rep3; each ledger exit=0; package materialized with its own materialize.sh in each). The model's answers were fixed stubs; no AI model was called. The Lean model covers v2.1, not v2.2's block selection or decimal-string reading. |
| [CTA Risk Budget Optimization](repairs/cta_risk_budget_optimization-v2/README.md) | grader | `a9651058ecef-ebv-v2.1` | unchanged | v2.1 image materialized and built in the worker from the package; native paired runs cta_risk_budget_optimization-v2.1-native-rep1..3 (each ledger exit=0) on the shipped standard answer and authored full submissions that pass the volatility, drawdown and participation gates; helper controls (13) pass against an exact oracle. No solver output graded. |
| [D-ABIC Gravity Inversion](repairs/dabic_gravity_inversion-v2/README.md) | grader | `517eb738b87b-ebv-v2` | unchanged | partial fix; task removed; Historical paired scope only; see the case page and package limits |
| [Equivalence Class Divide and Conquer](repairs/equivalence_class_divide_and_conquer-v2/README.md) | grader | `de7206e7e06d-ebv-v2` | unchanged | Paired cost-accounting controls validated; 9.67-point corpus effect is an unattained upper bound (10 - 0.5·2/30·10); per-problem evaluator checks on all six problems were not run. |
| [Exchange Core Throughput](repairs/exchange_core_throughput-v2/README.md) | grader | `2cbf65650b3c-ebv-v2` | unchanged | Integration-test gate validated: two one-edit bugs drop from ~2250 to 0, good-faith engines keep scoring within throughput noise; at the leaderboard setting (--cpus 4 --memory 8g, 3 jobs) v2 passes the gate with 33 tests; package rebuilt from scratch on a clean machine (materialize-check-g1). The post-average Maven failure path is tested only on a constructed arm. |
| [FFmpeg swscale Reimplementation](repairs/ffmpeg_swscale_reimplementation-v2/README.md) | grader | `d3c0aa3fa987-ebv-v2.2` | unchanged | Current v2.2 judge image built, and rebuilt from scratch on a clean machine (materialize-check-final); three paired native full-scorer controls passed, including valid output and exact-zero rejection. Full source-build eval_cmd and whole-task certification remain unverified. |
| [Git Rewrite in Zig](repairs/git_rewrite_in_zig-v2/README.md) | grader | `0d404251e9c9-ebv-v2` | unchanged | Paired native runs (3 repeats, each exit=0): five good-faith trees go from 0 to the starter score and the real-git oracle is unchanged; package rebuilt from scratch on a clean machine (materialize-check-g1). No real Zig port graded; v2 tested at 8 CPUs only. |
| [Graph Node Classification](repairs/graph_node_classification-v2/README.md) | grader | `f2ddd52992ae-ebv-v2.1` | unchanged | v2.1 validated by three paired runs of the original, the first fixed (v2) and v2.1 verifiers on seven submissions, each split over two workers (graph_node_classification-v2-paired-v21a, -v21b and their -rep2, -rep3; each ledger exit=0; package materialized with its own materialize.sh in each). Final scores of good-faith submissions differ by up to 2.9e-4 (timing). The Lean proof covers the first fix, not v2.1's str() key handling or duplicate-key rejection. |
| [Grid Turing Robot](repairs/grid_turing_robot-v2/README.md) | grader | `3c6f50ac4fe0-ebv-v2` | unchanged | CPU-share controls validated: three identical paired native runs at 4 CPUs plus 8-CPU controls (each ledger exit=0); package rebuilt from scratch on a clean machine (materialize-check-g1). Not tested in a Kubernetes pod, at 3 or 5-7 CPUs, or with multi-threaded solvers. |
| [Integer Compression Codec](repairs/integer_compression_codec-v2/README.md) | grader, score scale | `27063396e02a-ebv-v2` | unchanged | Three side-by-side native runs (all finished): starter 0.23 -> about 1.0 raw as documented, correct codec 0.83-0.97 -> 6.70-8.27, corrupting codec 0 in both; the scale's end points are exact; package rebuilt from scratch on a clean machine (materialize-check-g3). Timing noise about ±15% per dataset; other machine types and the Kubernetes grader not tested. |
| [Jagua Nesting Optimization](repairs/jagua_nesting_optimization-v2/README.md) | grader | `bba393b2dd53-ebv-v2.1` | unchanged | v2.1 validated by three identical paired runs of the original, v2 and v2.1 graders (each exit=0): overlap witnesses rejected, legal contact and f32-derived angles accepted, a +0.01 degree rotation rejected on all 15 instances with allowed orientations. The v2.1 package as committed was rebuilt from scratch on a clean machine (materialize-check-final). |
| [Juliet Vulnerability Analyzer](repairs/juliet_vulnerability_analyzer-v2/README.md) | grader | `0c4f2c0057c2-ebv-v2` | unchanged | Hidden-grading paired runs (3 identical runs) validated: public-form CWE-78 answers gain credit, hidden-form and wrong-source answers unchanged; package rebuilt from scratch on a clean machine (materialize-check-g1, again at the final commit in materialize-check-final). The +26.473 maximum is computed exactly from the grader's formula, not run. |
| [Lean Analysis Proofs](repairs/lean_analysis_proofs-v2/README.md) | grader, agent's starting files | `lean_analysis_proofs-v2-judge` | `lean_analysis_proofs-v2-work` | Component controls validated; actual eval_cmd dependency path and final grader/work images unverified: the rebuild needs about 45 GB of disk, more than the 21 GB workers used (materialize-check-lean). |
| [Molecular Self Assembly](repairs/molecular_self_assembly-v2/README.md) | grader | `96df6463f5e6-ebv-v2` | unchanged | CPU-share controls validated: three identical paired native runs at 4 CPUs plus 8-CPU controls (each ledger exit=0); package rebuilt from scratch on a clean machine (materialize-check-g2). The effect on strong solutions is derived, not measured; not tested in a Kubernetes pod or with multi-threaded solvers. |
| [OpenRCT2 Theme Park AI](repairs/openrct2_theme_park_ai-v2/README.md) | task instructions | `80316ccd77ae` | unchanged | Prompt-only correction: the measured horizon (about 70 game days in 120 s at speed 4) is reproduced from saved logs and the arithmetic is in Lean; package rebuilt from scratch on a clean machine (materialize-check-g3). The full wrapper, the Kubernetes grader and a competitive plugin were not run; lowering the game speed can still freeze value. |
| [OpenTTD Transport AI](repairs/openttd_transport_ai-v2/README.md) | agent's starting files, task instructions | `d8e83be4044e` | `f2e9a9fb0fff-ebv-v2` | Prompt and starter correction: three native runs (each exit=0) show the v1 starter dying on 5/5 seeds and the v2 starter and probe running without error; v2 work image rebuilt from scratch on a clean machine (materialize-check-g3). No score above the 1e5 anchor; the shipped API pages describe a newer OpenTTD and the documented docs path is wrong (documented limitation). |
| [Order Addition Permutation Optimization](repairs/order_addition_permutation_optimization-v2/README.md) | grader | `f6f385925889-ebv-v2` | unchanged | Paired runs (3, each exit=0): valid submissions pass 5/5 and the better later submission is selected, invalid controls rejected; a real archived run regraded through materialize.sh; package rebuilt from scratch on a clean machine (materialize-check-g2). Selection computed offline with select_best, not through a live judge_server. |
| [PFR Formalization](repairs/pfr_formalization-v2/README.md) | grader, agent's starting files | `pfr_formalization-v2-judge` | `pfr_formalization-v2-work` | Type-contamination mechanism validated on analogous lemmas; work image built once in the clean-machine rebuild (materialize-check-pfr, which ran a hand-edited copy of materialize.sh; the reordered committed materialize.sh has not been run), no solver run in it; actual five-target credit recovery unverified, because it needs real proofs of those theorems. |
| [Portfolio Risk Calibration](repairs/portfolio_risk_calibration-v2/README.md) | grader | `08fe0a4bad80-ebv-v2` | unchanged | Paired formula controls validated; 0.3921 is a restricted numerical sensitivity envelope, not a universal score bound. |
| [Rust Multicrate Reconstruction](repairs/rust_multicrate_reconstruction-v2/README.md) | grader, agent's starting files | `b749374fe7bc-ebv-v2` | `7f639fc9d090-ebv-v2` | Three paired runs of the verbatim eval_cmd (each exit=0) reproduce every published score; TLA+ covers the exemption; v2 judge and work images rebuilt from scratch on a clean machine (materialize-check-rust). No solver build run in the v2 work image; the v2 starter arm ran once. |
| [Schemathesis Config Modernization](repairs/schemathesis_config_modernization-v2/README.md) | grader | `function-identity-v2` | unchanged | Three paired runs (each exit=0): identity arm unchanged, wrapper arm -1/160, no-register arm as documented; package rebuilt from scratch on a clean machine (materialize-check-g2). The top-level schemathesis.metric re-export is still checked only for callability; no complete solution graded. |
| [Schemathesis Datagen Pipeline](repairs/schemathesis_datagen_pipeline-v2/README.md) | grader | `http-date-v2.1` | unchanged | v2.1 judge image materialized and built in the worker from the package; clean native rerun schemathesis_datagen_pipeline-v2.1-native-20261013b (ledger exit=0): six arms of the original eval_cmd, stdlib_1900 0.477350/0.477350, stdlib_any_year 0.477350/0.467094, garbage_shape 0.477350/0.467094. Whole-task certification and a new formal proof are not established. |
| [Schemathesis Reporting Observability](repairs/schemathesis_reporting_observability-v2/README.md) | grader | `junit-coverage-v2.1` | unchanged | Six paired runs (each exit=0, identical summaries): the complete reference stays 1.0, an other-suite writer rises 0.985714 -> 1.0, wrong reports lose points; package rebuilt from scratch on a clean machine (materialize-check-g2). One complete implementation tried; a namespaced JUnit root fails the revised test. |
| [SMT Solver](repairs/smt_solver-v2/README.md) | grader | `fdce54253c61-ebv-v2` | unchanged | Paired corpus controls validated; formal soundness covers only the modeled QF_UF fragment, with argued implementation correspondence. |
| [Treant Forest](repairs/treant_forest-v2/README.md) | score scale | `d47dc1a7da74` | unchanged | Anchor-only repair: raw scores identical under both versions in paired runs, greedy policy 3.04 -> 16.36 normalized, invalid control 0 in both; package rebuilt from scratch on a clean machine (materialize-check-g3). The 92,304 cap is a documented bound, not shown attainable. |
| [Tree Block Partitioning](repairs/tree_block_partitioning-v2/README.md) | grader | `f74f0ef897ce-ebv-v2` | unchanged | Three paired runs (each exit=0): reference 100 -> 100, aliasing variant 0.25 -> 5, logic-error control unchanged; exhaustive aliased-state probe and TLA+ agree; package rebuilt from scratch on a clean machine (materialize-check-g2). How often real solvers write v*=v is unknown. |
| [Triangulation Coloring Optimization](repairs/triangulation_coloring_optimization-v2/README.md) | grader, agent's starting files | `convex-flip-v2.2` | `convex-flip-v2.2` | Convexity, CPU and convex-hull coverage validated: all 13 v2.2 inputs cover their hull exactly (exact census); three identical paired runs of the original, v2.1 and v2.2 graders. |
| [Vibrating Path Graph Coloring](repairs/vibrating_path_graph_coloring-v2/README.md) | grader, judge.eval_timeout | `eb22343ce84e-ebv-v2` | unchanged | CPU controls validated; zero-hit formatting effect ruled out on 37 of 50 cases only, unresolved on the other 13. |
| [Warehouse Forklift Routing](repairs/warehouse_forklift_routing-v2/README.md) | grader, [host final-drain overlay](repairs/harness-final-drain-v1/README.md) | `d342863c29cc-ebv-v2.1` | unchanged | Grader time/CPU controls validated; requires harness wait overlay, whose end-to-end integration remains pending. |

For each task, the tag with the highest suffix (`v2.1` or `v2.2`) replaces every earlier one (`v2`,
and `v2.1` where a `v2.2` exists). The earlier tags' grader or work images differ from the current
fix, so rebuild any image built from an earlier package. Where the fix changes the agent's
environment, the work image column gives its tag; "unchanged" means the fix uses the original work
image and tag.

Tasks kept with a note need no change. Their notes are in [FINDINGS.md](FINDINGS.md) and on the
case pages.
