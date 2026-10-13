# Findings

All 51 public EdgeBench tasks, grouped by what goes wrong. Each row gives the problem in one line and how much it changes a score out of 100. The task name links to the full case: what the task asks, what goes wrong, how it was checked, the fix, and its limits.

"How much it matters" is the largest change we demonstrated or proved for one submission. It is not an estimate of the effect on the published leaderboard, which is in [IMPACT.md](IMPACT.md).

## Correct work is scored too low

An agent that does what the task asks loses points it should have earned.

| Task | Outcome | What goes wrong | How much it matters |
| --- | --- | --- | --- |
| [SMT Solver](cases/smt_solver.md) | Fixed | The answer checker misreads some valid solutions, so 27 hidden problems cannot be won | A perfect solver's maximum falls from 78.61 to 72.40 (6.21 points). All solvers lose the 27 problems; those following the documented format also lose 42 more. |
| [Borden Source Inversion](cases/borden_source_inversion.md) | Fixed | Hidden grading model uses unstated, non-physical conventions, so one-shot textbook solutions score near baseline | For a one-shot honest fit, about 24 of the original 109 points (22 of 100): 7.0 with a textbook model, 31.2 with the hidden conventions. Less, by an unmeasured amount, for agents learning from feedback (one reached 60.10). |
| [Arc Compiler Runtime](cases/arc_compiler_runtime.md) | Fixed | Hidden tests need an undocumented output format worth a third of the score | Up to 33.67 points lost, without warning, by any solver who keeps the starter's format or does not guess the required message wording. |
| [Lean Analysis Proofs](cases/lean_analysis_proofs.md) | Fixed | Two required statements are false; some points depend on proof style | At least 49 of 2901 points (1.69%) are out of reach for any honest, complete solution; up to 466 points could depend on proof style. |
| [PFR Formalization](cases/pfr_formalization.md) | Fixed | Five statements could never be earned because their type contained a hidden `sorry` | No solver could earn 5 statements (1.18 points out of 100, measured), or up to 9 (2.13 points) when later proofs used them (inferred from the upstream proofs). Only a solver that would have proved them loses points, so rankings could change. Re-scoring existing submissions with the fix changes nothing; new runs can gain up to 2.13 points. |
| [Tree Block Partitioning](cases/tree_block_partitioning.md) | Fixed | The supplied grading library miscalculates when a value multiplies itself | At most 5 of 100 points, only for submissions that multiply a value by itself. The other 95 points are unaffected. |
| [Git Rewrite in Zig](cases/git_rewrite_in_zig.md) | Fixed | Undisclosed file checks give an honest program 0; fixed, and a correct git still earns 100 | An honest submission that trips a check loses its whole score (up to 100 points). The time limit costs a correct git 2.6 points with 8 scripts per CPU, and nothing at 4 or fewer. |
| [Rust Multicrate Reconstruction](cases/rust_multicrate_reconstruction.md) | Fixed | Hidden tests that cannot compile zero two packages; fixed | In the publisher's grading environment a complete, correct solution scores 74.0 out of 100, against 94.7 with the fix (+20.7); no submission can gain more than 29.2. Stopping at the first failing test file costs 0.4 to 3.3 points in the measured submissions. Graded with the published images as shipped, the same solution scores 27.6. |
| [Juliet Vulnerability Analyzer](cases/juliet_vulnerability_analyzer.md) | Fixed | Public and hidden examples mark command-injection traces differently, and the original grader accepts only the hidden form | Only analyzers that use the public command-injection form are affected, and only upward: 2.49 points out of 100 for one that finds every bug with every other trace right, and 15 points for one that finds only the command-injection bugs (both measured). At most 26.47 points, computed exactly from the grader's formula, not run. |

## Wrong work is accepted

A plausible but incorrect submission passes the grader's checks, sometimes scoring higher than a correct one.

| Task | Outcome | What goes wrong | How much it matters |
| --- | --- | --- | --- |
| [Exchange Core Throughput](cases/exchange_core_throughput.md) | Fixed | The correctness check misses wrong fees and lost messages, so broken engines get full credit | Engines with these bugs get full credit instead of 0; across four runs each they scored 4.7–24.4 out of 100 and the correct engine 0–37.5, all within speed noise. At 4 grader CPUs any engine below about 2.09 million transactions per second scores 0; the prompt's own suggested thread change only reaches that zero point (2.09, a score of 0.02). |
| [FFmpeg swscale Reimplementation](cases/ffmpeg_swscale_reimplementation.md) | Fixed | Timed speed tests never check output, so failed calls earn speed credit | Up to 18.93 points out of 100 shown for honest but unfinished submissions whose library fails or does nothing on a timed conversion. |
| [Jagua Nesting Optimization](cases/jagua_nesting_optimization.md) | Fixed | The grader accepts overlapping shapes as valid layouts | Layouts with overlaps can score above every valid layout. The size was not measured. Honest layouts without overlaps are unaffected. |
| [College English Exam Bank](cases/college_english_exam_bank.md) | Fixed | Rubric rules the AI grader leaves out are counted as full marks | Raises a score by up to the value of the left-out rules; an empty assessment scores 100. Any submission can be affected when the AI model's assessment is incomplete. |
| [CTA Risk Budget Optimization](cases/cta_risk_budget_optimization.md) | Fixed | The overseas-exposure limit check skips currency conversion, so dollar positions are undercounted | Up to 5 points out of 100, only in the generous direction, and only for submissions holding US-dollar contracts. Compliant portfolios are never penalized. |
| [Graph Node Classification](cases/graph_node_classification.md) | Fixed | Non-numeric predictions are silently dropped and the run still counts as valid | Only submissions with missing or non-numeric predictions are affected. The added chance can raise a run's kept best score (general proof), but no gain for a real solver was shown. |
| [Equivalence Class Divide and Conquer](cases/equivalence_class_divide_and_conquer.md) | Fixed | One sub-problem's grader leaves the last state's size out of the cost limit check | At most 9.67 of 100 points, for a solution inside the window on all 28 large official inputs (5.17 if on one). No real gain was shown. |
| [Schemathesis Reporting Observability](cases/schemathesis_reporting_observability.md) | Fixed | Two hidden tests give credit for wrong or broken output | Wrong credit of about 2.4% of the total: 1/70 (about 1.4%) and 1/100 (1.0%); a correct writer with another suite name loses 1/70. The fixed version moves a score at most 4.76 points down, or 2.76 up (up to 4.76 only if a submission makes the GeneratedValue class unimportable). |
| [Schemathesis Datagen Pipeline](cases/schemathesis_datagen_pipeline.md) | Fixed | The date test checks only the format, not whether dates are real | At most about 1% of the total score, only for generators that produce invalid dates or times; they get the same credit as correct generators. |
| [Schemathesis Config Modernization](cases/schemathesis_config_modernization.md) | Fixed | One test does not check that a function is returned unchanged | At most 1/160 of the total (0.625 points) per run, either way: a wrapper decorator loses up to that; a correct one with that test group partly passed gains up to that. |

## The grader applies a different rule from the one the agent is told

The instructions promise one thing; the grader checks or runs another.

| Task | Outcome | What goes wrong | How much it matters |
| --- | --- | --- | --- |
| [Triangulation Coloring Optimization](cases/triangulation_coloring_optimization.md) | Fixed | The grader allows mesh moves the instructions forbid, and its test inputs overlap | Changes which moves are allowed for every solver; how much a strong solver gains from forbidden moves was not measured. On a 4-CPU grader, solutions using about 15 to 30 seconds of CPU per case lost their whole score. |
| [Warehouse Forklift Routing](cases/warehouse_forklift_routing.md) | Fixed | Time limit is stricter than promised, and no score can exceed about 30 | A solver taking 60 to 150 seconds on any input, or more than about 30 seconds of CPU per input on the publisher's 4-CPU grader (half a CPU each under the 60-second limit), loses its whole score; every solver is capped at about 30.6 out of 100 (30.3 before display rounding). |
| [Grid Turing Robot](cases/grid_turing_robot.md) | Fixed | On the publisher's 4-CPU grader, a solution within the 30-second limit can void the whole submission | Up to the full score for solutions using about 15 to 30 seconds of CPU per case on a 4-CPU grader; about 20 points if one case fails; at most 2.84 because the scale's zero point is set too high, so a do-nothing program already gets 2.84 points. |
| [Molecular Self Assembly](cases/molecular_self_assembly.md) | Fixed | On the publisher's 4-CPU grader, cases within the 30-second limit time out and score 0 | Up to nearly the full score for solutions using about 15 to 30 seconds of CPU per case on a 4-CPU grader; solutions that stop at a deadline got half the computing time. No way found for extra memory to raise a score. |
| [Vibrating Path Graph Coloring](cases/vibrating_path_graph_coloring.md) | Fixed | On the publisher's 4-CPU grader, a solution within the 30-second limit can leave the whole submission without a score | Up to the full score for solutions using about 14 to 30 seconds of CPU per case on a 4-CPU grader; solutions that stop at a deadline got half the computing time. The format mismatch changes no score. |
| [Apple Incremental Game](cases/apple_incremental_game.md) | Fixed | On the publisher's 4-CPU grader, cases within the 30-second limit time out and score 0 | Up to nearly the full score for solutions using about 15 to 30 seconds of CPU per case on a 4-CPU grader; solutions that stop at a deadline got half the computing time. The memory note matters only to users relying on the stated limit. |
| [OpenTTD Transport AI](cases/openttd_transport_ai.md) | Fixed | The instructions name a game function that does not exist | Up to the whole score for a submission that follows the instructions and calls the missing function. Submissions that use a different function are not affected. |
| [OpenRCT2 Theme Park AI](cases/openrct2_theme_park_ai.md) | Fixed | Instructions promise about 4 game years; the grader runs about 68 game days | Not measured as a score change. It changes what is measured: company value after about 2 months, not 4 years, for solvers who planned for the stated length. |
| [Portfolio Risk Calibration](cases/portfolio_risk_calibration.md) | Fixed | Excess return uses a slightly different formula than the instructions state | The total score moves by at most about 0.4 of 100 points: up by at most 0.39 for positive excess returns, down by at most 0.10 for negative ones (a 50-digit decimal sweep over the test data, not a proof). The order and sign of excess returns do not change (proved in Lean). |

## The 0–100 scale is wrong

The raw result is converted to 0–100 against reference points that cannot be reached or were measured on something else.

| Task | Outcome | What goes wrong | How much it matters |
| --- | --- | --- | --- |
| [Treant Forest](cases/treant_forest.md) | Fixed | The score scale tops out at 21 of 100 for any submission | Every submission's score is squeezed into 0 to 21, with ordering kept. A simple honest test submission scored 3.04. |
| [Integer Compression Codec](cases/integer_compression_codec.md) | Fixed | Scores compare against stored numbers the documented starter cannot produce | All submissions. Raw: starter about 0.24, not 1.0; a simple honest codec about 0.8, not 6 to 8; dataset weights off 7 to 9 times. Fixed scale: starter 0, codec about 1.8. |

## The wrong submission is kept

Each run should keep its best submission; here it keeps an earlier one.

| Task | Outcome | What goes wrong | How much it matters |
| --- | --- | --- | --- |
| [Order Addition Permutation Optimization](cases/order_addition_permutation_optimization.md) | Fixed | An outdated file check fails every submission, so later improvements are ignored | Each submission's own score is unaffected. A run's reported best score is wrong whenever a later valid submission scores higher; how often this happened was not measured. |

## Removed

No sound fix was possible, so the task is not part of the verified set.

| Task | Outcome | What goes wrong | How much it matters |
| --- | --- | --- | --- |
| [D-ABIC Gravity Inversion](cases/dabic_gravity_inversion.md) | Removed | 42 points come from the submission's own unchecked self-reported results | 42 points cannot be verified, for any submission. Choosing the allowed but penalised model-space formula can cost up to about 46 points for a strong solution (3.2 points of the total before the grader's penalty factor, at every level). |

## Kept: real issues that do not change scores

The issue is real, but it cannot change an honest agent's score out of 100 by a meaningful amount, or the task states it openly, and no change to the grader is needed.

| Task | Outcome | What goes wrong | How much it matters |
| --- | --- | --- | --- |
| [BipedalWalker Locomotion RL](cases/bipedalwalker_locomotion_rl.md) | Kept, with a note | Scores are capped at 30 out of 100 by design, as the task states | Every submission is limited to 30 of 100. A mismatched file scores like an untrained walker (about 10 with all loading checks passed). |
| [Vehicle Routing Time Windows](cases/vehicle_routing_time_windows.md) | Kept, with a note | Checker uses files solvers may edit; per-instance time argument does not fit the total | None for a program reporting its own cost and budgeting about 20 seconds per instance. Using the full 60 seconds caps the score near 37 (computed). Editing the header or flags was not tested. |
| [Ordinal Notation Well-Foundedness](cases/ordinal_notation_well_foundedness.md) | Kept, with a note | Grader correct; published results show targets 1–6 proved, 7–9 (64 of 85 points) open | No effect on honest proofs was found. A proof needing a helper file with an excluded name, or taking over 300 seconds to compile, would fail. |

## Kept: scores that depend on chance, machine speed or network access

The grader works, but repeated runs or different machines can give different scores. This is noise that no change to the grader removes, so these tasks are kept with a note even where the effect is large (ANN Vector Search: about ±7 of 100 points per grading).

| Task | Outcome | What goes wrong | How much it matters |
| --- | --- | --- | --- |
| [NetHack Dungeon Agent](cases/nethack_dungeon_agent.md) | Kept, with a note | Game seeding silently fails, so the 20 graded games are random and scores vary | For the starter, 0.02 points out of 100. For competent agents (up to 41.9 recorded) the variation was not measured, so whether it matters is unknown. A game over 120 seconds scores 0. |
| [Wesnoth Tactical AI](cases/wesnoth_tactical_ai.md) | Kept, with a note | The supplied starter program is broken, and repeat games give different results | The broken starter scores 0 for anyone submitting or building on it unchanged. Non-repeatable games move a score by about ±4–5 of 100 points per grading (binomial estimate, not measured). |
| [ANN Vector Search QPS](cases/ann_vector_search_qps.md) | Kept, with a note | No scoring problem found; measured speed depends on the machine | Speed varied 1.31-fold between gradings of one configuration on one machine: 13.9 of 100 points (about ±7 per grading) where agents score (23.8–59.7). Scores from different machines are not comparable. |
| [DCSS Dungeon AI](cases/dcss_dungeon_ai.md) | Kept, with a note | Scoring matches the instructions; scores depend on machine speed | Not measured: the effect of machine speed is unmeasured. |
| [Wireless Electricity Layout](cases/wireless_electricity_layout.md) | Kept, with a note | A program that fails to compile can be listed as best, but scores never change | The compile-failure rule changes no score (proved in Lean). Separately, one failed or timed-out case scores the whole submission 0; under a 5-second wall-clock limit this is machine-dependent (unmeasured). The starter scores 0. |
| [Ad Placement Optimization](cases/ad_placement_optimization.md) | Kept, with a note | No problem found; overlap and boundary checks match the original contest rules | No effect from the scoring rules. Not measured: with under 2 CPUs, a solver timing itself by CPU time rather than wall-clock time can time out on every case. |
| [New Foundations Consistency](cases/new_foundations_consistency.md) | Kept, with a note | Valid result with internet access, shown only for the unmodified starter; cannot grade offline | No effect measured. Offline graders give no score at all. The renaming risk is at most 0.67% of the score, an upper bound, not a measured loss. |
| [K-12 Math Recommendation](cases/k12_math_recommendation.md) | Kept, with a note | No scoring problem found; shipped example reports are out of date | No effect on honest submissions under normal memory limits. Under a tight address-space limit every submission gets 0 with an error. |

## Kept: no problem found

The grader scores honest work as the task promises. Each of these tasks carries a short usage note.

| Task | What we checked |
| --- | --- |
| [Anchorhead Text Adventure](cases/anchorhead_text_adventure.md) | No scoring problem; the grader counts each game's final score, not its peak |
| [Carleson Formalization](cases/carleson_formalization.md) | No problem found; one placeholder definition accepts any value |
| [Combinatorial Games Formalization](cases/combinatorial_games_formalization.md) | No problem found; honest proofs in different styles earn the same credit |
| [FLT Regular Formalization](cases/flt_regular_formalization.md) | No problem found; the 25 scored proofs match the task's own list |
| [Sphere Eversion Formalization](cases/sphere_eversion_formalization.md) | No problem found; no scored item found out of reach because of generated names |
| [Trinity Text Adventure](cases/trinity_text_adventure.md) | No problem found; the score is the game's own, and play is repeatable |
| [Tryst Text Adventure](cases/tryst_text_adventure.md) | No problem found; the score is the game's own repeatable score |
| [VLIW Kernel Optimization](cases/vliw_kernel_optimization.md) | No problem found for honest submissions |
