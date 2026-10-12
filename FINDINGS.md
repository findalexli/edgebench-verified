# Findings for EdgeBench maintainers

Every defect below was checked against the task's original, digest-pinned evaluator, by execution where feasible; a few rest on source reading or exact arithmetic, as their case pages state (for example the DCSS missing-morgue rule and the BipedalWalker ceiling). "Max effect" is the largest change to a good-faith solver's score we demonstrated or proved, on the task's 0–100 scale unless stated; it is not an estimate of historical leaderboard impact. Each task links to its case page (what we ran, the paired before/after table, limits, and how to reproduce). Tasks with no defect affecting good-faith solvers are listed at the end.

## Correct or honest work is scored below what it deserves

A solver doing what the task asks loses points, or cannot reach the score the scale promises.

| Task | Decision | What is wrong | Max effect |
| --- | --- | --- | --- |
| [Smt Solver](cases/smt_solver.md) | Repair (v2) | Witness checker keys UF values by source text, so 27 satisfiable hidden files are unwinnable | perfect-solver max 78.61→72.40 (−6.21) |
| [Warehouse Forklift Routing](cases/warehouse_forklift_routing.md) | Repair (v2) | Prompt promises 30 s per test case (150 s/input) but the evaluator gives 60 s per input; and a lower bound proved in Lean for a model of the tester (model matched to the tester by a 294-string differential test) shows every valid TOTAL ≥ 712.538 > rank1 395.80, so the top two anchors are unreachable and normalized scores are capped at ≈30.3 | whole score for budget-following solvers; ~70 points of the scale unreachable |
| [Borden Source Inversion](cases/borden_source_inversion.md) | Repair (v2) | Hidden forward model uses an undisclosed non-physical convention (mass-rate as mass, no porosity, mg/m³ as mg/L, source plane at box bottom); honest textbook solver scores at baseline; raw score uncapped (109) | ≈24 points (7.0 vs 31.2 for the same honest fit) |
| [Arc Compiler Runtime](cases/arc_compiler_runtime.md) | Repair (v2) | Hidden tests require an undocumented analyze() return format; TASK.md claims starter scores 0 (actual 35.59) | up to 33.7 points |
| [Lean Analysis Proofs](cases/lean_analysis_proofs.md) | Repair (v2) | Two required statements are false (refuted in Lean inside the task image), and compiler-generated auxiliary targets are credited by name and printed type, so at least 49 points (1.69%) are unattainable for any honest complete solution and up to 466 depend on proof style | ≥1.69% unattainable; up to 16% style-dependent |
| [Order Addition Permutation Optimization](cases/order_addition_permutation_optimization.md) | Repair (v2) | Integrity test expects a stale helper hash; every submission capped at pass rate 0.8, so pass_rate_first freezes the run on its first valid submission | material: later improvements ignored |
| [Tree Block Partitioning](cases/tree_block_partitioning.md) | Repair (v2) | Supplied in-place multiply wrong when operands alias (v *= v) | ≤5/100 (T2), only for aliasing solvers |
| [Dabic Gravity Inversion](cases/dabic_gravity_inversion.md) | Exclude | 42 of the points come from self-reported JSON the judge cannot verify; an undisclosed data-space-only gate also penalised the model-space form the prompt allows (fixed in a partial v2) | 42 points unverifiable; form gate up to ~46 at strong tier |
| [Integer Compression Codec](cases/integer_compression_codec.md) | Repair (v2) | Stored baseline table (impossible <8 bpi for varint) replaces the documented starter baseline | starter 0.24 vs documented 1.0; honest codec 0.76 vs 6.24 |
| [Treant Forest](cases/treant_forest.md) | Repair (v2) | Anchors exceed the 2N² turn cap: max normalized 21.02; movement semantics question separate | compresses all scores into 0–21 |

## Incorrect solutions are accepted or rewarded

A plausible wrong solution passes the checks, sometimes scoring higher than a correct one.

| Task | Decision | What is wrong | Max effect |
| --- | --- | --- | --- |
| [Exchange Core Throughput](cases/exchange_core_throughput.md) | Repair (v2) | Correctness gate misses fee/event errors; incorrect engines score higher than correct one | full credit for an incorrect engine (two one-edit bugs passed the check; their higher raw scores in single runs are within throughput noise) |
| [Ffmpeg Swscale Reimplementation](cases/ffmpeg_swscale_reimplementation.md) | Repair (v2) | Timed workloads never correctness-checked; failed calls earn speedup credit | up to ~19 points shown for honest-incomplete variants |
| [Jagua Nesting Optimization](cases/jagua_nesting_optimization.md) | Repair (v2) | Validator accepts large positive-area overlaps (identical placements, containment, half-slides) | material: infeasible layouts accepted |
| [Triangulation Coloring Optimization](cases/triangulation_coloring_optimization.md) | Repair (v2) | Flip-legality rule omits the README's convexity condition; the same rule generated the cases (all 10 overlap/fold) and scores submissions | material: changes which flips are legal for every solver |
| [College English Exam Bank](cases/college_english_exam_bank.md) | Repair (v2) | Grader code treats an unassessed rubric rule as full marks | up to the omitted rules' value |
| [Cta Risk Budget Optimization](cases/cta_risk_budget_optimization.md) | Repair (v2) | Cross-border exposure omits USD→CNY conversion required by the risk policy (~7× undercount) | up to 5/100, lenient only |
| [Graph Node Classification](cases/graph_node_classification.md) | Repair (v2) | Non-integer predictions silently dropped and run marked valid; (NaN-confidence clipping is score-neutral) | variance only; no expected gain shown |
| [Equivalence Class Divide And Conquer](cases/equivalence_class_divide_and_conquer.md) | Repair (v2) | T3 checker cost loop skips the final state (accepts ≤ limit + |last target|) | bounded (≤0.04% over limit); no gain shown |
| [Schemathesis Reporting Observability](cases/schemathesis_reporting_observability.md) | Repair (v2) | JUnit check accepts malformed output; body-coverage test is vacuous | ~2.4% |
| [Schemathesis Datagen Pipeline](cases/schemathesis_datagen_pipeline.md) | Repair (v2) | HTTP-date check is shape-only (accepts invalid dates/times) | ~1% |
| [Schemathesis Config Modernization](cases/schemathesis_config_modernization.md) | Repair (v2) | Phase 3 test checks callable() not identity | ~1/150 of score |

## The task cannot deliver what its prompt promises

The evaluator runs something different from what the solver is told.

| Task | Decision | What is wrong | Max effect |
| --- | --- | --- | --- |
| [Openrct2 Theme Park Ai](cases/openrct2_theme_park_ai.md) | Repair (v2) | Promised ~4 game years cannot run in the 120 s budget (~68 game days observed); score is an early snapshot | material: prompt/horizon mismatch |
| [Openttd Transport Ai](cases/openttd_transport_ai.md) | Retain with note | Prompt goal names a non-existent API (GetCompanyValue) that crashes a solver's AI; scorer itself works | whole score for prompt-following solvers (v2 prompt fix optional) |

## Real but immaterial, or disclosed, issues (retained with a note)

The defect is real but cannot materially change a good-faith solver's reported score, or the task discloses it.

| Task | Decision | What is wrong | Max effect |
| --- | --- | --- | --- |
| [Wireless Electricity Layout](cases/wireless_electricity_layout.md) | Retain with note | Compile failure counted once vs per case in raw totals | 0 normalized (monotonicity argument, checked on 200,000 random histories) |
| [Vibrating Path Graph Coloring](cases/vibrating_path_graph_coloring.md) | Retain with note | Tester rejects documented 3-line zero-hit format | 0 on official cases (zero-hit never valid) |
| [Molecular Self Assembly](cases/molecular_self_assembly.md) | Retain with note | Per-solution memory limit not enforced (one aggregate container limit) | no score mechanism found |
| [Portfolio Risk Calibration](cases/portfolio_risk_calibration.md) | Retain with note | Annual excess computed as annualized difference, not difference of annualized returns | ≤~0.4 points; ordering preserved |
| [Rust Multicrate Reconstruction](cases/rust_multicrate_reconstruction.md) | Retain with note | Exempt-test credit can forgive an unrelated failure | ≤0.1/100 |
| [Grid Turing Robot](cases/grid_turing_robot.md) | Retain with note | Baseline anchor 9,025,986 vs actual 7,744,909 (+2.84); one failed case voids submission (undisclosed); ≥8 CPUs needed for reproducibility | 2.84 (baseline anchor); ~20 if one case fails (undisclosed rule); up to full score on <8 judge CPUs |
| [Bipedalwalker Locomotion Rl](cases/bipedalwalker_locomotion_rl.md) | Retain with note | Task score capped at 30 (disclosed design) → max normalized 30 | by design |
| [Vehicle Routing Time Windows](cases/vehicle_routing_time_windows.md) | Retain with note | Decimal tolerance immaterial (exact check); instruction clarification adopted as note; the verifier is compiled from the submitted include/types.h, so a solver edit to the distance code changes the checker (recommended hardening: build verifier from the original header) | none |
| [Juliet Vulnerability Analyzer](cases/juliet_vulnerability_analyzer.md) | Retain with note | Labels consistent (723/723); public/hidden CWE-78 trace convention differs | ~2.5 points |
| [Apple Incremental Game](cases/apple_incremental_game.md) | Retain with note | Anchors consistent with an independent simulator; advertised 1 GB memory policy not enforced per solution (note) | 0 |
| [Ordinal Notation Well Foundedness](cases/ordinal_notation_well_foundedness.md) | Retain with note | Grader correct on honest/Admitted/axiom controls; helper file-name filter undisclosed; targets 2–9 unproven | 0 found |

## Repeatability and environment notes

Scores depend on randomness, host speed or network access that the task does not control.

| Task | Decision | What is wrong | Max effect |
| --- | --- | --- | --- |
| [Nethack Dungeon Agent](cases/nethack_dungeon_agent.md) | Retain with note | Seeding silently fails: the 20 graded games are unseeded and random (run-to-run variance unmeasured for scoring agents); 120 s per-game limit not stated in the prompt | variance unmeasured for scoring agents |
| [Wesnoth Tactical Ai](cases/wesnoth_tactical_ai.md) | Retain with note | Evaluation fits budget (80–172 s); shipped baseline recruit config broken (scores 0); games not repeatable | baseline only |
| [Ann Vector Search Qps](cases/ann_vector_search_qps.md) | Retain with note | QPS host-dependent; scorer isolation out of scope | none for honest solvers |
| [Dcss Dungeon Ai](cases/dcss_dungeon_ai.md) | Retain with note | One missing morgue voids the 5-game mean; wall-clock noise unmeasured | 0 observed |
| [New Foundations Consistency](cases/new_foundations_consistency.md) | Retain with note | Grades correctly with the judge's network (Lake re-clones doc-gen4 at the manifest-pinned commit 86d735ec, valid result); cannot be graded offline; 15 of 370 aux targets exposed to renumbering (≤0.67%), untested | 0 measured |
| [K12 Math Recommendation](cases/k12_math_recommendation.md) | Retain with note | Positive control valid (24.7/17.6); earlier failure was audit infrastructure; shipped reports stale | 0 found |

## No defect affecting good-faith solvers (some carry usage notes)

[Ad Placement Optimization](cases/ad_placement_optimization.md), [Anchorhead Text Adventure](cases/anchorhead_text_adventure.md), [Carleson Formalization](cases/carleson_formalization.md), [Combinatorial Games Formalization](cases/combinatorial_games_formalization.md), [Flt Regular Formalization](cases/flt_regular_formalization.md), [Git Rewrite In Zig](cases/git_rewrite_in_zig.md), [Pfr Formalization](cases/pfr_formalization.md), [Sphere Eversion Formalization](cases/sphere_eversion_formalization.md), [Trinity Text Adventure](cases/trinity_text_adventure.md), [Tryst Text Adventure](cases/tryst_text_adventure.md), [Vliw Kernel Optimization](cases/vliw_kernel_optimization.md).
