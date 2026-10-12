# Publication red-team 1: top-level docs and 16 case pages

Reviewer: Claude (adversarial publication review), 2026-10-12. Scope: good-faith claims only. No
decision was changed. Pages: `README.md`, `FINDINGS.md`, `METHOD.md`, `APPLYING-FIXES.md`, and
`cases/` for ad_placement_optimization, anchorhead_text_adventure, ann_vector_search_qps,
apple_incremental_game, arc_compiler_runtime, bipedalwalker_locomotion_rl, borden_source_inversion,
carleson_formalization, college_english_exam_bank, combinatorial_games_formalization,
cta_risk_budget_optimization, dabic_gravity_inversion, dcss_dungeon_ai,
equivalence_class_divide_and_conquer, exchange_core_throughput, ffmpeg_swscale_reimplementation.

Method: every number and every causal or universal claim was traced to `evidence/reviews/`,
`repairs/<id>-v2/` (README, `paired/results.md`, `source-lock.json`, `task-json.diff`, `repair.patch`),
`evidence/runs/<job>/result/`, `evidence/scripts/.../out`, `evidence/formal/` outputs,
`paired-results.csv` and `decisions.json`. Rescale values (ANN, DCSS, exchange log_max, Bipedal,
Apple, arc weights) were recomputed by hand.

## Counts

| Class | Claims |
| --- | ---: |
| SUPPORTED | about 160 (not tabulated individually) |
| OVERSTATED | 18 |
| UNSUPPORTED | 7 |
| CONTRADICTED | 10 |
| Edits made | all 35 non-supported claims fixed (34 page replacements, plus 2 generator strings mirrored) |

## Non-supported claims

| Page | Original text | Class | Evidence | Edit made |
| --- | --- | --- | --- | --- |
| README.md | "Every claim was reproduced on the task's original, digest-pinned evaluator" | OVERSTATED | Several claims rest on source reading or arithmetic only: `_game-tasks-correctness.md` Limits ("No native game was run here"), DCSS missing-morgue path not triggered (cases/dcss l.161), Carleson sorried def "not tested natively", Borden honest fits run on host Python (borden review l.146) | Reworded: checked against pinned sources, reproduced on the evaluator where feasible, case pages say which |
| README.md | "every material defect was repaired as a new task version" | CONTRADICTED | Dabic is excluded with only a partial repair (`decisions.json`) | "Every repaired defect ships as a new task version" |
| README.md | Retain with note = "Real but immaterial, or disclosed, issue" | OVERSTATED | FINDINGS "No defect affecting good-faith solvers" lists retain-with-note tasks (e.g. ad_placement "No good-faith defect") | Added "or a usage note only where no good-faith defect was found" |
| README.md | "every repair passed a paired before/after native run ([129 paired rows])" | CONTRADICTED | `repairs/openrct2_theme_park_ai-v2/paired/results.md`: "E2B paired job: Not run"; 4 of the 129 CSV rows are Dabic (excluded) | Scoped to "a native run for all but the prompt-only OpenRCT2 repair"; noted the 4 Dabic rows |
| README.md | Exchange bugs "score *higher* than the correct engine" | OVERSTATED | `exchange_core_throughput-native.md` l.108-115: one run per variant, "ranking ... is noise, not a speed effect" | "receive full throughput credit (in single runs ... higher ..., within throughput noise)" |
| README.md | "a Lean-proved lower bound also shows the top two score anchors are unreachable" | OVERSTATED | `warehouse_lower_bound_lean.md` l.161: "Model = original tester ... Not kernel-checked" (hand mapping + differential tests) | Added "for a model of the tester that was matched to the tester by testing, not by proof" |
| README.md | "(kernel-checked and independently recompiled)" | UNSUPPORTED | No recompile log anywhere in the repo; only the coordinator's statement on the warehouse case page | "kernel-checked; the coordinator's reported independent recompile has no saved log" |
| README.md | "Every Lean result lists its axioms (`propext`, `Classical.choice`, `Quot.sound` only)" | CONTRADICTED | `LeanAnalysisLocal.out`: `installed_*_inconsistent` depend on `sorryAx` (by design); `FinanceExcessFx.lean` has no `#print axioms` for `cta_native_passes`, `cta_cny_fails` | "Every main Lean result ...", with both exceptions named |
| FINDINGS.md (+ `tools/build_findings.py`) | "Every defect below was reproduced on the task's original, digest-pinned evaluator." | OVERSTATED | As for README; e.g. DCSS morgue rule and Bipedal ceiling are source/arithmetic (`_game-tasks-correctness.md` §4, §10) | Reworded with the source/arithmetic exception |
| FINDINGS.md | Exchange: "incorrect engines score higher than correct one \| 7.1→24.4 for a buggy engine" | OVERSTATED | Native review l.108-115 (noise); paired v1 control 2050/2210 vs feeswap 2269 | "receive full throughput credit (single runs scored above ..., within noise) \| full credit ... (7.1→24.4 in single runs; the gap ... is throughput noise)" |
| FINDINGS.md | Warehouse: "provably unreachable (Lean-checked lower bound ...)" | OVERSTATED | `warehouse_lower_bound_lean.md` l.161 | "unreachable (Lean-checked lower bound on a model of the tester, matched to the tester by testing ...)" |
| FINDINGS.md | Equivalence: "bounded (<0.04% over limit)" | CONTRADICTED | Excess ≤ \|N_last\| ≤ n = 10⁶ = exactly 0.04% of 2.5·10⁹ (equivalence review l.41; crafted star has \|N\| = n) | "≤0.04%" |
| METHOD.md | "every proof is reported with `#print axioms` (only propext, Classical.choice, Quot.sound)" | CONTRADICTED | Same as README Lean row | "every main proof", exceptions named |
| METHOD.md | Coordinator re-checked "for every published finding" | UNSUPPORTED | No record per finding; e.g. ad_placement footnote: README phrase "not re-located by the coordinator" | Re-check documented only where a page records it |
| METHOD.md | Repair "accepted only if, on the same inputs scored by ... v1 and ... v2 ... in one run" | CONTRADICTED | OpenRCT2 controls "Holds by construction ... Not re-run"; CTA "accepted, at component level" (`cta .../paired/results.md` l.41) | Added a sentence naming both narrower acceptances |
| APPLYING-FIXES.md (+ `tools/build_applying.py`) | "`paired/run.sh` reruns the paired evaluation (... 8-vCPU / 8 GiB workers) ... each repair fixes its trigger, keeps valid controls' scores ..." | OVERSTATED | `lean_analysis_proofs-v2/paired/` has only `run_local.sh` (local run); OpenRCT2 has no run script | Named both exceptions |
| cases/ad_placement_optimization.md | "no defect can mis-score an honest solver" | OVERSTATED | Review l.90: "No defect **found** can mis-score" | "no defect found can ..." |
| cases/ad_placement_optimization.md | "Any overlap with positive area is rejected, including ..." | CONTRADICTED | `micro/tester_results.tsv`: `noncontain_overlaps_earlier` scored 500000000 (accepted overlap) | Scoped to "when the later-indexed rectangle contains its own point"; pointed to the quirk |
| cases/arc_compiler_runtime.md | Local bun run "reproduced the earlier native starter result exactly" | UNSUPPORTED | No record in repo (the cited `_science-systems-triage.md` is absent); the native paired run (`hidden_v1_a_starter.log`) gives the same 167/448, 1057/2970, 35.59 | Noted the record is absent and the paired run gives the same values |
| cases/arc_compiler_runtime.md | constant one-diagnostic analyzer "scored 57.81" | UNSUPPORTED | Only in the absent triage | Added "triage record not included in this repository" |
| cases/arc_compiler_runtime.md | adversarial cases "(32% of weight)" | UNSUPPORTED | No weight table in repo; `case_inventory.py` needs the hidden dir | Added "per the earlier triage; not re-derived here" |
| cases/borden_source_inversion.md | independent model reproduces labels "to within 2.0e-15 relative" | OVERSTATED | Earlier-triage figure, not re-run; the saved in-image check `paired/evidence/label_check.txt` gives the judge's own model vs stored labels 8.9e-13 | Labelled as triage figure and added the saved 8.9e-13 check |
| cases/borden_source_inversion.md | footnote: "`release/DECISIONS.md` lists this repair as 'in progress'" | CONTRADICTED | No `release/` dir; `DECISIONS.md` l.17 says "accepted" | Footnote now says an earlier draft did; current records say accepted |
| cases/carleson_formalization.md | "Auxiliary-name defect: Refuted ... tested natively and rejected." | OVERSTATED | `lean_family_aux_census.md` l.177: carleson "Not tested natively, beyond the control" | "Not found"; rests on the probe and the control, with no honest proof scored |
| cases/carleson_formalization.md | 8 duplicate-type auxiliaries "not at risk" | OVERSTATED | `out/carleson_formalization/classify.txt`: "likely unattainable (+C dups): 8"; the probe says transitive-only; not tested by scoring | Gave both classifications; "not tested by scoring" |
| cases/carleson_formalization.md | "The upstream project completed its main theorem" | UNSUPPORTED | No evidence in repo; `classical_carleson` is BAD in the baseline listing (as expected for the starter) | "is reported to have ... (not checked here)" |
| cases/combinatorial_games_formalization.md | Decision: "Native tests show ... and that no target is out of reach" | OVERSTATED | Native honest test covers one module (census Limits l.196); "out of reach = 0" is the census lower bound | Split into one-module native test plus in-image census |
| cases/combinatorial_games_formalization.md | 33 duplicate-type auxiliaries "not at risk" | OVERSTATED | `classify.txt`: "likely unattainable (+C dups): 33"; probe-based reasoning | Gave both classifications and the scope of testing |
| cases/cta_risk_budget_optimization.md | "overseas exposure is undercounted about sevenfold" | OVERSTATED | The USD notional is undercounted ~7×; the checked share less so (1/3 vs 7/9, 0.175 vs 0.595) (cta review l.69-70, l.84-91) | "overseas (USD) notionals are undercounted about sevenfold" |
| cases/cta_risk_budget_optimization.md | "The proofs depend only on the standard axioms." | OVERSTATED | `FinanceExcessFx.out` prints axioms for 3 of the 5 CTA theorems | Scoped to the printed lists |
| cases/dabic_gravity_inversion.md | Bouguer-slab check "4.1931 vs 4.1934 mGal" | UNSUPPORTED | Script present, no saved output | Noted the output was not saved |
| cases/dabic_gravity_inversion.md | "v2 scores equal v1 scores for every submission classified as data-space ..." | OVERSTATED | Code-level claim; the measured data arm moved 26.82 → 26.84 (run noise), paired results l.27 | "By code reading, ... up to run noise (measured once ...)" |
| cases/equivalence_class_divide_and_conquer.md | "The excess is bounded (under 0.04%)" | CONTRADICTED | As FINDINGS row | "at most 0.04%" |
| cases/equivalence_class_divide_and_conquer.md | scores equal for true cost "≤ 2.5·10⁹ − \|N_last\| or > 2.5·10⁹ + \|N_last\|" | CONTRADICTED | v1 accepts iff true − \|N_last\| ≤ W, v2 iff true ≤ W, so they differ only on (W, W+\|N_last\|] (review l.39-41); the stated set leaves out the agreeing range (W−\|N_last\|, W] | "≤ 2.5·10⁹ or > 2.5·10⁹ + \|N_last\|" |
| cases/exchange_core_throughput.md | Decision: "incorrect engines were scored above the correct one" | OVERSTATED | Native review l.108-115 (noise) | "received full credit (in single runs they even scored above ..., within throughput noise)" |

## Checked and supported (selected)

ANN ±17% (875–1,222); DCSS rescale table (recomputed); Apple 17.7 (piecewise, rank30 262.5M);
Bipedal 2.5/10/18/30 (recomputed); arc 21 suites / 448 / 1057/2970, 128/128, `errors: 0` (paired logs),
v1 = v2 suite files byte-identical (cmp); Borden 7.03/31.2/12.9, 10.9–323×, 109, forward-model header-only
diff (`repair.patch`), agent_query section (`task-json.diff`); exchange log_max values recomputed
(7.14/24.40/15.62), 5+28 tests; CTA 32/1565, 14/17, 20.0 full-scorer; college-english paired table and
selection log; Dabic B+D maxima 12+30 = 42 (structured JSON), strong-tier totals (`penalty_check.txt`);
equivalence 35% (871,274,246), +5.17, 307/329; ffmpeg variant numbers and 14.91 dB (ffmpeg review);
combinatorial 16/3732 identical repaired sets (`native/report_{A,B}.json`); README earlier-audit counts
(18 withheld = 12 repaired + 6 retained-with-note; 7 new material defects = 10 repair/exclude tasks without
an earlier withhold, minus SMT, FFmpeg and OpenRCT2, which had earlier findings), checked against
`TASKS.md` at tag `earlier-audit-final`.

## Decisions questioned (not edited)

- **ad_placement_optimization and nine other tasks are "retain-with-note" but listed under "No defect
  affecting good-faith solvers".** This is a labelling inconsistency, not a wrong outcome. The README
  row now says so.
- **exchange_core_throughput: "Max effect 7.1→24.4" is a single-run noise artefact.** The repair
  decision stands, because incorrect engines get full credit. But `decisions.json` `max_effect`
  should state full credit, not the noise gap.

No repair, exclude or retain decision in this batch looked unsupported.

## Follow-ups for the coordinator

- `FINDINGS.md` table rows are generated from `decisions.json` `finding`/`max_effect`. The Exchange,
  Warehouse and Equivalence row edits made here will be reverted by `tools/build_findings.py` unless
  the same text goes into `decisions.json`/`decisions.csv`. The intro and `APPLYING-FIXES.md` edits
  were mirrored into the generators.
- `site/index.html` was not regenerated.
- `tools/check_consistency.py` currently reports 3 mismatches. These come from a concurrent
  `decisions.json` change for `git_rewrite_in_zig` (retain → retain-with-note), not from these edits.
