# Publication red team 3: case-page claims vs. evidence

Reviewer: Claude (adversarial publication review), 2026-10-12. Scope: good-faith claims on 18 case
pages. Pages reviewed: portfolio_risk_calibration, rust_multicrate_reconstruction,
schemathesis_config_modernization, schemathesis_datagen_pipeline,
schemathesis_reporting_observability, smt_solver, sphere_eversion_formalization, treant_forest,
tree_block_partitioning, triangulation_coloring_optimization, trinity_text_adventure,
tryst_text_adventure, vehicle_routing_time_windows, vibrating_path_graph_coloring,
vliw_kernel_optimization, warehouse_forklift_routing, wesnoth_tactical_ai and
wireless_electricity_layout.

Method: I checked every quantitative or causal claim against the saved evidence. The sources were
the reviews, the repair READMEs and `paired/results.md` / `raw-summary.md` files,
`evidence/runs/*/result/out`, the script outputs under `evidence/scripts/`, the TLC `.out` files,
the Lean `.out` files and `decisions.json`. I made no new runs and changed no decisions. I edited
only the case pages.

## Counts

| Class | Claims |
| --- | ---: |
| SUPPORTED | about 290 (not listed one by one) |
| OVERSTATED | 13 |
| UNSUPPORTED | 10 |
| CONTRADICTED | 7 |
| Edits made | 30 sentence edits on 15 pages |

Three pages needed no edit: tree_block_partitioning, triangulation_coloring_optimization and
trinity/tryst. Their claims trace to `direct-results.txt`, `native-results.txt`, the TLC outputs,
the review tables, the paired results and `_game-tasks-correctness.md` §1-3.

## Non-SUPPORTED claims

| Page | Original text | Class | Evidence | Edit made |
| --- | --- | --- | --- | --- |
| portfolio_risk_calibration | "The gap in the excess value itself is at most about 0.56 percentage points." | CONTRADICTED | `evidence/scripts/portfolio_risk_calibration/sensitivity.out`: diff_pp = −0.713 at a=−0.30 and −0.543 at −0.20; 0.557 is the maximum only for a ≥ 0. Scores at a ≤ 0 are at the −10 floor in both formulas. | Scoped it to 0% to +100% and added the 0.71 pp value at −30%. |
| portfolio_risk_calibration | "differ by under 0.6 percentage points" (Note for users) | CONTRADICTED | Same `sensitivity.out` lines | Changed to "at most about 0.7 percentage points for agent returns from −30% to +100% (under 0.6 points from 0% upward)". |
| rust_multicrate_reconstruction | "Host cargo 1.95.0 gave the same outcomes." | UNSUPPORTED | Only the review says this (line 102). `out/run.log` and `out/results.json` record only cargo 1.88.0, and nothing in the repo mentions "1.95". | Now attributed to the reviewer, with a note that the output is not saved. |
| schemathesis_config_modernization | "The only observable differences are `decorated is original` and the presence of `__wrapped__`." | OVERSTATED | The review (line 54) says only "I found no task-relevant behavior…". It shows no exhaustive comparison. | "The only differences the reviewer found are…" |
| schemathesis_config_modernization | "All 132 original items keep their v1 outcome." | CONTRADICTED | `paired/raw-summary.md`: for wrapper, `test_phase_3` PASSED->FAILED | Now says the wrapper's `test_phase_3` item flips and the other 131 original items keep their v1 outcome. |
| schemathesis_datagen_pipeline | "`test_http_date_values_grammar` is the only test whose result changes. All other 98 items are unchanged." | CONTRADICTED | `evidence/runs/schemathesis_datagen_pipeline-v2-paired-b/result/out/summary.md`: `test_phase_1` PASSED->FAILED for garbage_shape, independent_fields and off_by_one_clock | Now mentions the `test_phase_1` flip and says "97" other items. |
| schemathesis_datagen_pipeline | "v2 differs from v1 only for submissions whose `http_date_values` emits invalid dates or clock times." | OVERSTATED | The property test is randomized. With 50 examples a rare defect was caught in 15/20 seeds (`observed_seed_sweep.txt`). With 200 examples, 20/20 were caught for only the two tested generators. | Added "that the test's 200 sampled examples hit". |
| schemathesis_reporting_observability | "The only changed items are the JUnit test and the two former deny-only coverage tests…" | CONTRADICTED | `repairs/schemathesis_reporting_observability-v2/paired/raw-summary.md`: `test_phase_2` / `test_phase_5` PASSED->FAILED for the three fullref mutants | Added the phase summary items. |
| smt_solver | "The public dev set also contains 2 unwinnable sat cases." | UNSUPPORTED | Only the review asserts it (line 130). `results/` holds hidden-corpus scans only. | Now attributed to the review, with a note that no dev-set scan output is saved. |
| sphere_eversion_formalization | "Each is BAD only because it depends on a sorried theorem, so honest proofs of those theorems leave it unchanged." | OVERSTATED | `probe_summary.txt`: 97 of the 119 aux targets have a `def` parent, not a theorem. No honest-proof variant was scored (`lean_family_aux_census.md`:181,196). | Changed to "parent declaration" and "should leave it unchanged". Noted that this is a probe inference with no scored test. |
| sphere_eversion_formalization | "They are earned automatically once their dependencies are proved." | OVERSTATED | Same | Now says "By the probe, they should be earned…; this was not tested by scoring." |
| treant_forest | "the 20-80 and 80-100 bands of the scale are unreachable by any submission" | CONTRADICTED | `check_arith.out.json`: rescaled cap 21.0202, so 20–21.02 is reachable | Now says "every normalized score above 21.02 (nearly all of the 20-80 band and the whole 80-100 band)". |
| treant_forest | "the best honest per-case result was 47% of that case's cap" | UNSUPPORTED | `paired/result/out/eval_v1_honest_greedy.txt` has per-case scores, but the per-case N (cap 2N²) is not saved. I could not recompute it. | Now says "reported as 47%", with a note that the caps are not saved. |
| vehicle_routing_time_windows | 282,800 node pairs with 0 mismatches; the 12.05/11.95 vs 4.05/3.95 tolerance behaviour; the integer-field claim | UNSUPPORTED (3 claims) | `exact_checks.py` exists, but its output is not saved. There is no review file, and the triage record is internal. 282,800 = 56 × C(101,2) is at least arithmetically consistent. | Noted on the oracle bullet that the output is not saved. |
| vehicle_routing_time_windows | "Binary64 drift is at most 1.13e-11" | OVERSTATED | It is the maximum over 20,000 random 120-term trials, not a bound (`exact_checks.py`:99). The output is also not saved. | "The largest binary64 drift seen in the 20,000 random trials was 1.13e-11". |
| vehicle_routing_time_windows | `reproductions/vrptw-instruction-clarification/` cited twice as evidence | UNSUPPORTED | No `reproductions/` directory in the repository | Marked "not included in this repository" both times. |
| vehicle_routing_time_windows | "at most 286 raw points, 2.86%" | SUPPORTED (noted for the record) | eval_cmd: the per-case score is capped at 160 and final = mean × 100, so 160 × 100 / 56 = 285.7 | None |
| vibrating_path_graph_coloring | Decision: "a zero-hit answer is never valid on any official case" | OVERSTATED | `zero_hit_reachability.out`: EXACT 37, BOUND_ONLY 13. The 13 cases rest on a union bound under an assumed generator model. | Added "(proved for 37 of 50; overwhelmingly likely for the other 13…)". |
| vibrating_path_graph_coloring | "On all 50 official cases, the input graph cannot be K-colored without hits." | OVERSTATED | Same | Split into 37 proved and 13 with overwhelming probability. |
| vibrating_path_graph_coloring | Note: "On every official case a zero-hit answer is wrong anyway" | OVERSTATED | Same | Added the same scope. |
| vliw_kernel_optimization | Decision: "Honest submissions are scored correctly." | OVERSTATED | Only two controls were run (starter kernel and empty program), and no optimized kernel (page Limits). No run record is in the public repo. | "The two honest controls run were scored correctly." |
| vliw_kernel_optimization | "valid, 9/9 PASSED, cycles = 147734" (table) | UNSUPPORTED | No review, run directory or script output for this task in the repository | Noted that the run record is not included. |
| vliw_kernel_optimization | "a correct kernel receives its true cycle count" | OVERSTATED | One kernel was run, and its cycle count was not independently checked. | "the correct starter kernel received a valid cycle count" |
| vliw_kernel_optimization | Note: "Honest submissions are scored correctly on the original evaluator." | OVERSTATED | Same | Scoped to the two controls. |
| warehouse_forklift_routing | "The bound is therefore TOTAL ≥ 712.54" | CONTRADICTED (rounding direction) | `warehouse_lower_bound_lean.md`:89: the exact bound is ≈ 712.538131 < 712.54 | "TOTAL ≥ 712.538". |
| warehouse_forklift_routing | "an honest solver that spent 13 s per test case" | OVERSTATED | The trigger arm is a `sleep`-based time-budget control (page Limits; paired results). | "a time-budgeted control (it sleeps) that spent 13 s per test case" |
| warehouse_forklift_routing | "It records no task defect, and the hold is lifted." | CONTRADICTED (process) | `AGENTS.md` still lists "warehouse implementation" under holds. Only the reviewer's recommendation (`warehouse_forklift_routing.md`:155) supports "lifted". | Now says the reviewer recommended lifting the hold and notes that AGENTS.md still lists it. |
| wesnoth_tactical_ai | Decision: "the full evaluation fits its time budget (80–172 s against 900 s)" | OVERSTATED | One 8-vCPU host with no CPU limit and one run per configuration (`wesnoth_tactical_ai-native.md`:87-88) | Added "on one 8-vCPU host". |
| wesnoth_tactical_ai | "a full-length default-AI game takes about 3 s" | OVERSTATED | Same; the review says "refuted on this host" (line 68) | Added "on one 8-vCPU host". |
| wireless_electricity_layout | 200,000-history check: 0 normalized changes, 43,336 raw changes | UNSUPPORTED (output) | `normalized_invariance.py` exists, but no output is saved. `observed/` holds only the three judge logs. The analytic argument (review line 62) does support the 0-effect conclusion. | Noted that the output is not saved. |

## Spot checks that passed (selected)

- rust: the TLC outputs match the page (2,304 / 4,608 distinct states, and the counterexample
  `<<ok,ok,ok,FAILED>>, Ex={1}`). `results.json` matches the S1-S6 table.
- smt: `score_impact_output.txt` gives 78.606, 72.396 and 6.210. `scan_z3.jsonl` has all 27
  multi-context files as true=sat and checker=unsat. `scan_syntax.jsonl` has a maximum depth of 2621.
- wesnoth: `rca_games.jsonl` gives mean 2.858 s, median 2.785 s, maximum 5.65 s, 2 games with no
  winner, and 1 of 30 identical repeat pairs. The status files give 172 s and 80 s.
- datagen: in the paired-b re-run, `stdlib_any_year` is unchanged in v2 and the 20-seed sweeps match.
  `repair.patch` has `year < 1` and `max_examples=200`.
- tree_block: the native alias variant scores 1/10 with case 1 OK (0.25), and the TLC results match.

## Issues outside the edited pages (reported, not edited)

- `evidence/reviews/portfolio_risk_calibration.md` (line 73) and its recommended wording also say
  "at most about 0.56 pp anywhere in the range" and "under 0.6". `sensitivity.out` contradicts both
  at a = −0.30.
- `FINDINGS.md` and `DECISIONS.md` say "every valid TOTAL ≥ 712.54" for warehouse. The exact bound is
  712.538.
- `evidence/reviews/_game-tasks-correctness.md`:400 repeats the "20-80 band unreachable" wording for
  treant.
- `repairs/schemathesis_datagen_pipeline-v2/paired/results.md`:20 and
  `repairs/schemathesis_config_modernization-v2/paired/results.md`:16 say "only per-test difference
  … all other items unchanged". Their own `raw-summary.md` shows the phase-summary item flipping.

## Decisions

No decision changed. Two decisions deserve attention, but neither is clearly wrong:

- **warehouse_forklift_routing**: the repair rests on a paired run of work that `AGENTS.md` still
  lists as held ("warehouse implementation"). The coordinator should confirm whether the hold was
  formally lifted. The decision's science (TIME_LIMIT 60→150) is supported by the paired-b results.
- **vliw_kernel_optimization**: "retain with note" rests on two controls whose run record is not in
  the public repository. The decision is plausible, but the public evidence for it is thin.
