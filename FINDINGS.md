# Findings

12 of the 51 public EdgeBench tasks have a measured score change on the current judge, large enough to matter. Effects are out of 100 unless stated otherwise. How the review worked is in [METHOD.md](METHOD.md); the data is in [data/review.json](data/review.json).

A task is confirmed when the measured change reaches real work: regrading a real submission shows it, or a repeatability failure affects any submission. A defect that is large only on a trigger no real submission we hold uses stays with the others. Graph Node, for example, drops from 90.52-90.57 to 1.95-2.01 if predictions use integer keys, which the task permits.

| Task | What goes wrong | Measured effect | Upstream |
| --- | --- | --- | --- |
| [Apple Incremental Game](cases/apple_incremental_game.md) | The same eight-at-once pool costs real files points at 4 CPUs and many cases under load. | At true 4 CPUs a real file scores 68.10-70.60, against 73.25-73.92 with a smaller pool, with no timeouts (n=5). In an overload test, five judges sharing 8 CPUs, it scored 3.09-19.78 with the original pool and 17.81-68.87 with the smaller one across three workers (n=20 each). The smaller pool also lost cases on the noisiest worker. | Same mechanism as PR #36; not reported separately. |
| [Arc Compiler Runtime](cases/arc_compiler_runtime.md) | Hidden tests expect an `analyze()` return shape that nothing the agent sees describes. | A real Opus submission scores 61.31 as submitted and 94.81 with only the return shape changed (n=2 each). One real run each: best 61.31 on the original task, 96.06 with the shape documented. | Not yet reported. |
| [Integer Compression Codec](cases/integer_compression_codec.md) | A stored baseline figure is impossible for the documented starter, which distorts how the datasets are weighted. | The starter gets 0.25 raw against the documented 1.0, and 0.855 with the exact figures. A real submission scores 73.60 today; with the figures corrected its raw score is 164.4, which clips to 100 on the existing scale, or gives 51.22 on a new 1..320 scale. So the size of the fix depends on the scale. No ranking change was shown, and real runs reach 73.78 today. | Not yet reported. Choosing a fix means choosing a new scale, which is the maintainers' call. |
| [Juliet Vulnerability Analyzer](cases/juliet_vulnerability_analyzer.md) | Any `.py` or `.sh` file containing the word `infer`, even in a comment, loses 100 points. Separately, CWE-416 findings that start at the release are rejected. | A real analyzer scores 0 and would score 79.59 with the fix; another goes from 90.70 to 0 with one added comment (n=6). CWE-416: a real analyzer loses 3.34, from 89.00 to 85.66 (n=3), though that solver turned the option off and its best score lost nothing. | Reported: issue #39 and PR #35 (the `infer` part). |
| [NetHack Dungeon Agent](cases/nethack_dungeon_agent.md) | Seeding silently fails, so the 20 graded games differ every time. | Our bot scores 6.8-15.5 over 12 gradings, and 14.5 on all 12 once seeding works, all on one day; NetHack also reads the clock, so repeatability across dates is untested. The bot is ours; there is no real submission to test. | Listed in upstream's known issues. |
| [OpenRCT2 Theme Park AI](cases/openrct2_theme_park_ai.md) | The instruction promises about four game years, but the 120 seconds per scenario fit 68 to 69 of 992 game days. | A real plugin scores 27.50 under the official budget (n=3). Direct evaluator runs continued to 992 days score 16.44 (n=2), so for this plugin the short run inflates the score. No judge fix was tested. Real files also vary between gradings, up to 11.40-44.73, but randomness in the plugins may cause that, so we don't count it against the judge. | The short run is listed in upstream's known issues; issue #12 raises a separate question about this task's scale. |
| [Rust Multicrate Reconstruction](cases/rust_multicrate_reconstruction.md) | Four source files are missing, which blocks nine scored crates. | At 8 vCPUs, restoring the files raises a real submission from 17.20 to 27.17 and a reference we rebuilt from upstream code from 27.61 to 73.99 (n=2). Original-judge scores matched 4-CPU results, but the restored arm wasn't run at 4 CPUs. Two crates still fail because of separate hidden-test defects. The starter also rises, from 1.47 to 3.82, so old scores don't carry over. | Listed in upstream's known issues. |
| [Schemathesis Datagen Pipeline](cases/schemathesis_datagen_pipeline.md) | The hidden header test imports names and expects format keys that `TODO.md` never gives, so every real `headers` module scores 0 of 15 on it. | Once those are supplied, a real submission goes from 72.31 to 85.64 or 86.67; the two values come from a flaky test. The 8 real modules are 2 distinct versions. | Not yet reported. |
| [SMT Solver](cases/smt_solver.md) | The validator's recursion crashes on 5 hard files when a solver answers `sat`; no score file gets written, and the judge still reports a valid 0. | A real solver scores 0.00 on the shipped judge and 47.04 and 46.17 with a larger validator stack. The 5 crashing answers still fail validation; preventing the crash restores credit earned on other cases. Measured at 8 CPUs and 7 GB, not the official 16 and 16 GB, with 6 to 7 solver OOM kills per run. No real run shows it. | Not yet reported. |
| [Treant Forest](cases/treant_forest.md) | The tester stops each game at an undocumented turn cap, so no submission can pass 21.02, while the 0-100 scale assumes totals the cap rules out. | All 87 archived real reports sit at 20.46-21.02, so the cap hides real differences between them. Removing the cap with the scale unchanged raises one real submission by 15.83 and reorders the ones we tested, though some long replays hit the tester's time limit. The four real submissions we measured read a destination list the README says solutions don't use; a grid-only control scores 3.04 with or without the cap. | Listed in upstream's known issues. Whether to change the cap, the scale or both is the maintainers' call. |
| [Vibrating Path Graph Coloring](cases/vibrating_path_graph_coloring.md) | Eight cases run at once on the official 4 CPUs, and one timeout makes the whole total `inf`. | A real Opus solver gets `inf` on all 15 gradings and 19.77-19.98 with 4 cases at once. The same file passed all 7 grades during its own run on the published judge image, so the grading is non-repeatable. | Reported: issue #40 and PR #36. |
| [Wesnoth Tactical AI](cases/wesnoth_tactical_ai.md) | The same file gets different scores despite fixed seeds. | Wesnoth's stock AI scores 36 to 43 over 8 gradings with no timeouts. We haven't found the cause, and there is no real submission to test. | Listed in upstream's known issues. |

<details>
<summary>The other 39 tasks, including first-audit claims we withdrew</summary>

Our first audit reported problems in 32 tasks. Of those 32, 10 are confirmed, 13 are real but small or unseen, 1 has changed upstream and 8 are not confirmed.

| Status | Tasks |
| --- | ---: |
| Confirmed | 12 |
| Real, small or unseen | 15 |
| Changed upstream | 1 |
| Not confirmed | 8 |
| No problem found | 15 |
| **Total** | **51** |

### Real, small or unseen

The defect exists, but it moves about a point or less, or it is large only when triggered and no real submission we hold triggers it.

| Task | Why it is here | First audit |
| --- | --- | --- |
| [D-ABIC Gravity Inversion](cases/dabic_gravity_inversion.md) | An undisclosed gate costs a model-space solver 1.08 points, but 0 of 75 real reports use that form. The self-reported points are a separate design question. | Removed |
| [DCSS Dungeon AI](cases/dcss_dungeon_ai.md) | Upstream's notes record one bot at raw 1556.0-5211.2 on the current judge, which computes to 32.82-54.61. Our own weaker bots spread by under 1 point, so we did not reproduce the large swing or isolate its cause. | Kept, with a note |
| [Exchange Core Throughput](cases/exchange_core_throughput.md) | Broken engines do earn credit, but at the official 4 CPUs correct work mostly scores 0 too, and no real run was affected. | Fixed |
| [FFmpeg swscale Reimplementation](cases/ffmpeg_swscale_reimplementation.md) | Making a conversion fail raises a score by 12.82, but no real run gained from it. | Fixed |
| [Git Rewrite in Zig](cases/git_rewrite_in_zig.md) | An ordinary object file or an unimported test calling system git takes a real implementation from 36.86 to 0, but none of the 46 distinct real archives has either. | Fixed |
| [Graph Node Classification](cases/graph_node_classification.md) | Changing a real solver's predictions to integer keys, which the task permits, takes it from 90.52-90.57 to 1.95-2.01. No real submission we hold uses them. | Fixed |
| [Grid Turing Robot](cases/grid_turing_robot.md) | A smaller pool is worth +0.67 to +0.71 on valid real files. No real file goes from invalid to valid. | Fixed |
| [Lean Analysis Proofs](cases/lean_analysis_proofs.md) | Two required statements are false, which is proved in Lean. The computed score effect is tiny, and the grader image is too large for us to rerun. | Fixed |
| [Molecular Self Assembly](cases/molecular_self_assembly.md) | A smaller pool gives deadline search more CPU, worth +1.13 to +1.46. The timeouts we first blamed on the pool occur on both pools. | Fixed |
| [Ordinal Notation Well-Foundedness](cases/ordinal_notation_well_foundedness.md) | A file-name filter can drop a needed proof helper (1.18 to 0). Only our own proof triggers it. We hold no real submission for this task, though upstream records historical runs. | Kept, with a note |
| [PFR Formalization](cases/pfr_formalization.md) | Five scored statements carry a hidden `sorry` in their type, so no submission can earn them: 5 of 423 targets, or 1.18 points. A volunteer Lean user checked this by hand and passed it: with the workaround, all five completed proofs receive credit (398/423 to 403/423). We did not rerun it on the current judge. | Fixed |
| [Schemathesis Config Modernization](cases/schemathesis_config_modernization.md) | A forwarding decorator gets 0.67 points too many. No real submission writes one. | Fixed |
| [Schemathesis Reporting Observability](cases/schemathesis_reporting_observability.md) | Two checks give 1.00 to 1.43 points too many, and a third takes 1.43 from a valid report without the word schemathesis. One unchanged real file is affected (2.0 instead of 1.0). | Fixed |
| [Triangulation Coloring Optimization](cases/triangulation_coloring_optimization.md) | A smaller pool is worth +0.32 to +0.59, with no timeouts in any condition. | Fixed |
| [Warehouse Forklift Routing](cases/warehouse_forklift_routing.md) | The judge allows 60 s per input. Five cases at 30 s each suggest 150 s, though another README passage calls whole inputs test cases. Edited solvers with long deadlines recover under a longer limit; real submissions we hold are unaffected, and the pool makes about no difference. | Fixed |

### Changed upstream

Real on the original release, no longer applies on the `community` branch.

| Task | Why it is here | First audit |
| --- | --- | --- |
| [Order Addition Permutation Optimization](cases/order_addition_permutation_optimization.md) | Real on the original release: a real run kept 3.79 instead of the 41.24 a later submission earned. `community` changed how a run picks its best, so this no longer applies there. | Fixed |

### Not confirmed

The first audit's claim did not hold up, or we could not settle it. It may still be a true statement about the code; we could not show it moves a good-faith solver's score on the current judge.

| Task | Why it is here | First audit |
| --- | --- | --- |
| [Borden Source Inversion](cases/borden_source_inversion.md) | The unstated model didn't stop one real run from reaching raw 108.97 of 109 through score feedback, while a run with the model documented reached 52.86. Single runs like these don't show what documenting it would change. | Fixed |
| [College English Exam Bank](cases/college_english_exam_bank.md) | The code gives full marks for omitted rules, but every example is a constructed grader reply, and no real submission hit it. | Fixed |
| [CTA Risk Budget Optimization](cases/cta_risk_budget_optimization.md) | The limit formula differs from the policy, but a real submission we checked scores 50.0 both ways. | Fixed |
| [Equivalence Class Divide and Conquer](cases/equivalence_class_divide_and_conquer.md) | The cost accounting is off, but reference and naive submissions score the same either way, and the swing needs an input we added. | Fixed |
| [Jagua Nesting Optimization](cases/jagua_nesting_optimization.md) | The overlap bug exists, but we have no good-faith submission that gains or loses from it. | Fixed |
| [OpenTTD Transport AI](cases/openttd_transport_ai.md) | The named API doesn't exist, but we measured no loss for a productive AI. The archived idle script scored 0, and a corrected one was not game-tested. | Fixed |
| [Portfolio Risk Calibration](cases/portfolio_risk_calibration.md) | The excess-return formula differs from the stated one, but a modified file on a local scoring path moved only from 15.35 to 15.34 (or 15.27 with aligned annualization). Harm on the current judge remains unverified. | Fixed |
| [Tree Block Partitioning](cases/tree_block_partitioning.md) | The supplied multiply is wrong when operands alias, but none of the 61 real archives hits it. | Fixed |

### No problem found

Nothing to correct. Each of these tasks carries a short usage note on its case page.

| Task | What we checked |
| --- | --- |
| [Ad Placement Optimization](cases/ad_placement_optimization.md) | No problem found; overlap and boundary checks match the original contest rules |
| [Anchorhead Text Adventure](cases/anchorhead_text_adventure.md) | No scoring problem; the grader counts each game's final score, not its peak |
| [ANN Vector Search QPS](cases/ann_vector_search_qps.md) | No scoring problem found; measured speed depends on the machine |
| [BipedalWalker Locomotion RL](cases/bipedalwalker_locomotion_rl.md) | Scores are capped at 30 out of 100 by design, as the task states |
| [Carleson Formalization](cases/carleson_formalization.md) | No problem found; one placeholder definition accepts any value |
| [Combinatorial Games Formalization](cases/combinatorial_games_formalization.md) | No problem found; correct proofs in different styles earn the same credit |
| [FLT Regular Formalization](cases/flt_regular_formalization.md) | No problem found; the 25 scored proofs match the task's own list |
| [K-12 Math Recommendation](cases/k12_math_recommendation.md) | No scoring problem found; shipped example reports are out of date |
| [New Foundations Consistency](cases/new_foundations_consistency.md) | Valid result with internet access, shown only for the unmodified starter; cannot grade offline |
| [Sphere Eversion Formalization](cases/sphere_eversion_formalization.md) | No problem found; no scored item found out of reach because of generated names |
| [Trinity Text Adventure](cases/trinity_text_adventure.md) | No problem found; the score is the game's own, and play is repeatable |
| [Tryst Text Adventure](cases/tryst_text_adventure.md) | No problem found; the score is the game's own repeatable score |
| [Vehicle Routing Time Windows](cases/vehicle_routing_time_windows.md) | Checker uses files solvers may edit; per-instance time argument does not fit the total |
| [VLIW Kernel Optimization](cases/vliw_kernel_optimization.md) | No problem found for submissions that follow the rules |
| [Wireless Electricity Layout](cases/wireless_electricity_layout.md) | A program that fails to compile can be listed as best, but scores never change |

</details>
