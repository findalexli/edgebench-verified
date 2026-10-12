# Findings

All 51 public EdgeBench tasks, grouped by what goes wrong. Each row gives the problem in one line and how much it changes a score out of 100. The task name links to the full case: what the task asks, what goes wrong, how it was checked, the fix, and its limits.

"How much it matters" is the largest change we demonstrated or proved for one submission. It is not an estimate of the effect on the published leaderboard, which is in [IMPACT.md](IMPACT.md).

## Correct work is scored too low

An agent that does what the task asks loses points it should have earned.

| Task | Outcome | What goes wrong | How much it matters |
| --- | --- | --- | --- |
| [Smt Solver](cases/smt_solver.md) | Fixed | The answer checker misreads some valid solutions, so 27 hidden problems cannot be won | A perfect solver's maximum falls from 78.61 to 72.40 (6.21 points). All solvers lose the 27 problems; those following the documented format also lose 42 more. |
| [Borden Source Inversion](cases/borden_source_inversion.md) | Fixed | The hidden grading model uses unstated, non-physical conventions, so textbook solutions score near baseline | About 24 points out of 100: the same honest fitting method scores 7.0 with a textbook model and 31.2 with the grader's hidden conventions. Affects every documentation-following solver. |
| [Arc Compiler Runtime](cases/arc_compiler_runtime.md) | Fixed | Hidden tests need an undocumented output format worth a third of the score | Up to 33.67 points lost, without warning, by any solver who keeps the starter's format or does not guess the required message wording. |
| [Lean Analysis Proofs](cases/lean_analysis_proofs.md) | Fixed | Two required statements are false; some points depend on proof style | At least 49 of 2901 points (1.69%) are out of reach for any honest, complete solution; up to 466 points could depend on proof style. |
| [Tree Block Partitioning](cases/tree_block_partitioning.md) | Fixed | The supplied grading library miscalculates when a value multiplies itself | At most 5 of 100 points, only for submissions that multiply a value by itself. The other 95 points are unaffected. |

## Wrong work is accepted

A plausible but incorrect submission passes the grader's checks, sometimes scoring higher than a correct one.

| Task | Outcome | What goes wrong | How much it matters |
| --- | --- | --- | --- |
| [Exchange Core Throughput](cases/exchange_core_throughput.md) | Fixed | The correctness check misses wrong fees and lost messages, so broken engines get full credit | Engines with these bugs get full credit instead of 0; in single runs one scored 24.4 versus 7.1 for the correct engine, a gap within speed noise. |
| [Ffmpeg Swscale Reimplementation](cases/ffmpeg_swscale_reimplementation.md) | Fixed | Timed speed tests never check output, so failed calls earn speed credit | Up to 18.93 points out of 100 shown for honest but unfinished submissions whose library fails or does nothing on a timed conversion. |
| [Jagua Nesting Optimization](cases/jagua_nesting_optimization.md) | Fixed | The grader accepts overlapping shapes as valid layouts | Layouts with overlaps can score above every valid layout. The size was not measured. Honest layouts without overlaps are unaffected. |
| [College English Exam Bank](cases/college_english_exam_bank.md) | Fixed | Rubric rules the AI grader leaves out are counted as full marks | Raises a score by up to the value of the left-out rules; an empty assessment scores 100. Any submission can be affected when the AI model's assessment is incomplete. |
| [Cta Risk Budget Optimization](cases/cta_risk_budget_optimization.md) | Fixed | The overseas-exposure limit check skips currency conversion, so dollar positions are undercounted | Up to 5 points out of 100, only in the generous direction, and only for submissions holding US-dollar contracts. Compliant portfolios are never penalized. |
| [Graph Node Classification](cases/graph_node_classification.md) | Fixed | Non-numeric predictions are silently dropped and the run still counts as valid | Only submissions with missing or non-numeric predictions are affected. It adds chance to their score; no expected gain was shown, and whether it can raise scores was not established. |
| [Equivalence Class Divide And Conquer](cases/equivalence_class_divide_and_conquer.md) | Fixed | One sub-problem's grader leaves the last step out of the cost limit check | In the worst case a solution could gain up to 5.17 of 100 points. No real gain was shown. |
| [Schemathesis Reporting Observability](cases/schemathesis_reporting_observability.md) | Fixed | Two hidden tests give credit for wrong or broken output | About 2.4% of the total in all: at most 1/70 (about 1.4%) and 1/100 (1.0%). Only submissions with these mistakes gain. |
| [Schemathesis Datagen Pipeline](cases/schemathesis_datagen_pipeline.md) | Fixed | The date test checks only the format, not whether dates are real | At most about 1% of the total score, only for generators that produce invalid dates or times; they get the same credit as correct generators. |
| [Schemathesis Config Modernization](cases/schemathesis_config_modernization.md) | Fixed | One test does not check that a function is returned unchanged | At most about 1/150 of the total score, only for submissions whose decorator returns something other than the original function. |

## The grader applies a different rule from the one the agent is told

The instructions promise one thing; the grader checks or runs another.

| Task | Outcome | What goes wrong | How much it matters |
| --- | --- | --- | --- |
| [Triangulation Coloring Optimization](cases/triangulation_coloring_optimization.md) | Fixed | The grader allows mesh moves the instructions forbid, and its test inputs overlap | Changes which moves are allowed for every solver. How much a strong solver gains from forbidden moves was not measured. |
| [Warehouse Forklift Routing](cases/warehouse_forklift_routing.md) | Fixed | Time limit is stricter than promised, and no score can exceed about 30 | A solver taking 60 to 150 seconds on any input loses its whole score; every solver is capped at about 30.3 out of 100. |
| [Openttd Transport Ai](cases/openttd_transport_ai.md) | Fixed | The instructions name a game function that does not exist | Up to the whole score for a submission that follows the instructions and calls the missing function. Submissions that use a different function are not affected. |
| [Openrct2 Theme Park Ai](cases/openrct2_theme_park_ai.md) | Fixed | Instructions promise about 4 game years; the grader runs about 68 game days | Not measured as a score change. It changes what is measured: company value after about 2 months, not 4 years, for solvers who planned for the stated length. |

## The 0–100 scale is wrong

The raw result is converted to 0–100 against reference points that cannot be reached or were measured on something else.

| Task | Outcome | What goes wrong | How much it matters |
| --- | --- | --- | --- |
| [Treant Forest](cases/treant_forest.md) | Fixed | The score scale tops out at 21 of 100 for any submission | Every submission's score is squeezed into 0 to 21, with ordering kept. A simple honest test submission scored 3.04. |
| [Integer Compression Codec](cases/integer_compression_codec.md) | Fixed | Scores compare against stored numbers the documented starter cannot produce | All submissions: the starter scores 0.24 instead of 1.0 and a simple honest codec 0.76 instead of 6.24; relative dataset weights are off by up to 6.7 times. |

## The wrong submission is kept

Each run should keep its best submission; here it keeps an earlier one.

| Task | Outcome | What goes wrong | How much it matters |
| --- | --- | --- | --- |
| [Order Addition Permutation Optimization](cases/order_addition_permutation_optimization.md) | Fixed | An outdated file check fails every submission, so later improvements are ignored | Each submission's own score is unaffected. A run's reported best score is wrong whenever a later valid submission scores higher; how often this happened was not measured. |

## Removed

No sound fix was possible, so the task is not part of the verified set.

| Task | Outcome | What goes wrong | How much it matters |
| --- | --- | --- | --- |
| [Dabic Gravity Inversion](cases/dabic_gravity_inversion.md) | Removed | 42 points come from the submission's own unchecked self-reported results | 42 points cannot be verified, for every submission. The form penalty costs up to about 46 points at a strong level, and 3.2 raw points at every level. |

## Kept: real issues that do not change scores

The issue is real, but it cannot change an honest agent's score out of 100 by a meaningful amount, or the task states it openly.

| Task | Outcome | What goes wrong | How much it matters |
| --- | --- | --- | --- |
| [Wireless Electricity Layout](cases/wireless_electricity_layout.md) | Kept, with a note | A program that fails to compile can be listed as best, but scores never change | No effect on scores out of 100: every affected submission scores 0 either way, an argument checked on 200,000 random submission histories. |
| [Vibrating Path Graph Coloring](cases/vibrating_path_graph_coloring.md) | Kept, with a note | The tester rejects one documented output format, but no score changes | No effect on any score on the official puzzles; a solver using the documented no-hit format only sees a different error message. |
| [Molecular Self Assembly](cases/molecular_self_assembly.md) | Kept, with a note | The stated 1 GB memory limit is not enforced; no score advantage found | No way found for extra memory to raise a score; this is reasoned, not measured. Solutions using too much memory may lose cases unpredictably. |
| [Portfolio Risk Calibration](cases/portfolio_risk_calibration.md) | Kept, with a note | Excess return uses a slightly different formula than the instructions state | The total score moves by at most about 0.4 of 100 points, for all submissions. The ranking of excess returns does not change. |
| [Rust Multicrate Reconstruction](cases/rust_multicrate_reconstruction.md) | Kept, with a note | A test exemption can forgive one unrelated failure, worth at most 0.1 points | At most +0.1 points out of 100 per grading, only for solvers whose excused test passes while another test in the same package fails. |
| [Grid Turing Robot](cases/grid_turing_robot.md) | Kept, with a note | Scored correctly, but one failed case voids the whole submission unannounced | About 20 points if one case fails; at most 2.84 points from the scale offset; up to the full score on graders with fewer than about 8 CPUs. |
| [Bipedalwalker Locomotion Rl](cases/bipedalwalker_locomotion_rl.md) | Kept, with a note | Scores are capped at 30 out of 100 by design, as the task states | Every submission is limited to 30 of 100. A mismatched file scores like an untrained walker plus the points for loading. |
| [Vehicle Routing Time Windows](cases/vehicle_routing_time_windows.md) | Kept, with a note | No scoring problem; the checker is built from a file solvers may edit | None for a program that reports its own computed cost. Editing the shared distance file was not tested, so any effect is not measured. |
| [Juliet Vulnerability Analyzer](cases/juliet_vulnerability_analyzer.md) | Kept, with a note | Answer key checks out; public and hidden examples differ in one convention | About 2.5 points out of 100 (an estimate, not measured), only for solvers that copy the public command-injection convention. The use-after-free effect was not measured. |
| [Apple Incremental Game](cases/apple_incremental_game.md) | Kept, with a note | No scoring problem found; the stated 1 GB memory limit is not enforced | No effect on the scores of honest submissions. The memory note matters only to users who rely on the stated limit. |
| [Ordinal Notation Well Foundedness](cases/ordinal_notation_well_foundedness.md) | Kept, with a note | Grader correct; only the first of nine targets is known to be provable | No effect on honest proofs was found. A proof needing a helper file with an excluded name, or taking over 300 seconds to compile, would fail. |

## Kept: scores that depend on chance, machine speed or network access

The grader works, but repeated runs or different machines can give different scores.

| Task | Outcome | What goes wrong | How much it matters |
| --- | --- | --- | --- |
| [Nethack Dungeon Agent](cases/nethack_dungeon_agent.md) | Kept, with a note | Game seeding silently fails, so the 20 graded games are random and scores vary | For the starter program, 0.02 points out of 100. The variation for a competent agent was not measured and is likely much larger. |
| [Wesnoth Tactical Ai](cases/wesnoth_tactical_ai.md) | Kept, with a note | The supplied starter program is broken, and repeat games give different results | The broken starter scores 0 for anyone who submits or builds on it unchanged. The effect of non-repeatable games on scores was not measured. |
| [Ann Vector Search Qps](cases/ann_vector_search_qps.md) | Kept, with a note | No scoring problem found; measured speed depends on the machine | No effect on the scores of honest submissions, but the same submission's speed varied by ±17% between runs, so scores from different machines are not comparable. |
| [Dcss Dungeon Ai](cases/dcss_dungeon_ai.md) | Kept, with a note | Scoring matches the instructions; one failed game voids the whole submission | No effect observed. In the worst case one failed game voids a whole submission; the effect of machine speed is unmeasured. |
| [New Foundations Consistency](cases/new_foundations_consistency.md) | Kept, with a note | Grades correctly with internet access; cannot grade offline | No effect measured. Offline graders give no score at all. The renaming risk is at most 0.67% of the score, an upper bound, not a measured loss. |
| [K12 Math Recommendation](cases/k12_math_recommendation.md) | Kept, with a note | No scoring problem found; shipped example reports are out of date | No effect on honest submissions under normal memory limits. Under a tight memory limit every submission gets 0 with an error. |

## Kept: no problem found

The grader scores honest work as the task promises. Some of these tasks carry a short usage note.

| Task | What we checked |
| --- | --- |
| [Ad Placement Optimization](cases/ad_placement_optimization.md) | No problem found; overlap and boundary checks match the original contest rules |
| [Anchorhead Text Adventure](cases/anchorhead_text_adventure.md) | No scoring problem; the grader counts each game's final score, not its peak |
| [Carleson Formalization](cases/carleson_formalization.md) | No problem found; one placeholder definition accepts any value |
| [Combinatorial Games Formalization](cases/combinatorial_games_formalization.md) | No problem found; honest proofs in different styles earn the same credit |
| [Flt Regular Formalization](cases/flt_regular_formalization.md) | No problem found; the 25 scored proofs match the task's own list |
| [Git Rewrite In Zig](cases/git_rewrite_in_zig.md) | No problem found; a correct program can earn the full 100 |
| [Pfr Formalization](cases/pfr_formalization.md) | No problem found; two proof styles scored the same |
| [Sphere Eversion Formalization](cases/sphere_eversion_formalization.md) | No problem found; all scored items reachable by an honest solution |
| [Trinity Text Adventure](cases/trinity_text_adventure.md) | No problem found; the score is the game's own, and play is repeatable |
| [Tryst Text Adventure](cases/tryst_text_adventure.md) | No problem found; the score is the game's own repeatable score |
| [Vliw Kernel Optimization](cases/vliw_kernel_optimization.md) | No problem found for honest submissions |
