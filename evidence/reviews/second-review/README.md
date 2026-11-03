# Second review: what is here and what reproduces

| Path | Contents |
| --- | --- |
| `container/` | One verdict file per task: arms, n, effect and the weakest point |
| `tables/` | The saved output of each table script, run on the full results. Numbers in `data/review.json` trace to these and to the verdict files |
| `astra/` | The independent reviewer's passes and claims |
| `human/` | Verification recorded by volunteers |
| `pr-evidence/` | Evidence behind our upstream reports |

The jobs are in `evidence/runs/community9-*` and `evidence/runs/community8-arc_shape`: how each arm was built and run (`run.sh`, `arms.sh`, patches), per-arm grades, and judge output. The table scripts are in `evidence/scripts/second_review/`. Run them from the repository root.

## Not in this repository

- Real agent submissions and the archives built from them (`subs/`, `submission.tar.gz`), because they are agent code.
- Build logs, machine environment dumps, and files over 256 KB in job results.
- The working claim files in `.internal/`, which a few scripts read at the end to write a verdict. The reviewer's published claims are in `astra/claims.json`.

So a job's arms cannot be rerun from this repository alone where they start from a real submission. The grades they produced are here.

## Which table scripts reproduce their saved output from this repository

**In full (12):** `arc_shape_table`, `c9_dcss_dungeon_ai_table`, `c9_exchange_core_throughput_table`, `c9_git_rewrite_in_zig_table`, `c9_juliet_vulnerability_analyzer_table`, `c9_nethack_dungeon_agent_table`, `c9_openrct2_theme_park_ai_table`, `c9_rust_multicrate_reconstruction_table`, `c9_schemathesis_config_modernization_table`, `c9_schemathesis_datagen_pipeline_table`, `c9_schemathesis_reporting_observability_table`, `c9_wesnoth_tactical_ai_table`.

**In part (11):** `c9_apple_incremental_game_table`, `c9_dabic_gravity_inversion_table`, `c9_ffmpeg_swscale_reimplementation_table`, `c9_grid_turing_robot_table`, `c9_integer_compression_codec_table`, `c9_molecular_self_assembly_table`, `c9_ordinal_notation_well_foundedness_table`, `c9_smt_solver_table`, `c9_treant_forest_table`, `c9_triangulation_coloring_optimization_table`, `c9_warehouse_forklift_routing_table`. These also read real-run reports or submissions, an environment dump or `.internal/`, so they print less or stop early. Their full output is in `tables/`.
