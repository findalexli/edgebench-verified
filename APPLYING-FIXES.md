# Applying the fixes

Every repair is a new version of an EdgeBench task, packaged in EdgeBench's own format. The
original task definitions in `tasks/` and the original images are never modified. Each package in
`repairs/<task_id>-v2/` contains:

| File | Purpose |
| --- | --- |
| `README.md` | The defect, the exact change, score compatibility and limits |
| `repair.patch` | Our change, as a unified diff against the files in the original image |
| `materialize.sh` | Pulls the pinned original image, extracts the original files, applies the patch, and checks every result against `source-lock.json` |
| `Dockerfile` (and `Dockerfile.work` where the solver image changes) | `FROM` the original image digest, then only the changed files |
| `task.json.in` | The task definition for v2: a copy of `tasks/<task_id>.json` with only the necessary fields changed |
| `paired/` | The paired evaluation: the same inputs scored by the original and the repaired evaluator |

## Apply one repair

```bash
cd repairs/<task_id>-v2
./materialize.sh                     # regenerate the changed files from the public image
TAG=$(python3 -c "import json;print(json.load(open('task.json.in'))['judge']['image_tag'])")
docker build -t edgebench.judge.<task_id>:$TAG .
# if the package has Dockerfile.work, also build edgebench.work.<task_id>:<work image_tag> from it
cp task.json.in ../../tasks/<task_id>.json   # the harness resolves edgebench.judge.<task_id>:<image_tag>
```

The harness looks up images as `edgebench.judge.<task_id>:<image_tag>` and
`edgebench.work.<task_id>:<image_tag>`, taking the tags from the task JSON, so no harness change
is needed. Maintainers who build images from source can apply `repair.patch` to their source tree
instead; the patch paths are the in-image paths.

## Check a repair

`paired/run.sh` reruns the paired evaluation (it was run on 8-vCPU / 8 GiB workers). Two packages
differ: Lean Analysis uses `paired/run_local.sh`, run locally, and OpenRCT2 has no run script because
nothing executable changed (its controls hold by construction and were not re-run). The
accepted results are in `paired/results.md` and in [paired-results.csv](paired-results.csv):
each repair fixes its trigger, keeps valid controls' scores (or explains the change), and still
rejects invalid controls.

## Score compatibility

v2 scores are **not comparable** with v1 leaderboard scores for the same task. Rerun affected
submissions under v2 rather than mixing versions. Each package README states exactly which
submissions' scores change.

## What each repair changes

| Package | Changes | v2 judge image tag | Status |
| --- | --- | --- | --- |
| [arc_compiler_runtime](repairs/arc_compiler_runtime-v2/README.md) | solver (work) image | `200e176a8e30` | accepted |
| [borden_source_inversion](repairs/borden_source_inversion-v2/README.md) | solver (work) image, task prompt, score scale | `cc54d4fd7006` | accepted |
| [college_english_exam_bank](repairs/college_english_exam_bank-v2/README.md) | judge image | `6628b6d3f834-ebv-v2` | accepted |
| [cta_risk_budget_optimization](repairs/cta_risk_budget_optimization-v2/README.md) | judge image | `a9651058ecef-ebv-v2` | accepted |
| [dabic_gravity_inversion](repairs/dabic_gravity_inversion-v2/README.md) | judge image | `517eb738b87b-ebv-v2` | partial (task excluded) |
| [equivalence_class_divide_and_conquer](repairs/equivalence_class_divide_and_conquer-v2/README.md) | judge image | `de7206e7e06d-ebv-v2` | accepted |
| [exchange_core_throughput](repairs/exchange_core_throughput-v2/README.md) | judge image | `2cbf65650b3c-ebv-v2` | accepted |
| [ffmpeg_swscale_reimplementation](repairs/ffmpeg_swscale_reimplementation-v2/README.md) | judge image | `d3c0aa3fa987-ebv-v2` | accepted |
| [graph_node_classification](repairs/graph_node_classification-v2/README.md) | judge image | `f2ddd52992ae-ebv-v2` | accepted |
| [integer_compression_codec](repairs/integer_compression_codec-v2/README.md) | judge image | `27063396e02a-ebv-v2` | accepted |
| [jagua_nesting_optimization](repairs/jagua_nesting_optimization-v2/README.md) | judge image | `bba393b2dd53-ebv-v2` | accepted |
| [lean_analysis_proofs](repairs/lean_analysis_proofs-v2/README.md) | judge image, solver (work) image | `lean_analysis_proofs-v2-judge` | accepted |
| [openrct2_theme_park_ai](repairs/openrct2_theme_park_ai-v2/README.md) | task prompt | `80316ccd77ae` | accepted |
| [openttd_transport_ai](repairs/openttd_transport_ai-v2/README.md) | solver (work) image, task prompt | `d8e83be4044e` | accepted |
| [order_addition_permutation_optimization](repairs/order_addition_permutation_optimization-v2/README.md) | judge image | `f6f385925889-ebv-v2` | accepted |
| [schemathesis_config_modernization](repairs/schemathesis_config_modernization-v2/README.md) | judge image | `function-identity-v2` | accepted |
| [schemathesis_datagen_pipeline](repairs/schemathesis_datagen_pipeline-v2/README.md) | judge image | `http-date-v2` | accepted |
| [schemathesis_reporting_observability](repairs/schemathesis_reporting_observability-v2/README.md) | judge image | `junit-coverage-v2` | accepted |
| [smt_solver](repairs/smt_solver-v2/README.md) | judge image | `fdce54253c61-ebv-v2` | accepted |
| [treant_forest](repairs/treant_forest-v2/README.md) | score scale | `d47dc1a7da74` | accepted |
| [tree_block_partitioning](repairs/tree_block_partitioning-v2/README.md) | judge image | `f74f0ef897ce-ebv-v2` | accepted |
| [triangulation_coloring_optimization](repairs/triangulation_coloring_optimization-v2/README.md) | judge image, solver (work) image | `convex-flip-v2` | accepted |
| [warehouse_forklift_routing](repairs/warehouse_forklift_routing-v2/README.md) | judge image | `d342863c29cc-ebv-v2` | accepted |

Tasks retained with a note need no change; their notes are in [FINDINGS.md](FINDINGS.md) and the
case pages.
