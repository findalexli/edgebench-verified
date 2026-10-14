# Effect on the published leaderboard

The public task averages are not enough to compute a corrected leaderboard, because the original submissions and the raw scores of each run are not available. The intervals below carry the rounding of the public scores, the scale changes and the documented effect limits through to each model's average. They are outer envelopes. They are not estimates, and we have not shown that their endpoints can be reached. `tools/estimate_impact.py` generates this page; [data/impact.csv](data/impact.csv) has the machine-readable results.

## Conditional score intervals

Every interval keeps the same set of valid runs and treats kept tasks as unchanged. Each one depends on the effect directions and limits listed below, including the inferred PFR credit and the documented cap on Treant's raw total. The 'Plus documented limits' and 'Plus Portfolio sensitivity' columns count every direction-only (open) effect as zero; only the full-domain envelope lets those effects move. New runs, changed failure rates, agents adapting to a fix, or an unsupported assumption about an effect's direction can break these conditions. None of the intervals is a statistical confidence interval.

| Model | Published mean | Scale changes and removal | Plus documented limits | Plus Portfolio sensitivity assumption | Full-domain outer envelope |
| --- | ---: | ---: | ---: | ---: | ---: |
| Opus 4.8 | 44.2 | 45.92–46.05 | 45.49–47.30 | 45.49–47.30 | 36.01–67.13 |
| GPT-5.5 | 43.1 | 44.73–44.86 | 44.30–46.35 | 44.30–46.36 | 35.54–67.81 |
| GPT-5.4 | 34.2 | 35.57–35.71 | 35.15–37.71 | 35.15–37.71 | 28.27–62.37 |
| GLM-5.1 | 30.4 | 31.81–31.94 | 31.39–34.00 | 31.38–34.01 | 25.29–59.55 |
| DS-V4-Pro | 25.7 | 26.77–26.91 | 26.48–28.98 | 26.47–28.99 | 20.45–53.98 |

`scale_midpoint_mean` in the CSV is a midpoint for display, not an inferred corrected mean. The CSV endpoints are the exact rational endpoints rounded outward to 9 decimals, so each CSV interval contains the exact one. In the full-domain envelope, open effects can span the rest of the score range in their stated directions, and Portfolio gets the full 0–100 range because its sweep does not establish a global bound.

## What can be recovered from an average

- **D-ABIC:** remove the task; the denominator becomes 50 (49 for Opus 4.8, whose Rust result is missing).
- **Borden:** multiply the rounded raw average by 100/109 and carry the ±0.05 rounding through. The conversion is affine, so it gives the same result before or after averaging. The separate effect of the instruction repair still needs new runs.
- **Treant:** an average below 20 does not show that every run fell on the first linear segment. Because of zero-score clipping and the second segment, inverting the scale directly is unsound. Let C = 20 + 60(92304−88189)/(330195−88189), approximately 21.02022. For each reachable per-run original score s, the repaired score lies between 100s/C and min(100,100(1951+4141s)/88886). The lower chord lies below both linear segments and permits zero at the clipped endpoint; the upper affine line lies above both segments and above the clipped endpoint. Averaging preserves the affine inequalities. We apply the lower bound to max(0,published−0.05) and the upper bound to min(C,published+0.05). These conservative bounds need neither raw scores nor an assumption that all runs occupy the same segment. They use the documented upper bound of 92,304 and do not assume the cap can be reached.
- **Rounding:** each kept task's one-decimal score is enclosed by ±0.05, clipped to its score domain, and this uncertainty is carried through the mean.

## Does this certify the model order?

If the higher model's lower endpoint is above the lower model's upper endpoint, their order is certified under the stated assumptions. If the outer intervals overlap, these bounds cannot certify the order. That does not show a reversal is possible, because the individual maxima may be unattainable or incompatible with one another.

The documented-limit column uses only the 10 bounded effects and counts the 19 direction-only (open) effects as zero, so an order it certifies holds only if those 19 fixes have no effect on the score. The full-domain column lets the open effects span their stated directions; in that envelope every neighbouring pair overlaps, so no order is certified.

| Neighbouring models in published order | Certified by documented limits, with the 19 direction-only effects counted as zero? | Certified within the full-domain envelope? |
| --- | --- | --- |
| Opus 4.8 > GPT-5.5 | No; overlap does not establish reversal | No; overlap does not establish reversal |
| GPT-5.5 > GPT-5.4 | Yes, only if the 19 direction-only fixes have no effect | No; overlap does not establish reversal |
| GPT-5.4 > GLM-5.1 | Yes, only if the 19 direction-only fixes have no effect | No; overlap does not establish reversal |
| GLM-5.1 > DS-V4-Pro | Yes, only if the 19 direction-only fixes have no effect | No; overlap does not establish reversal |

## Portfolio sensitivity is separate from a proved limit

The saved decimal sweep covers only N=242 or 243 shared dates and strategy period returns from −30% to +100%. Its largest sampled joint rise is 0.3913; its sampled envelope with risk-measure and rounding slack is 0.3921. The sampled fall is 0.10. We show a separate scenario assuming +0.3921/−0.10 applies to the hidden submissions. Neither the grid nor Lean establishes this as a global bound. Lean proves the order and sign of the excess values for a fixed benchmark and exponent under domain hypotheses. It does not prove the ordering of total scores or the size of the score change. The details are in [the case](cases/portfolio_risk_calibration.md) and the [saved sweep](repairs/portfolio_risk_calibration-v2/paired/bound.out).

## Every repaired or removed task

| Task | Effect assumption and evidence | Classification | Per-task limit or scenario |
| --- | --- | --- | ---: |
| [apple_incremental_game](cases/apple_incremental_game.md) | up: on the publisher's 4-CPU grader, cases using ~15–30 s CPU scored 0 and deadline-based solvers got half the CPU; size needs regrading or new runs | open | — |
| [arc_compiler_runtime](cases/arc_compiler_runtime.md) | up: the fix only documents the required interface, so its effect depends on how agents respond; measurable only by new runs | open | — |
| [borden_source_inversion](cases/borden_source_inversion.md) | scale ×100/109 applied with published rounding uncertainty; up for good-faith fits once the convention is documented (24 raw points for a one-shot fit; less for agents that iterate on the grader's feedback) | open | — |
| [college_english_exam_bank](cases/college_english_exam_bank.md) | down: incomplete grader assessments over-credit | open | — |
| [cta_risk_budget_optimization](cases/cta_risk_budget_optimization.md) | v2.1 (shipped): up to the 5-point overseas-ratio component (4 of 80 raw) in either direction; three native paired runs through the original eval_cmd (58.75→53.75, 66.25→71.25). Historical FX-only proof applies to the previous denominator. | bounded | +5/−5 |
| [dabic_gravity_inversion](cases/dabic_gravity_inversion.md) | excluded, removed from the mean | excluded | — |
| [equivalence_class_divide_and_conquer](cases/equivalence_class_divide_and_conquer.md) | down, only for outputs inside the acceptance window; at most 9.67 points if every large official input falls in it | bounded | −9.67 |
| [exchange_core_throughput](cases/exchange_core_throughput.md) | down: incorrect engines can get full credit | open | — |
| [ffmpeg_swscale_reimplementation](cases/ffmpeg_swscale_reimplementation.md) | down: incomplete libraries over-credited (18.9 points shown) | open | — |
| [git_rewrite_in_zig](cases/git_rewrite_in_zig.md) | up, only for runs the original zeroed for a leftover build file or a git call in src/ (up to the whole run's score); how often real runs tripped a check is unknown | open | — |
| [graph_node_classification](cases/graph_node_classification.md) | either: a good-faith run whose prediction file is keyed by integer node IDs scores 0 under the original verifier and moves up under the fix (neighbor_intkeys: 0 to 24.089 of 100). A run that violates the output contract (non-numeric or missing predictions, or keys that collide under str()) was scored by the original and moves down. Under best-so-far selection the added variance can raise a run's score (a general lemma). None of the real runs we regraded was integer-keyed, and no gain for a real solver was established | open | — |
| [grid_turing_robot](cases/grid_turing_robot.md) | up: on the publisher's 4-CPU grader, solutions using ~15–30 s CPU per case were voided and deadline-based solvers got half the CPU; size needs regrading or new runs | open | — |
| [integer_compression_codec](cases/integer_compression_codec.md) | either: raw results were understated by a factor that depends on the submission (2.4 and 3.7 for two real submissions, 7–9 for a simple correct codec), and the fixed 0–100 scale runs from the starter (1.0) to the formula maximum (320). A real run's recorded best, 75.72, becomes 53.95 for its best submission on the fixed grader (second regrade of all 37 submissions; the first regrade, of the recorded best submission alone, gave 66.31 on the original grader and 50.08 on the fixed one) | open | — |
| [jagua_nesting_optimization](cases/jagua_nesting_optimization.md) | either: down for layouts with overlaps and for forbidden rotations; up only in the constructed swim_cr leniency case, where the original's edge-crossing test rejects a near-touching layout that the fixed area test accepts (seed_shift_wrongdeg: 0 → 0.186857 raw); unchanged for valid layouts | open | — |
| [juliet_vulnerability_analyzer](cases/juliet_vulnerability_analyzer.md) | up, only for submissions that report CWE-78 findings with source = sink and trace [sink], the form of all 38 public answers: +600/241 = 2.49 for complete detection with every other trace accepted (measured 97.51 → 100.00), +15.00 for a CWE-78-only analyzer (measured 45.66 → 60.66); at most 6380/241 ≈ 26.473029 (conservatively bounded by 26.474) when the change lifts trace quality across the 0.60 cap (exact, from score.py:163-176; computed, not run) | bounded | +26.474 |
| [lean_analysis_proofs](cases/lean_analysis_proofs.md) | either: scored set changes from 2901 to 2338 targets | open | — |
| [molecular_self_assembly](cases/molecular_self_assembly.md) | up: on the publisher's 4-CPU grader, cases using ~15–30 s CPU scored 0 and deadline-based solvers got half the CPU; size needs regrading or new runs | open | — |
| [openrct2_theme_park_ai](cases/openrct2_theme_park_ai.md) | either: the game is scored after about 68 game days instead of the promised ~4 years | open | — |
| [openttd_transport_ai](cases/openttd_transport_ai.md) | up: prompt-following scripts die at the named call | open | — |
| [order_addition_permutation_optimization](cases/order_addition_permutation_optimization.md) | up: later improvements ignored when the run keeps its best by pass rate; seen in a real run (3.79 kept instead of 41.24) | open | — |
| [pfr_formalization](cases/pfr_formalization.md) | up, new runs only: rule arithmetic allows 1.18 points for five targets and at most 2.13 with four downstream targets. The five actual targets were not proved, so component controls and inferred upstream dependencies support only a conditional limit, not a measured recovery. | bounded | +2.13 |
| [portfolio_risk_calibration](cases/portfolio_risk_calibration.md) | Sensitivity assumption only: +0.3921 / −0.10 from a finite sweep at N=242/243, strategy return −30% to +100%; largest sampled joint rise 0.3913. No proved bound for all valid submissions. | sensitivity | +0.3921/−0.1 |
| [rust_multicrate_reconstruction](cases/rust_multicrate_reconstruction.md) | up: two packages' hidden tests do not compile and score 0 for every run that leaves the tests unchanged (cas-search 12 points, cas-cli 10), and stopping at the first failing test file can cost up to 7.22 more, for a total of at most 29.22 (28.42 when cas-mux crashes, as it did for every complete solution measured). We measured +20.71 for a complete solution (73.99 to 94.70) in the publisher's inferred grading environment (the original grader plus four restored library files, which reproduces the publisher's starter score exactly). Down by at most 0.10 from the stricter exemption | bounded | +29.22/−0.1 |
| [schemathesis_config_modernization](cases/schemathesis_config_modernization.md) | either: one weak test item; a wrapper loses up to 0.625 points and a partly passing correct decorator gains up to 0.625 | bounded | +0.625/−0.625 |
| [schemathesis_datagen_pipeline](cases/schemathesis_datagen_pipeline.md) | down: one weak test item | bounded | −1.03 |
| [schemathesis_reporting_observability](cases/schemathesis_reporting_observability.md) | either: two weak test items. A submission can lose up to 4.76 points (wrong report writer and wrong coverage output). Good-faith work can gain up to 2.76 (a correct report writer whose suite has another name, plus coverage tests). A rise reaches 4.76 only if a submission makes the `GeneratedValue` class that the original coverage tests import unimportable, so we use 4.76 as the bound in both directions | bounded | +4.76/−4.76 |
| [smt_solver](cases/smt_solver.md) | up: correct witnesses rejected (ceiling 72.40 → 78.61) | open | — |
| [treant_forest](cases/treant_forest.md) | Scale interval from rounded average, allowing zero-score clipping and second-segment runs; no exact inversion from the public mean. | scale | — |
| [tree_block_partitioning](cases/tree_block_partitioning.md) | up, only for programs that multiply a value by itself in place (`v *= v`) | bounded | +5 |
| [triangulation_coloring_optimization](cases/triangulation_coloring_optimization.md) | either: a different flip rule; also up for solutions voided by the CPU share on the publisher's 4-CPU grader, where deadline-based solvers got about half a CPU | open | — |
| [vibrating_path_graph_coloring](cases/vibrating_path_graph_coloring.md) | up: on the publisher's 4-CPU grader, solutions using ~14–30 s CPU per case got no score and deadline-based solvers got half the CPU; size needs regrading or new runs | open | — |
| [warehouse_forklift_routing](cases/warehouse_forklift_routing.md) | up: runs over 60 s on any input, or over about 30 s of CPU per input on the publisher's 4-CPU grader, were voided, and deadline-based solvers got about half a CPU; ceiling ≈30.6 (30.3 before display rounding) | bounded | +30.586 |

## Evidence and limits

The publisher normalizes each run's score, keeps its best submission and averages the valid runs, as [the scoring-method record](evidence/impact/edgebench-scoring-method.md) describes. The scale intervals keep that set of runs, and they do not simulate how agents respond to new instructions or feedback.

We separately regraded third-party four-hour Opus 5.5 runs ([the saved regrade summary](evidence/runs/opus55-regrade2-summary/summary.json)). They show that some defects matter in real agent runs, but they are not a regrade of this twelve-hour leaderboard. The audit covers only the 51 public tasks; the publisher also has 83 unreleased tasks. The repairs form a new version of the benchmark.
