# Applying the fixes

Each fixed task is published as a new version of the original EdgeBench task, in EdgeBench's own
format. Nothing in the original release is modified: the original task definitions stay in `tasks/`,
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
cp task.json.in ../../tasks/<task_id>.json   # the harness resolves edgebench.judge.<task_id>:<image_tag>
```

EdgeBench's runner finds images by the names `edgebench.judge.<task_id>:<image_tag>` (the grader)
and `edgebench.work.<task_id>:<image_tag>` (the agent's environment), reading the tags from the task
definition. Replacing the task definition is therefore enough; the runner itself does not change.
Maintainers who build images from source can apply `repair.patch` to their source tree instead.
The paths in the patch are the paths inside the image.

## Test a fix yourself

`paired/run.sh` reruns the side-by-side test. The published runs used machines with 8 virtual CPUs
and 8 GiB of memory. Two fixes differ:
- Lean Analysis uses `paired/run_local.sh`, which was run locally.
- OpenRCT2 has no run script, because only its instructions changed and nothing that runs was
  modified.

The results are in each `paired/results.md` and together in [data/paired-results.csv](data/paired-results.csv).
Every fix was accepted only if three things held:
- the test submission that shows the problem is now graded correctly;
- correct test submissions keep their scores, or the change is explained;
- wrong test submissions are still rejected.

## Scores are not comparable across versions

A score from a fixed version cannot be compared with a score from the original task or the original
leaderboard. Regrade submissions with the fixed version rather than mixing the two. Each fix's
README says exactly which submissions' scores change.

## What each fix changes

| Task | What changes | Fixed grader image tag | Status |
| --- | --- | --- | --- |
| [Arc Compiler Runtime](repairs/arc_compiler_runtime-v2/README.md) | agent's starting files | `200e176a8e30` | fixed and tested |
| [Borden Source Inversion](repairs/borden_source_inversion-v2/README.md) | agent's starting files, task instructions, score scale | `cc54d4fd7006` | fixed and tested |
| [College English Exam Bank](repairs/college_english_exam_bank-v2/README.md) | grader | `6628b6d3f834-ebv-v2` | fixed and tested |
| [Cta Risk Budget Optimization](repairs/cta_risk_budget_optimization-v2/README.md) | grader | `a9651058ecef-ebv-v2` | fixed and tested |
| [Dabic Gravity Inversion](repairs/dabic_gravity_inversion-v2/README.md) | grader | `517eb738b87b-ebv-v2` | partial fix; task removed |
| [Equivalence Class Divide And Conquer](repairs/equivalence_class_divide_and_conquer-v2/README.md) | grader | `de7206e7e06d-ebv-v2` | fixed and tested |
| [Exchange Core Throughput](repairs/exchange_core_throughput-v2/README.md) | grader | `2cbf65650b3c-ebv-v2` | fixed and tested |
| [Ffmpeg Swscale Reimplementation](repairs/ffmpeg_swscale_reimplementation-v2/README.md) | grader | `d3c0aa3fa987-ebv-v2` | fixed and tested |
| [Graph Node Classification](repairs/graph_node_classification-v2/README.md) | grader | `f2ddd52992ae-ebv-v2` | fixed and tested |
| [Integer Compression Codec](repairs/integer_compression_codec-v2/README.md) | grader | `27063396e02a-ebv-v2` | fixed and tested |
| [Jagua Nesting Optimization](repairs/jagua_nesting_optimization-v2/README.md) | grader | `bba393b2dd53-ebv-v2` | fixed and tested |
| [Lean Analysis Proofs](repairs/lean_analysis_proofs-v2/README.md) | grader, agent's starting files | `lean_analysis_proofs-v2-judge` | fixed and tested |
| [Openrct2 Theme Park Ai](repairs/openrct2_theme_park_ai-v2/README.md) | task instructions | `80316ccd77ae` | fixed and tested |
| [Openttd Transport Ai](repairs/openttd_transport_ai-v2/README.md) | agent's starting files, task instructions | `d8e83be4044e` | fixed and tested |
| [Order Addition Permutation Optimization](repairs/order_addition_permutation_optimization-v2/README.md) | grader | `f6f385925889-ebv-v2` | fixed and tested |
| [Schemathesis Config Modernization](repairs/schemathesis_config_modernization-v2/README.md) | grader | `function-identity-v2` | fixed and tested |
| [Schemathesis Datagen Pipeline](repairs/schemathesis_datagen_pipeline-v2/README.md) | grader | `http-date-v2` | fixed and tested |
| [Schemathesis Reporting Observability](repairs/schemathesis_reporting_observability-v2/README.md) | grader | `junit-coverage-v2` | fixed and tested |
| [Smt Solver](repairs/smt_solver-v2/README.md) | grader | `fdce54253c61-ebv-v2` | fixed and tested |
| [Treant Forest](repairs/treant_forest-v2/README.md) | score scale | `d47dc1a7da74` | fixed and tested |
| [Tree Block Partitioning](repairs/tree_block_partitioning-v2/README.md) | grader | `f74f0ef897ce-ebv-v2` | fixed and tested |
| [Triangulation Coloring Optimization](repairs/triangulation_coloring_optimization-v2/README.md) | grader, agent's starting files | `convex-flip-v2` | fixed and tested |
| [Warehouse Forklift Routing](repairs/warehouse_forklift_routing-v2/README.md) | grader | `d342863c29cc-ebv-v2` | fixed and tested |

Tasks kept with a note need no change. Their notes are in [FINDINGS.md](FINDINGS.md) and on the
case pages.
