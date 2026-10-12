# Case pages

One page per public EdgeBench task: what the task asks, what goes wrong, how much it matters, the fix, how it was checked, the limits, and how to reproduce it.

| Task | Field | Outcome | In one line |
| --- | --- | --- | --- |
| [ANN Vector Search QPS](ann_vector_search_qps.md) | Systems & Software Engineering | Kept, with a note | No scoring problem found; measured speed depends on the machine |
| [Ad Placement Optimization](ad_placement_optimization.md) | Combinatorial Optimization | Kept, with a note | No problem found; overlap and boundary checks match the original contest rules |
| [Anchorhead Text Adventure](anchorhead_text_adventure.md) | Interactive Games & Simulators | Kept, with a note | No scoring problem; the grader counts each game's final score, not its peak |
| [Apple Incremental Game](apple_incremental_game.md) | Combinatorial Optimization | Kept, with a note | No scoring problem found; the stated 1 GB memory limit is not enforced |
| [Arc Compiler Runtime](arc_compiler_runtime.md) | Systems & Software Engineering | Fixed | Hidden tests need an undocumented output format worth a third of the score |
| [BipedalWalker Locomotion RL](bipedalwalker_locomotion_rl.md) | Scientific Problems & ML | Kept, with a note | Scores are capped at 30 out of 100 by design, as the task states |
| [Borden Source Inversion](borden_source_inversion.md) | Scientific Problems & ML | Fixed | The hidden grading model uses unstated, non-physical conventions, so textbook solutions score near baseline |
| [CTA Risk Budget Optimization](cta_risk_budget_optimization.md) | Professional Knowledge Work | Fixed | The overseas-exposure limit check skips currency conversion, so dollar positions are undercounted |
| [Carleson Formalization](carleson_formalization.md) | Formal Math & Theorem Proving | Kept, with a note | No problem found; one placeholder definition accepts any value |
| [College English Exam Bank](college_english_exam_bank.md) | Professional Knowledge Work | Fixed | Rubric rules the AI grader leaves out are counted as full marks |
| [Combinatorial Games Formalization](combinatorial_games_formalization.md) | Formal Math & Theorem Proving | Kept, with a note | No problem found; honest proofs in different styles earn the same credit |
| [D-ABIC Gravity Inversion](dabic_gravity_inversion.md) | Scientific Problems & ML | Removed | 42 points come from the submission's own unchecked self-reported results |
| [DCSS Dungeon AI](dcss_dungeon_ai.md) | Interactive Games & Simulators | Kept, with a note | Scoring matches the instructions; one failed game voids the whole submission |
| [Equivalence Class Divide and Conquer](equivalence_class_divide_and_conquer.md) | Combinatorial Optimization | Fixed | One sub-problem's grader leaves the last step out of the cost limit check |
| [Exchange Core Throughput](exchange_core_throughput.md) | Systems & Software Engineering | Fixed | The correctness check misses wrong fees and lost messages, so broken engines get full credit |
| [FFmpeg swscale Reimplementation](ffmpeg_swscale_reimplementation.md) | Systems & Software Engineering | Fixed | Timed speed tests never check output, so failed calls earn speed credit |
| [FLT Regular Formalization](flt_regular_formalization.md) | Formal Math & Theorem Proving | Kept, with a note | No problem found; the 25 scored proofs match the task's own list |
| [Git Rewrite in Zig](git_rewrite_in_zig.md) | Systems & Software Engineering | Kept, with a note | No problem found; a correct program can earn the full 100 |
| [Graph Node Classification](graph_node_classification.md) | Scientific Problems & ML | Fixed | Non-numeric predictions are silently dropped and the run still counts as valid |
| [Grid Turing Robot](grid_turing_robot.md) | Combinatorial Optimization | Kept, with a note | Scored correctly, but one failed case voids the whole submission unannounced |
| [Integer Compression Codec](integer_compression_codec.md) | Systems & Software Engineering | Fixed | Scores compare against stored numbers the documented starter cannot produce |
| [Jagua Nesting Optimization](jagua_nesting_optimization.md) | Combinatorial Optimization | Fixed | The grader accepts overlapping shapes as valid layouts |
| [Juliet Vulnerability Analyzer](juliet_vulnerability_analyzer.md) | Systems & Software Engineering | Kept, with a note | Answer key checks out; public and hidden examples differ in one convention |
| [K-12 Math Recommendation](k12_math_recommendation.md) | Professional Knowledge Work | Kept, with a note | No scoring problem found; shipped example reports are out of date |
| [Lean Analysis Proofs](lean_analysis_proofs.md) | Formal Math & Theorem Proving | Fixed | Two required statements are false; some points depend on proof style |
| [Molecular Self Assembly](molecular_self_assembly.md) | Combinatorial Optimization | Kept, with a note | The stated 1 GB memory limit is not enforced; no score advantage found |
| [NetHack Dungeon Agent](nethack_dungeon_agent.md) | Interactive Games & Simulators | Kept, with a note | Game seeding silently fails, so the 20 graded games are random and scores vary |
| [New Foundations Consistency](new_foundations_consistency.md) | Formal Math & Theorem Proving | Kept, with a note | Grades correctly with internet access; cannot grade offline |
| [OpenRCT2 Theme Park AI](openrct2_theme_park_ai.md) | Interactive Games & Simulators | Fixed | Instructions promise about 4 game years; the grader runs about 68 game days |
| [OpenTTD Transport AI](openttd_transport_ai.md) | Interactive Games & Simulators | Fixed | The instructions name a game function that does not exist |
| [Order Addition Permutation Optimization](order_addition_permutation_optimization.md) | Combinatorial Optimization | Fixed | An outdated file check fails every submission, so later improvements are ignored |
| [Ordinal Notation Well-Foundedness](ordinal_notation_well_foundedness.md) | Formal Math & Theorem Proving | Kept, with a note | Grader correct; only the first of nine targets is known to be provable |
| [PFR Formalization](pfr_formalization.md) | Formal Math & Theorem Proving | Kept, with a note | No problem found; two proof styles scored the same |
| [Portfolio Risk Calibration](portfolio_risk_calibration.md) | Professional Knowledge Work | Kept, with a note | Excess return uses a slightly different formula than the instructions state |
| [Rust Multicrate Reconstruction](rust_multicrate_reconstruction.md) | Systems & Software Engineering | Kept, with a note | A test exemption can forgive one unrelated failure, worth at most 0.1 points |
| [SMT Solver](smt_solver.md) | Combinatorial Optimization | Fixed | The answer checker misreads some valid solutions, so 27 hidden problems cannot be won |
| [Schemathesis Config Modernization](schemathesis_config_modernization.md) | Systems & Software Engineering | Fixed | One test does not check that a function is returned unchanged |
| [Schemathesis Datagen Pipeline](schemathesis_datagen_pipeline.md) | Systems & Software Engineering | Fixed | The date test checks only the format, not whether dates are real |
| [Schemathesis Reporting Observability](schemathesis_reporting_observability.md) | Systems & Software Engineering | Fixed | Two hidden tests give credit for wrong or broken output |
| [Sphere Eversion Formalization](sphere_eversion_formalization.md) | Formal Math & Theorem Proving | Kept, with a note | No problem found; all scored items reachable by an honest solution |
| [Treant Forest](treant_forest.md) | Combinatorial Optimization | Fixed | The score scale tops out at 21 of 100 for any submission |
| [Tree Block Partitioning](tree_block_partitioning.md) | Combinatorial Optimization | Fixed | The supplied grading library miscalculates when a value multiplies itself |
| [Triangulation Coloring Optimization](triangulation_coloring_optimization.md) | Combinatorial Optimization | Fixed | The grader allows mesh moves the instructions forbid, and its test inputs overlap |
| [Trinity Text Adventure](trinity_text_adventure.md) | Interactive Games & Simulators | Kept, with a note | No problem found; the score is the game's own, and play is repeatable |
| [Tryst Text Adventure](tryst_text_adventure.md) | Interactive Games & Simulators | Kept, with a note | No problem found; the score is the game's own repeatable score |
| [VLIW Kernel Optimization](vliw_kernel_optimization.md) | Systems & Software Engineering | Kept, with a note | No problem found for honest submissions |
| [Vehicle Routing Time Windows](vehicle_routing_time_windows.md) | Combinatorial Optimization | Kept, with a note | No scoring problem; the checker is built from a file solvers may edit |
| [Vibrating Path Graph Coloring](vibrating_path_graph_coloring.md) | Combinatorial Optimization | Kept, with a note | The tester rejects one documented output format, but no score changes |
| [Warehouse Forklift Routing](warehouse_forklift_routing.md) | Combinatorial Optimization | Fixed | Time limit is stricter than promised, and no score can exceed about 30 |
| [Wesnoth Tactical AI](wesnoth_tactical_ai.md) | Interactive Games & Simulators | Kept, with a note | The supplied starter program is broken, and repeat games give different results |
| [Wireless Electricity Layout](wireless_electricity_layout.md) | Combinatorial Optimization | Kept, with a note | A program that fails to compile can be listed as best, but scores never change |
