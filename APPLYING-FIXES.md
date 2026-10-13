# Applying the fixes

Each repair package defines a new version of an original EdgeBench task, in EdgeBench's own
format. Validation depth differs by package; the status table and package limits are authoritative. Nothing in the original release is modified: the original task definitions stay in `tasks/`,
and the original software images are used unchanged as the base of each fix.

## What a fix contains

Each fix lives in its own folder, `repairs/<task_id>-v2/` ("v2" marks the fixed version).

| File | What it is |
| --- | --- |
| `README.md` | What the fix changes, how it was tested, and its limits |
| `repair.patch` | The change itself, as a standard diff against the original files |
| `materialize.sh` | Rebuilds the changed files: downloads the original public image, extracts the original files, applies the patch, and checks every result against the fingerprints in `source-lock.json` |
| `Dockerfile` (and `Dockerfile.work` when the agent's starting files change) | Builds the fixed image on top of the exact original image, adding only the changed files |
| `task.json.in` | The fixed task definition: a copy of `tasks/<task_id>.json` with only the necessary fields changed |
| `paired/` | The side-by-side test: the same test submissions graded by the original and the fixed grader |

Only the patch is distributed, never copies of the original files, so the fixes can be published
without redistributing EdgeBench's images.

## Build and use one fix

```bash
cd repairs/<task_id>-v2
./materialize.sh                     # regenerate the changed files from the public image
TAG=$(python3 -c "import json;print(json.load(open('task.json.in'))['judge']['image_tag'])")
docker build -t edgebench.judge.<task_id>:$TAG .
# if the package has Dockerfile.work, also build edgebench.work.<task_id>:<work image_tag> from it
cp task.json.in <your EdgeBench checkout>/tasks/<task_id>.json   # not this repository's tasks/, which is locked to the original
```

EdgeBench's runner finds images by the names `edgebench.judge.<task_id>:<image_tag>` (the grader)
and `edgebench.work.<task_id>:<image_tag>` (the agent's environment), reading the tags from the task
definition. Warehouse also requires the host-side final-drain overlay described below; replacing
its task definition and grader image alone leaves the 900-second final-result collection defect.
Maintainers who build images from source can apply `repair.patch` to their source tree instead.
The paths in the patch are the paths inside the image.

## Warehouse host-side integration

The [final-drain overlay](repairs/harness-final-drain-v1/README.md) is separate from the Warehouse
judge-image patch. It polls until recorded jobs are terminal, allows a queue-aware bounded wait,
and reports failure rather than returning an incomplete final score. Materialize it into a new
source directory and run the harness from that directory; this repository's locked `sforge/` mirror
stays unchanged. Its paired deterministic tests exercise the real patched drain and result assembly,
including a long evaluation and serial queue. Full Docker/Kubernetes integration remains unverified.

## Test a fix yourself

`paired/run.sh` reruns the side-by-side test. Most published runs used E2B cloud sandboxes with 8
virtual CPUs and 8 GiB of memory, with the grader limited to the CPU count each case page states
(1 to 8). These fixes differ:
- Lean Analysis uses `paired/run_local.sh`, which was run on a local host with 16 CPUs and 15 GB.
- OpenRCT2 has no run script, because only its instructions changed and nothing that runs was
  modified.
- Git in Zig uses `paired/run_gates.sh` and `paired/run_oracle.sh`.
- PFR Formalization uses `paired/build_v2.sh` and `paired/grade_variants.sh`.
- Rust Multicrate uses the templates `paired/run-paired.sh.in` and `paired/run-failfast.sh.in`.
- Triangulation and Warehouse Routing also have `paired/run-cpu4.sh` for the 4-CPU tests.
- The separate host overlay uses `python3 repairs/harness-final-drain-v1/test_drain.py` from the repository root (deterministic component tests, no cloud calls).

The results are in each `paired/results.md` and together in [data/paired-results.csv](data/paired-results.csv).
These are the acceptance criteria; the table distinguishes demonstrated controls from incomplete
release validation, component tests, and documentation-only changes:
- the test submission that shows the problem is now graded correctly;
- correct test submissions keep their scores, or the change is explained;
- wrong test submissions are still rejected.

## Scores are not comparable across versions

A score from a fixed version cannot be compared with a score from the original task or the original
leaderboard. Regrade submissions with the fixed version rather than mixing the two. Each fix's
README says exactly which submissions' scores change.

## What each fix changes

| Task | What changes | Fixed grader image tag | Fixed work image tag | Status |
| --- | --- | --- | --- | --- |
| [Apple Incremental Game](repairs/apple_incremental_game-v2/README.md) | grader | `16968d8ec7f2-ebv-v2` | unchanged | see package evidence and limits |
| [Arc Compiler Runtime](repairs/arc_compiler_runtime-v2/README.md) | agent's starting files | `200e176a8e30` | `v2-analyze-contract-docs` | see package evidence and limits |
| [Borden Source Inversion](repairs/borden_source_inversion-v2/README.md) | agent's starting files, task instructions, score scale | `cc54d4fd7006` | `f389fcf94240-ebv-v2.1` | see package evidence and limits |
| [College English Exam Bank](repairs/college_english_exam_bank-v2/README.md) | grader | `6628b6d3f834-ebv-v2.1` | unchanged | see package evidence and limits |
| [CTA Risk Budget Optimization](repairs/cta_risk_budget_optimization-v2/README.md) | grader | `a9651058ecef-ebv-v2.1` | unchanged | Current v2.1 currency/NAV predicate passes paired original-helper controls; full native grading and final-score integration pending. |
| [D-ABIC Gravity Inversion](repairs/dabic_gravity_inversion-v2/README.md) | grader | `517eb738b87b-ebv-v2` | unchanged | partial fix; task removed; see package evidence and limits |
| [Equivalence Class Divide and Conquer](repairs/equivalence_class_divide_and_conquer-v2/README.md) | grader | `de7206e7e06d-ebv-v2` | unchanged | Paired cost-accounting controls validated; 9.67-point corpus effect is an unattained upper bound. |
| [Exchange Core Throughput](repairs/exchange_core_throughput-v2/README.md) | grader | `2cbf65650b3c-ebv-v2` | unchanged | see package evidence and limits |
| [FFmpeg swscale Reimplementation](repairs/ffmpeg_swscale_reimplementation-v2/README.md) | grader | `d3c0aa3fa987-ebv-v2.2` | unchanged | Current v2.2 judge image built; three paired native full-scorer controls passed, including valid output and exact-zero rejection. Full source-build eval_cmd and whole-task certification remain unverified. |
| [Git Rewrite in Zig](repairs/git_rewrite_in_zig-v2/README.md) | grader | `0d404251e9c9-ebv-v2` | unchanged | see package evidence and limits |
| [Graph Node Classification](repairs/graph_node_classification-v2/README.md) | grader | `f2ddd52992ae-ebv-v2` | unchanged | see package evidence and limits |
| [Grid Turing Robot](repairs/grid_turing_robot-v2/README.md) | grader | `3c6f50ac4fe0-ebv-v2` | unchanged | see package evidence and limits |
| [Integer Compression Codec](repairs/integer_compression_codec-v2/README.md) | grader, score scale | `27063396e02a-ebv-v2` | unchanged | see package evidence and limits |
| [Jagua Nesting Optimization](repairs/jagua_nesting_optimization-v2/README.md) | grader | `bba393b2dd53-ebv-v2` | unchanged | see package evidence and limits |
| [Juliet Vulnerability Analyzer](repairs/juliet_vulnerability_analyzer-v2/README.md) | grader | `0c4f2c0057c2-ebv-v2` | unchanged | see package evidence and limits |
| [Lean Analysis Proofs](repairs/lean_analysis_proofs-v2/README.md) | grader, agent's starting files | `lean_analysis_proofs-v2-judge` | `lean_analysis_proofs-v2-work` | Component controls validated; actual eval_cmd dependency path and final grader/work images unverified. |
| [Molecular Self Assembly](repairs/molecular_self_assembly-v2/README.md) | grader | `96df6463f5e6-ebv-v2` | unchanged | see package evidence and limits |
| [OpenRCT2 Theme Park AI](repairs/openrct2_theme_park_ai-v2/README.md) | task instructions | `80316ccd77ae` | unchanged | see package evidence and limits |
| [OpenTTD Transport AI](repairs/openttd_transport_ai-v2/README.md) | agent's starting files, task instructions | `d8e83be4044e` | `f2e9a9fb0fff-ebv-v2` | see package evidence and limits |
| [Order Addition Permutation Optimization](repairs/order_addition_permutation_optimization-v2/README.md) | grader | `f6f385925889-ebv-v2` | unchanged | see package evidence and limits |
| [PFR Formalization](repairs/pfr_formalization-v2/README.md) | grader, agent's starting files | `pfr_formalization-v2-judge` | `pfr_formalization-v2-work` | Type-contamination mechanism validated on analogous lemmas; actual five-target credit recovery and work-image build unverified. |
| [Portfolio Risk Calibration](repairs/portfolio_risk_calibration-v2/README.md) | grader | `08fe0a4bad80-ebv-v2` | unchanged | Paired formula controls validated; 0.3921 is a restricted numerical sensitivity envelope, not a universal score bound. |
| [Rust Multicrate Reconstruction](repairs/rust_multicrate_reconstruction-v2/README.md) | grader, agent's starting files | `b749374fe7bc-ebv-v2` | `7f639fc9d090-ebv-v2` | see package evidence and limits |
| [Schemathesis Config Modernization](repairs/schemathesis_config_modernization-v2/README.md) | grader | `function-identity-v2` | unchanged | see package evidence and limits |
| [Schemathesis Datagen Pipeline](repairs/schemathesis_datagen_pipeline-v2/README.md) | grader | `http-date-v2.1` | unchanged | v2.1 judge image materialized and built in the worker from the package; clean native rerun schemathesis_datagen_pipeline-v2.1-native-20261013b (ledger exit=0): six arms of the original eval_cmd, stdlib_1900 0.477350/0.477350, stdlib_any_year 0.477350/0.467094, garbage_shape 0.477350/0.467094. Whole-task certification and a new formal proof are not established. |
| [Schemathesis Reporting Observability](repairs/schemathesis_reporting_observability-v2/README.md) | grader | `junit-coverage-v2.1` | unchanged | see package evidence and limits |
| [SMT Solver](repairs/smt_solver-v2/README.md) | grader | `fdce54253c61-ebv-v2` | unchanged | Paired corpus controls validated; formal soundness covers only the modeled QF_UF fragment, with argued implementation correspondence. |
| [Treant Forest](repairs/treant_forest-v2/README.md) | score scale | `d47dc1a7da74` | unchanged | see package evidence and limits |
| [Tree Block Partitioning](repairs/tree_block_partitioning-v2/README.md) | grader | `f74f0ef897ce-ebv-v2` | unchanged | see package evidence and limits |
| [Triangulation Coloring Optimization](repairs/triangulation_coloring_optimization-v2/README.md) | grader, agent's starting files | `convex-flip-v2.1` | `convex-flip-v2` | Convexity and CPU controls validated; regenerated meshes still leave convex-hull gaps in 12 of 13 files. |
| [Vibrating Path Graph Coloring](repairs/vibrating_path_graph_coloring-v2/README.md) | grader, judge.eval_timeout | `eb22343ce84e-ebv-v2` | unchanged | CPU controls validated; zero-hit formatting effect ruled out on 37 of 50 cases only, unresolved on the other 13. |
| [Warehouse Forklift Routing](repairs/warehouse_forklift_routing-v2/README.md) | grader, [host final-drain overlay](repairs/harness-final-drain-v1/README.md) | `d342863c29cc-ebv-v2.1` | unchanged | Grader time/CPU controls validated; requires harness wait overlay, whose end-to-end integration remains pending. |

A tag ending in `v2.1` replaces the tag ending in `v2` of the v1.0 package, whose grader or work
image differs from the current fix; an image built from the v1.0 package must be rebuilt. The work
image column shows the tag of the agent's environment where the fix changes it; "unchanged" means the
original work image and tag are used.

Tasks kept with a note need no change. Their notes are in [FINDINGS.md](FINDINGS.md) and on the
case pages.
