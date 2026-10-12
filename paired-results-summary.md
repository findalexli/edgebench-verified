# Paired before/after results: summary

This file summarizes [paired-results.csv](paired-results.csv). The CSV has 134 rows from the 23
`repairs/*-v2/paired/results.md` files: 22 accepted repairs plus the partial
`dabic_gravity_inversion` repair, which is **excluded** from the release. Row numbers below are CSV
line numbers; the header is line 1.

## How the CSV was built

- **Values are copied, never recomputed.** Markdown bold markers (`**`) were removed. A cell that
  holds a verdict or a composite status goes in `v1_result`/`v2_result`. When that cell also holds
  the arm's headline number, the number is copied into `*_score` as well (cta row 32,
  equivalence, integer_compression, tree_block, warehouse).
- **One primary score per arm.** Where a table has several score columns, the CSV uses one:
  - normalized for graph, treant and triangulation, where the repair is in the normalization or
    the run is invalidated;
  - raw everywhere else.
  - `score_kind` names the column. No table needed `pass_rate` as its primary score. For order,
    the test pass count is in `*_result`.
- **`changed`** compares the two scores when both exist, and otherwise the result and score
  together. It is literal: a valid control whose throughput or timing noise moved is
  `changed=yes`. One manual override: jagua row 71 is `accept` in both versions, and the v2 cell
  only adds an explanation.
- **Roles.**
  - An explicit label in the file wins.
  - An unlabeled shipped starter or baseline is `baseline`.
  - A ceiling anchor or setup-only arm is `setup`.
  - college J and K, which exercise the new re-ask path, are `trigger`.
  - lean T, S and W are `valid`, as honest proofs.
- **Latest table used.**
  - schemathesis_datagen_pipeline: the "Amendment 2026-10-12" table, not the original table.
  - warehouse_forklift_routing: the "Re-run after host restart" table, not the lost-job
    placeholder.
  - exchange_core_throughput and ffmpeg_swscale_reimplementation: each file contains one table,
    from the `-b` rerun, as its header states.
  - smt_solver: the corpus subset scores. These come from jobs `-b` and `-c`; `-c` reran
    `ground_wrong`.
- **Extra tables used where the main submission table has no trigger.**
  - jagua: section 1, the witnesses (rows 64–73), plus section 3, the full scorer (rows 74–76).
  - order: the selection table (rows 88–91), plus the paired table.
  - treant: one computed anchor endpoint, row 118. It is `score_rescale.py` output, not a
    submission run.
- **Not copied.**
  - Secondary tables: arc suite counts, dabic penalty check, equivalence direct checker, smt full
    `eval_cmd` and mini cases, triangulation rule-only and sample-loop tables, datagen seed sweep
    beyond the amendment column, and treant's other anchor rows.
  - openrct2 is a prompt-only repair with no paired scoring table. Its one row (83) holds the v1
    and v2 horizon statements, taken from prose.

## Per task

"Triggers changed" means every trigger row has `changed=yes`. "Controls as expected" uses the
expectation that the results.md file states for each control.

| Task | Trig | Valid | Inv | Other | Triggers changed | Valid as expected | Invalid as expected |
|---|---:|---:|---:|---|---|---|---|
| arc_compiler_runtime | 2 | 1 | 1 | 1 baseline | **no** (rows 5–6). This is a docs-only repair, and every score is identical by design. The defect is the gap between d (69.26) and e (35.59), which v2 fixes in TASK.md | yes (3) | yes (4) |
| borden_source_inversion | 0 | 3 | 2 | 1 baseline, 1 setup | n/a. No arm is labeled trigger. The repair adds `forward_model.py` and a rescale, and raw scores are identical | yes (7–9) | yes (12–13) |
| college_english_exam_bank | 7 | 4 | 1 | – | yes (18–22, 24–25) | yes (14–17) | yes (23) |
| cta_risk_budget_optimization | 2 | 3 | 1 | 1 baseline | yes (26–27), at component level only | yes (28, 29, 32) | yes (30) |
| dabic_gravity_inversion (excluded) | 1 | 1 | 1 | 1 baseline | yes (33) | yes (34). It moves 26.82→26.84, which the file attributes to run noise | yes (35). It is rejected only by `valid=false`; its score is not low |
| equivalence_class_divide_and_conquer | 1 | 2 | 1 | – | yes (37) | yes (38–39) | yes (40) |
| exchange_core_throughput | 2 | 3 | 2 | 1 setup | yes (45–46) | yes (42–44). These are OK in both versions, with large throughput noise | yes (47–48). The verdict is RE in v1 and WA in v2, so both versions reject them |
| ffmpeg_swscale_reimplementation | 3 | 2 | 1 | 1 baseline | yes (52–54) | yes (49–50), within timing noise | yes (55) |
| graph_node_classification | 1 | 3 | 1 | – | yes (59) | yes (56–58). Each moves by ≤0.008 normalized, from the timing penalty | yes (60) |
| integer_compression_codec | 1 | 1 | 1 | – | yes (61) | yes per file (62). It moves 0.8253→6.7024, which is the intended rescaling | yes (63) |
| jagua_nesting_optimization | 6 | 5 | 2 | – | yes (65–69, 72) | yes (64, 71, 73–75) | yes (70, 76) |
| lean_analysis_proofs | 1 | 4 | 1 | – | yes (78) | yes per file (77; 80–82). Scores change because of the intended denominator change and the removal of auxiliary credit | yes (79) |
| openrct2_theme_park_ai | 1 | 0 | 0 | – | yes (83), prompt text only | not run (holds by construction) | not run (holds by construction) |
| openttd_transport_ai | 1 | 2 | 0 | 2 baseline | yes (131): the shipped starter dies in v1 and not in v2. Added at the end of the CSV so earlier line numbers are unchanged | yes (133, 135). One judge serves both versions, so scores are identical by construction | n/a. No invalid arm; the v1 starter (132) is the crashing case |
| order_addition_permutation_optimization | 3 | 3 | 2 | – | yes (88, 90, 91) | yes (84, 85, 89) | yes (86–87). They have no score in either version; the pass count rises from 3/5 to 4/5 |
| schemathesis_config_modernization | 1 | 1 | 1 | 1 baseline | yes (94) | yes (93) | yes (95) |
| schemathesis_datagen_pipeline | 2 | 3 | 2 | 1 baseline | yes (99–100) | yes (96–98) | **no** in the strict sense. garbage_shape (101) is accepted by v1, at the same score as correct, and rejected only by v2; the file counts this as the fix. rfc850 (102) is rejected by both |
| schemathesis_reporting_observability | 4 | 2 | 1 | – | yes (105–107, 109) | yes with caveat. fullref (104) is unchanged; stub_junit_correct (108) gains +0.005, a documented caveat | **no** in the strict sense. The starter (110) rises from 0.020000 to 0.025000; the file says its body bug is now caught but documents the score gain |
| smt_solver | 2 | 1 | 1 | – | yes (111, 113) | yes (112) | yes (114) |
| treant_forest | 1 | 1 | 1 | 1 baseline | yes (118), a computed anchor and not a submission | yes per file (116). The raw score is unchanged and the normalized score moves only because of the new anchors | yes (117) |
| tree_block_partitioning | 1 | 1 | 1 | – | yes (120) | yes (119) | yes (121) |
| triangulation_coloring_optimization | 1 | 2 | 1 | – | yes (124) | yes (122–123), within 0.08 normalized | yes (125) |
| warehouse_forklift_routing | 2 | 1 | 2 | – | yes (129–130) | yes (126) | yes (127–128) |

## Totals (23 packages, 134 rows)

| Role | Rows | changed=yes | changed=no |
|---|---:|---:|---:|
| trigger | 46 | 44 | 2 (arc rows 5–6, docs-only) |
| valid | 49 | 17 | 32 |
| invalid | 27 | 8 | 19 |
| baseline | 10 | 2 | 8 |
| setup | 2 | 1 | 1 |

By score kind, 100 rows are `raw`, 21 are `verdict` and 13 are `normalized`.

**By task:**
- **Triggers.** 22 tasks have at least one trigger row, and in 21 of them every trigger changed.
  The exception is arc, a docs-only repair. borden has no trigger row.
- **Valid controls.** Every task with valid rows behaves as its file expects. 17 valid rows
  change, all of them noise or intended rescaling that the file documents.
- **Invalid controls.** 19 of the 21 tasks with invalid rows meet "rejected in both" strictly.
  The two exceptions are datagen garbage_shape and the reporting starter, both explained above.
- **Not run.** openrct2 has no executed controls.

## Verification

An automated re-read compared each CSV row with its own results.md: the arm, both results,
both scores and the source heading. All 134 rows pass after `**` is removed and whitespace is
normalized. 24 values match only after the bold markers are removed.

A stricter check required each value to sit on the arm's own line or on the next line. Only
openrct2 row 83 fails it, because its values come from wrapped prose rather than a table.
