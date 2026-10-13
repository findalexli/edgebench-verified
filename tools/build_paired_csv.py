import csv, sys
OUT = "data/paired-results.csv"

# (task, arm, role, v1_result, v2_result, v1_score, v2_score, kind, source)
R = []
def add(task, src, kind, rows):
    for r in rows:
        arm, role, v1r, v2r, v1s, v2s = r
        R.append([task, arm, role, v1r, v2r, v1s, v2s, kind, src])

# arc: Hidden raw SCORE; result = valid column
add("arc_compiler_runtime", "arc_compiler_runtime v2: paired results", "raw", [
 ("(a) shipped starter", "baseline", "true", "true", "35.59", "35.59"),
 ("(b) starter, `analyze()` returns `[]` (documented shape only)", "valid", "true", "true", "47.21", "47.21"),
 ("(c) invalid: codegen emits `var result = null;`", "invalid", "true", "true", "25.79", "25.79"),
 ("(d) independent honest analyzer, documented shape", "trigger", "true", "true", "69.26", "69.26"),
 ("(e) same analyzer as (d), starter shape `{ok,errors,warnings,program}`", "trigger", "true", "true", "35.59", "35.59"),
])

# borden: raw columns
add("borden_source_inversion", "borden_source_inversion-v2: paired results", "raw", [
 ("textbook ADE fit (review regression case)", "valid", "", "", "7.031", "7.031"),
 ("judge-convention fit (review, own re-implementation)", "valid", "", "", "31.200", "31.200"),
 ("v2 fit using only the shipped `forward_model.py`", "valid", "", "", "31.199", "31.199"),
 ("bound-midpoint baseline", "baseline", "", "", "7.012", "7.012"),
 ("hidden true source", "setup", "", "", "109.000", "109.000"),
 ("out-of-bounds answer (C0=5000, half_length_x=500)", "invalid", "", "", "4.000", "4.000"),
 ("no `answer.json`", "invalid", "", "", "0", "0"),
])

# college: result = valid flag, score = score
add("college_english_exam_bank", "Paired table", "raw", [
 ("A all 12 rules, one deduction each", "valid", "true", "true", "77", "77"),
 ("B all 12 rules floored to 0", "valid", "true", "true", "0", "0"),
 ("F R009 rule-level score 0, no checkpoints", "valid", "true", "true", "0", "0"),
 ("L A without any rule-level score (complete checkpoints)", "valid", "true", "true", "77", "77"),
 ("C empty `scores`", "trigger", "true", "false (grading failure)", "100", ""),
 ("D A minus R009", "trigger", "true", "false", "81", ""),
 ("E B minus R009", "trigger", "true", "false", "15", ""),
 ("G R009 row with no score and no checkpoints", "trigger", "true", "false", "0", ""),
 ("I R009 score 0 with all-zero checkpoints", "trigger", "true", "false", "15", ""),
 ("H no JSON", "invalid", "false", "false", "", ""),
 ("J D, then A on re-ask", "trigger", "true", "true", "81", "77"),
 ("K no JSON, then A on re-ask", "trigger", "false", "true", "", "77"),
])

# cta: composite verdict cells
src = "Paired v1/v2 results: cta_risk_budget_optimization"
add("cta_risk_budget_optimization", src, "verdict", [
 ("Trigger (synthetic)", "trigger", "violations 0/1; `cross_border` 1 (cost_fx 0) / 5 (cost_fx 2)", "violations 1/1; `cross_border` 0 / 1", "", ""),
 ("Trigger (real data)", "trigger", "violations 0/1; cb 1 / 5", "violations 1/1; cb 0 / 1", "", ""),
 ("Same-currency control", "valid", "0/1; cb 1 / 5", "0/1; cb 1 / 5", "", ""),
 ("Under-limit mixed control", "valid", "0/1; cb 1 / 5", "0/1; cb 1 / 5", "", ""),
 ("Invalid control (over the limit even natively)", "invalid", "1/1; cb 0 / 1", "1/1; cb 0 / 1", "", ""),
 ("Shipped reference positions (component)", "baseline", "violations 0/1565; cb 1 / 5", "violations 32/1565 (2.04%); cb 0 / 1", "", ""),
])
add("cta_risk_budget_optimization", src, "raw", [
 ("Full original scorer, complete shipped reference", "valid",
  "TOTAL_SCORE 20.0 (raw 16/80); M1 4, M2 0, M3 0 (\"Veto: annual vol 1.3% outside [5%,20%]\"), M4 2, M5 10; valid, pass_rate 1.0, exit 0",
  "identical: 20.0, the same metric breakdown, the same veto. Logs are identical apart from timings", "20.0", "20.0"),
])

# dabic (partial; excluded): score raw=norm, result = valid flag
add("dabic_gravity_inversion", "Paired v1/v2 results: dabic_gravity_inversion", "raw", [
 ("honest model-space D-ABIC (`FORM=\"model\"`)", "trigger", "true", "true", "25.77", "26.81"),
 ("honest data-space D-ABIC (`FORM=\"data\"`)", "valid", "true", "true", "26.82", "26.84"),
 ("data form, log-det via `np.linalg.det` (`make_invalid_variant.py`)", "invalid", "false", "false", "26.91", "26.86"),
 ("judge image's own workspace (no `outputs/`, nothing submitted)", "baseline", "false", "false", "0.00", "0.00"),
])

# equivalence: composite cells; score = raw extracted
add("equivalence_class_divide_and_conquer", "Paired v1/v2 results: equivalence_class_divide_and_conquer", "raw", [
 ("`naive.cpp` on crafted B (star, n=10⁶, m=2501; true cost 2.501·10⁹ > limit)", "trigger", "AC, raw 10 (T3 1/1)", "WA \"Operation cost exceeded\", raw 0", "10", "0"),
 ("`naive.cpp` on crafted A (m=2500; true cost exactly 2.5·10⁹)", "valid", "AC, raw 10", "AC, raw 10", "10", "10"),
 ("official `std.cpp` for T1–T6", "valid", "raw 100 / norm 100; T1 5/5, T2 10/10, T3 30/30, T4 25/25, T5 20/20, T6 30/30 (cases passed); exit 0; pass rate 1.000", "raw 100 / norm 100; identical per-subtask counts; exit 0; pass rate 1.000", "100", "100"),
 ("`naive.cpp` as T3, others empty, on the 30 official inputs", "invalid", "raw 1 / norm 1; T3 6 AC / 24 WA (cost exceeded); exit 1; pass rate 0.020", "raw 1 / norm 1; the same 6 AC / 24 WA, case by case; exit 1; pass rate 0.020", "1", "1"),
])

# exchange (-b run, only table in file)
add("exchange_core_throughput", "Paired results: exchange_core_throughput v1 vs v2", "raw", [
 ("unmodified engine, original image without artifacts (\"v1raw\")", "setup", "RE, 0", "—", "", ""),
 ("unmodified engine (control, run 1)", "valid", "OK 2050", "gate OK (33 tests), OK 2153", "2050", "2153"),
 ("unmodified engine (control, run 2)", "valid", "OK 2210", "gate OK, OK 2978", "2210", "2978"),
 ("`topo21` honest variant", "valid", "OK 2524", "gate OK, OK 2481", "2524", "2481"),
 ("`feeswap` (fee swap, balance kept at zero)", "trigger", "OK 2269", "WA 0 (gate failed)", "2269", ""),
 ("`dropevents` (user events not forwarded)", "trigger", "OK 2234", "WA 0 (gate failed)", "2234", ""),
 ("`feeleak`", "invalid", "RE 0", "WA 0", "", ""),
 ("`compileerr`", "invalid", "RE 0", "WA 0", "", ""),
])

# ffmpeg (-b run, only table in file)
add("ffmpeg_swscale_reimplementation", "Paired results: ffmpeg_swscale_reimplementation v1 vs v2", "raw", [
 ("forwarding shim, each frame once (`ref_r1`)", "valid", "", "", "0.967353", "0.980056"),
 ("forwarding shim, each frame twice (`ref_r2`, about 2× slower)", "valid", "", "", "0.509049", "0.507032"),
 ("shipped scaffold", "baseline", "", "", "0.447819", "0.012416"),
 ("errors on 3:1 downscale", "trigger", "", "", "2.881761", "0.000464"),
 ("silent no-op on 3:1 downscale", "trigger", "", "", "2.884506", "0.000463"),
 ("errors on RGBA→RGB24", "trigger", "", "", "1.305860", "0.000451"),
 ("unsupported yuv420p→rgb24", "invalid", "0.0 (28/30)", "0.0 (28/30)", "0.0", "0.0"),
])

# git: reward 0-1 (score = reward x 100); result = tests passed ("–": tests ran, reward ignores them)
add("git_rewrite_in_zig", "Paired table", "raw", [
 ("`control`: unmodified starter", "baseline", "2", "2", "0.000069", "0.000069"),
 ("`zig_build_exe`: starter after `zig build-exe src/main.zig -lc -lz` (leaves `main`, `main.o`)", "trigger", "–", "2", "0.0", "0.000069"),
 ("`obj_only`: as above, only `main.o` left", "trigger", "–", "2", "0.0", "0.000069"),
 ("`elf_only`: as above, only `main` left", "trigger", "–", "2", "0.0", "0.000069"),
 ("`exec_git`: `test` block in `src/main.zig` runs system git (`zig test` passes 1/1)", "trigger", "–", "2", "0.0", "0.000069"),
 ("`exec_git_helper`: `src/difftest.zig` helper runs system git, used only by a `test` block (`zig test` passes 1/1)", "trigger", "–", "2", "0.0", "0.000069"),
 ("oracle: real git v2.47.0 in `zig-out/bin`, `HARBOR_ORACLE_MODE=1`", "valid", "29,075", "29,075", "1.000000", "1.000000"),
 ("`bad_wrap_cgit`: `main.zig` execs `./cgit`, a C git v2.47.0 in the project folder", "invalid", "–", "0", "0.0", "0.0"),
 ("`bad_shell_git`: `main.zig` forwards every call to the system `git`", "invalid", "2", "2", "0.000069", "0.000069"),
 ("`bad_shell_git_oneline`: the same, with `\"git\"` on the `std.process.Child` line", "invalid", "–", "2", "0.0", "0.000069"),
])

# graph: Normalized 0-100; result = harness valid
add("graph_node_classification", "Paired table", "normalized", [
 ("baseline (shipped solution.py)", "valid", "true", "true", "29.278", "29.270"),
 ("neighbor (honest neighbour-vote solver, int ids)", "valid", "true", "true", "24.100", "24.104"),
 ("nanconf (baseline predictions, NaN confidences)", "valid", "true", "true", "27.147", "27.143"),
 ("shrink (one real prediction, rest `\"x\"`)", "trigger", "true", "false", "16.026", ""),
 ("missing_half (half the test nodes)", "invalid", "false", "false", "", ""),
])

# integer compression
add("integer_compression_codec", "Paired v1/v2 results: integer_compression_codec", "raw", [
 ("shipped Varint starter (unchanged)", "trigger", "0.2327 / 0.2327", "0.9786 / 0.9786 (repeat 1.0155)", "0.2327", "0.9786"),
 ("delta + zigzag + varint", "valid", "0.8253 / 0.8253", "6.7024 / 6.7024 (repeat 6.9708)", "0.8253", "6.7024"),
 ("starter with one corrupted value", "invalid", "0 / 0", "0 / 0", "0", "0"),
])

# jagua: witnesses (trigger evidence) + full scorer
add("jagua_nesting_optimization", "1. Witnesses (`validate_solution` of each image; `witnesses_v1.txt`, `witnesses_v2.txt`)", "verdict", [
 ("valid_adjacent_squares (shared edge)", "valid", "accept", "accept", "", ""),
 ("coincident_squares", "trigger", "accept", "reject `overlap_0_1`", "", ""),
 ("half_slid_squares", "trigger", "accept", "reject", "", ""),
 ("rect_inside_square", "trigger", "accept", "reject", "", ""),
 ("triangle_inside_square", "trigger", "accept", "reject", "", ""),
 ("diamond_inside_square", "trigger", "accept", "reject", "", ""),
 ("diag_shift_squares (proper crossings)", "invalid", "reject", "reject", "", ""),
 ("tiny_overlap_1e-6 (relative overlap 1e-7)", "valid", "accept", "accept (below the 1e-6 relative tolerance)", "", ""),
 ("forbidden_rotation_90 (allowed [0])", "trigger", "accept", "reject `orientation_not_allowed_0`", "", ""),
 ("allowed_rotation_minus180 (allowed [0, 180])", "valid", "accept", "accept", "", ""),
])
add("jagua_nesting_optimization", "3. Full original scorer (TaskSpec `eval.sh`, `--network none`)", "raw", [
 ("Shipped baseline (candidate = reference)", "valid", "0 / 16 / 0", "0 / 16 / 0", "0.000000", "0.000000"),
 ("seed_shift (honest: same LBF, different PRNG stream)", "valid", "6 / 10 / 0", "6 / 10 / 0", "1.644419", "1.644419"),
 ("drop_last_item (one item missing)", "invalid", "0 / 16 / 0, all `demand_mismatch`", "0 / 16 / 0, all `demand_mismatch`", "0.000000", "0.000000"),
])
# jagua revision v2.1: original (v1) against the current fixed grader v2.1 (the superseded v2 arm is in results.md)
add("jagua_nesting_optimization", "Full original scorer (TaskSpec `eval.sh`, `--network none`)", "raw", [
 ("Shipped baseline (rev. v2.1)", "valid", "0 / 16 / 0", "0 / 16 / 0", "0.000000", "0.000000"),
 ("seed_shift (rev. v2.1)", "valid", "6 / 10 / 0", "6 / 10 / 0", "1.644419", "1.644419"),
 ("drop_last_item (rev. v2.1)", "invalid", "0 / 16 / 0", "0 / 16 / 0", "0.000000", "0.000000"),
 ("seed_shift_f32deg (honest: seed_shift with f32-derived angles)", "valid", "6 / 10 / 0", "6 / 10 / 0", "1.644419", "1.644419"),
 ("seed_shift_wrongdeg (every angle + 0.01°)", "invalid", "0 / 16 / 0: 8 `overlap`, 7 `out_of_strip`, 1 valid without improvement (case 0012, `gardeyn3`)", "1 / 15 / 0, 15 `orientation_not_allowed`", "0.000000", "0.186857"),
])
add("jagua_nesting_optimization", "Witnesses (`validate_solution` of each image)", "verdict", [
 ("f32_rot90_f64deg (allowed [0, 90, 180, 270])", "valid", "accept", "accept", "", ""),
 ("f32_rot180_f64deg (allowed [0, 180])", "valid", "accept", "accept", "", ""),
 ("f32_rot_minus90_f64deg", "valid", "accept", "accept", "", ""),
 ("f32_rot270_f64deg", "valid", "accept", "accept", "", ""),
 ("near_tol_rot_90.0009 (0.9 × the v2.1 tolerance)", "valid", "accept", "accept", "", ""),
 ("wrong_rot_90.002 (2 × the v2.1 tolerance)", "trigger", "accept", "reject `orientation_not_allowed_0`", "", ""),
 ("wrong_rot_90.01 (10 × the v2.1 tolerance)", "trigger", "accept", "reject `orientation_not_allowed_0`", "", ""),
 ("wrong_rot_45 (allowed [0, 90, 180, 270])", "trigger", "accept", "reject `orientation_not_allowed_0`", "", ""),
])

# lean: score raw (=normalized); result = repaired/targets
add("lean_analysis_proofs", "Paired table", "raw", [
 ("orig", "valid", "0/2901", "0/2338", "0", "0"),
 ("A (trigger + controls)", "trigger", "1/2901 (trans only)", "3/2338 (anti_symm, div, trans)", "0.000345", "0.001283"),
 ("BAD (invalid)", "invalid", "no score", "no score", "", ""),
 ("T", "valid", "26/2901 (15 parents + 11 aux)", "15/2338", "0.008962", "0.006416"),
 ("S", "valid", "26/2901 (15 + 11)", "15/2338", "0.008962", "0.006416"),
 ("W", "valid", "25/2901 (15 + 10)", "15/2338", "0.008618", "0.006416"),
])

# openrct2: prompt-only; only the trigger has v1/v2 values
add("openrct2_theme_park_ai", "Measured horizon and recomputation", "verdict", [
 ("Trigger: v1 states a false horizon, v2 states the measured one", "trigger", "~4 game years", "about 70 game days, a little over 2 game months", "", ""),
])

# order: paired table (raw; result = tests passed) + selection (trigger)
add("order_addition_permutation_optimization", "Paired table", "raw", [
 ("identity", "valid", "4/5", "5/5", "3.3e-09", "3.3e-09"),
 ("search", "valid", "4/5", "5/5", "0.0093733018", "0.0093733018"),
 ("badcost (misreported cost)", "invalid", "3/5", "4/5", "", ""),
 ("dup (not a permutation)", "invalid", "3/5", "4/5", "", ""),
])
add("order_addition_permutation_optimization", "Selection (task policy `pass_rate_first`, EdgeBench `select_best`)", "verdict", [
 ("identity, search", "trigger", "identity (3.3e-09), frozen on the first", "search (0.00937)", "", ""),
 ("search, identity", "valid", "search (0.00937)", "search (0.00937)", "", ""),
 ("dup, identity, search", "trigger", "identity (3.3e-09)", "search (0.00937)", "", ""),
 ("badcost, identity, search", "trigger", "identity (3.3e-09)", "search (0.00937)", "", ""),
])

# schemathesis config
add("schemathesis_config_modernization", "Paired v1/v2 results: schemathesis_config_modernization", "raw", [
 ("starter", "baseline", "0/15", "0/16", "0.031466", "0.031466"),
 ("identity", "valid", "15/15", "16/16", "0.135313", "0.135313"),
 ("wrapper", "trigger", "15/15", "15/16", "0.135313", "0.129063"),
 ("no_register", "invalid", "12/15", "12/16", "0.115313", "0.110313"),
])

# schemathesis datagen: Amendment table (latest); result = 20-seed sweep
add("schemathesis_datagen_pipeline", "Final paired run (year ≥ 1900 floor removed)", "raw", [
 ("correct", "valid", "", "", "0.477350", "0.477350"),
 ("stdlib_1900", "valid", "0/20", "0/20", "0.477350", "0.477350"),
 ("stdlib_any_year", "valid", "0/20", "0/20", "0.477350", "0.477350"),
 ("independent_fields", "trigger", "0/20", "20/20", "0.477350", "0.467094"),
 ("off_by_one_clock", "trigger", "0/20", "20/20", "0.477350", "0.467094"),
 ("garbage_shape", "invalid", "", "", "0.477350", "0.467094"),
 ("rfc850 (invalid)", "invalid", "", "", "0.467094", "0.467094"),
 ("starter", "baseline", "", "", "0.323504", "0.323504"),
])
# schemathesis datagen v2.1 (current fix): clean native rerun, original eval_cmd
add("schemathesis_datagen_pipeline", "v2.1 native rerun (2026-10-13, year ≥ 1900 restored)", "raw", [
 ("stdlib_1900 (`email.utils.format_datetime`, years 1900–9999)", "valid", "", "", "0.477350", "0.477350"),
 ("stdlib_any_year (same formatter, years 0001–9999)", "invalid", "", "", "0.477350", "0.467094"),
 ("garbage_shape (`999, 99 888 0000 99:99:99 GMT`)", "invalid", "", "", "0.477350", "0.467094"),
])

# schemathesis reporting
add("schemathesis_reporting_observability", "Paired v1/v2 results: schemathesis_reporting_observability", "raw", [
 ("fullref", "valid", "", "", "1.000000", "1.000000"),
 ("fullref_junit_drops_error", "trigger", "", "", "1.000000", "0.985714"),
 ("fullref_no_body_fix", "trigger", "", "", "1.000000", "0.991667"),
 ("fullref_always_suppress", "trigger", "", "", "1.000000", "0.983333"),
 ("stub_junit_correct", "valid", "", "", "0.091429", "0.096429"),
 ("stub_junit_drops_error", "trigger", "", "", "0.091429", "0.082143"),
 ("starter", "invalid", "", "", "0.020000", "0.025000"),
])

# smt: corpus subset scores (one per arm)
add("smt_solver", "Corpus: 69 scoped hidden files (verdict counts)", "raw", [
 ("ground", "trigger", "", "", "0.0", "0.9"),
 ("textual", "valid", "", "", "0.587", "0.587"),
 ("textual_true", "trigger", "", "", "0.587", "0.9"),
 ("ground_wrong", "invalid", "", "", "0.0", "0.0"),
])

# treant: normalized; result = cases OK; + computed anchor row
add("treant_forest", "treant_forest v2 paired evaluation", "normalized", [
 ("Shipped baseline (`0`, `-1`)", "baseline", "50/50 OK", "50/50 OK", "0.00", "0.00"),
 ("Honest greedy (grid-only maze lengthening)", "valid", "50/50 OK", "50/50 OK", "3.04", "16.36"),
 ("Invalid: treant on the revealed entrance", "invalid", "0/50 (all WA)", "0/50 (all WA)", "0.00", "0.00"),
])
add("treant_forest", "Anchor endpoints", "normalized", [
 ("92304 (= Σ 2N², the score cap)", "trigger", "", "", "21.02", "100.00"),
])

# tree block
add("tree_block_partitioning", "Paired v1/v2 results: tree_block_partitioning", "raw", [
 ("Official `std.cpp` for all six subtasks", "valid", "100 / 100", "100 / 100", "100", "100"),
 ("T2 = alias variant of `std.cpp` (`make_alias_variant.py`); T1, T3–T6 empty", "trigger", "0.25 / 0.25 (T2 1/10)", "5 / 5 (T2 10/10)", "0.25", "5"),
 ("T2 = `std.cpp` with the second merge factor dropped (`make_invalid_variant.py`); others empty", "invalid", "0.25 / 0.25 (T2 1/10, 9 WA)", "0.25 / 0.25 (T2 1/10, 9 WA)", "0.25", "0.25"),
])

# triangulation: normalized; result = cases OK
add("triangulation_coloring_optimization", "Full judge (`eval_cmd`, 10 hidden cases)", "normalized", [
 ("shipped `solution.py` (do nothing)", "valid", "10/10", "10/10", "0.055", "0.054"),
 ("`greedy.py` (greedy recolour + greedy README-legal convex flips)", "valid", "10/10", "10/10", "48.87", "48.95"),
 ("`nonconvex_flip.py` (do nothing + one README-forbidden non-convex flip per case)", "trigger", "10/10 accepted", "0/10 (WA \"Invalid flip\")", "0.052", ""),
 ("`wrong_count.py` (recolours vertex 1, claims C=0)", "invalid", "0/10 (WA)", "0/10 (WA)", "", ""),
])

# warehouse: Re-run after host restart (latest)
add("warehouse_forklift_routing", "Paired run", "raw", [
 ("generic valid control", "valid", "OK 50/50, TOTAL 46676.8", "OK 50/50, TOTAL 46676.8", "46676.8", "46676.8"),
 ("one honest bug", "invalid", "49 OK + 1 WA → inf", "49 OK + 1 WA → inf", "", ""),
 ("shipped starter", "invalid", "50 WA → inf", "50 WA → inf", "", ""),
 ("13 s per test case (uses the promised budget)", "trigger", "50 TLE → inf", "50 OK, TOTAL 46676.8", "", "46676.8"),
 ("near the 150 s per-input limit", "trigger", "50 TLE → inf", "50 OK, TOTAL 46676.8", "", "46676.8"),
])

# openttd (added last so earlier CSV line numbers stay stable): one judge for v1 and v2, so each
# submission scores the same under both; the trigger row compares the shipped starters.
add("openttd_transport_ai", "Paired table", "raw", [
 ("shipped starter (v1 work image vs v2 work image)", "trigger", "yes, at `main.nut` line 5", "no", "", ""),
 ("baseline_v1 (shipped starter)", "baseline", "yes, at `main.nut` line 5", "yes, at `main.nut` line 5", "0", "0"),
 ("probe_min (calls corrected API monthly)", "valid", "no", "no", "0", "0"),
 ("baseline_v2 (fixed starter)", "baseline", "no", "no", "0", "0"),
 ("probe_value (positive-value control)", "valid", "no", "no", "4975", "4975"),
])

# pfr (added after openttd so earlier CSV line numbers stay stable): every score is 0.0 because no
# real proof of the five targets was run; the trigger rows compare the status of the added lemmas.
src = "Paired table"
add("pfr_formalization", src, "raw", [
 ("starter", "baseline", "0/423", "0/423", "0.0", "0.0"),
])
add("pfr_formalization", src, "verdict", [
 ("T (trigger)", "trigger", "both BAD `unexpected=[sorryAx]`", "both OK `[propext, Classical.choice, Quot.sound]`", "", ""),
 ("D (downstream)", "trigger", "all three BAD `unexpected=[sorryAx]`", "all three OK", "", ""),
])
add("pfr_formalization", src, "raw", [
 ("BAD (bad control)", "invalid", "`app_ent_PFR` BAD, `ebv_bad_sorry` BAD", "`app_ent_PFR` BAD, `ebv_bad_sorry` BAD", "0.0", "0.0"),
])

# grid / molecular / warehouse CPU share (added last so earlier CSV line numbers stay stable). Score
# columns are left empty for grid and molecular: their results.md gives TOTAL with thousands separators,
# which is kept verbatim in the result columns.
add("grid_turing_robot", "grid_turing_robot v2: paired results", "raw", [
 ("`baseline_good` (no extra work)", "baseline", "50 OK, TOTAL 94,092 (19.80)", "50 OK, TOTAL 94,092 (19.80)", "", ""),
 ("`cpu12` (12 s CPU per case)", "valid", "50 OK, TOTAL 94,092", "50 OK, TOTAL 94,092", "", ""),
 ("`cpu16` (16 s CPU per case)", "trigger", "2 OK, 48 TLE, TOTAL inf (invalid)", "50 OK, TOTAL 94,092 (19.80)", "", ""),
 ("`cpu28` (28 s CPU per case)", "trigger", "2 OK, 48 TLE, TOTAL inf (invalid)", "50 OK, TOTAL 94,092 (19.80)", "", ""),
 ("`wall25` (works until 25 s wall clock)", "valid", "50 OK, TOTAL 94,092", "50 OK, TOTAL 94,092", "", ""),
 ("`spin40` (bad control, 40 s CPU per case)", "invalid", "0 OK, 50 TLE, TOTAL inf", "0 OK, 50 TLE, TOTAL inf", "", ""),
 ("`cpu20` (20 s CPU per case)", "valid", "50 OK, TOTAL 94,092", "50 OK, TOTAL 94,092", "", ""),
])
add("molecular_self_assembly", "molecular_self_assembly v2: paired results", "raw", [
 ("`baseline` (shipped baseline, no extra work)", "baseline", "50 OK, TOTAL 69,280,072", "50 OK, TOTAL 69,280,072", "", ""),
 ("`cpu12` (12 s CPU per case)", "valid", "50 OK, TOTAL 69,280,072", "50 OK, TOTAL 69,280,072", "", ""),
 ("`cpu16` (16 s CPU per case)", "trigger", "2 OK, 48 TLE, TOTAL 2,849,909", "50 OK, TOTAL 69,280,072", "", ""),
 ("`cpu28` (28 s CPU per case)", "trigger", "2 OK, 48 TLE, TOTAL 2,849,909", "50 OK, TOTAL 69,280,072", "", ""),
 ("`wall25` (works until 25 s wall clock)", "valid", "50 OK, TOTAL 69,280,072", "50 OK, TOTAL 69,280,072", "", ""),
 ("`spin40` (bad control, 40 s CPU per case)", "invalid", "0 OK, 50 TLE, TOTAL 0", "0 OK, 50 TLE, TOTAL 0", "", ""),
 ("`cpu20` (20 s CPU per case)", "valid", "50 OK, TOTAL 69,280,072", "50 OK, TOTAL 69,280,072", "", ""),
])
# warehouse at 4 CPUs: v1 = original grader, v2 = current fixed version (the earlier, limit-only fixed
# version gave 2 OK + 48 TLE -> inf for both arms; see results.md).
add("warehouse_forklift_routing", "CPU share at 4 CPUs (current fixed version, 2026-10-12)", "raw", [
 ("`cpu80` (80 s CPU per input)", "trigger", "50 TLE → inf", "50 OK, TOTAL 46676.8", "", "46676.8"),
 ("`cpu140` (140 s CPU per input)", "trigger", "50 TLE → inf", "50 OK, TOTAL 46676.8", "", "46676.8"),
])

# vibrating / apple / triangulation CPU share (added 2026-10-12, after rust in the CSV so earlier
# line numbers stay stable). v1 = original grader, v2 = fixed version, at 4 grader CPUs unless the arm
# ends in "| 8" (the 8-CPU row of the results.md table). Score columns are left empty where results.md
# gives TOTAL with thousands separators, which is kept verbatim in the result columns.
CPU_ROWS = []
CPU_ROWS.append(("vibrating_path_graph_coloring", "vibrating_path_graph_coloring v2: paired results", "raw", [
 ("`cpu0` (honest control alone)", "baseline", "50 OK, TOTAL 24,650,014 (2.06)", "50 OK, TOTAL 24,650,014 (2.06)", "", ""),
 ("`cpu20` (20 s CPU per case)", "trigger", "2 OK, 48 TLE, TOTAL inf (no score)", "50 OK, TOTAL 24,650,014 (2.06)", "", ""),
 ("`cpu28` (28 s CPU per case)", "trigger", "2 OK, 48 TLE, TOTAL inf (no score)", "50 OK, TOTAL 24,650,014 (2.06)", "", ""),
 ("`wall25` (works until 25 s wall clock)", "valid", "36 OK, 14 TLE, TOTAL inf", "50 OK, TOTAL 24,650,014", "", ""),
 ("`wall25`, repeat 1 / repeat 2", "valid", "50 OK, 24,650,014", "50 OK, 24,650,014", "", ""),
 ("`spin40` (bad control, 40 s CPU per case)", "invalid", "0 OK, 50 TLE, TOTAL inf", "0 OK, 50 TLE, TOTAL inf", "", ""),
 ("`cpu20` (20 s CPU per case) | 8", "valid", "50 OK, TOTAL 24,650,014", "50 OK, TOTAL 24,650,014", "", ""),
]))
CPU_ROWS.append(("apple_incremental_game", "apple_incremental_game v2: paired results", "raw", [
 ("`cpu0` (honest control alone)", "baseline", "50 OK, TOTAL 99,714,418 (5.04)", "50 OK, TOTAL 99,714,418 (5.04)", "", ""),
 ("`cpu20` (20 s CPU per case)", "trigger", "2 OK, 48 TLE, TOTAL 3,955,266 (0.00)", "50 OK, TOTAL 99,714,418 (5.04)", "", ""),
 ("`cpu28` (28 s CPU per case)", "trigger", "2 OK, 48 TLE, TOTAL 3,955,266 (0.00)", "50 OK, TOTAL 99,714,418 (5.04)", "", ""),
 ("`wall25` (works until 25 s wall clock)", "valid", "50 OK, TOTAL 99,714,418", "50 OK, TOTAL 99,714,418", "", ""),
 ("`spin40` (bad control, 40 s CPU per case)", "invalid", "0 OK, 50 TLE, TOTAL 0", "0 OK, 50 TLE, TOTAL 0", "", ""),
 ("`cpu20` (20 s CPU per case) | 8", "valid", "50 OK, TOTAL 99,714,418", "50 OK, TOTAL 99,714,418", "", ""),
]))
# triangulation: the original grader scores the original cases, the fixed version the regenerated ones,
# so valid totals differ (866,166 against 863,058), as in its existing rows.
CPU_ROWS.append(("triangulation_coloring_optimization", "CPU-quota parallelism (added 2026-10-12)", "raw", [
 ("`cpu0` (control alone)", "baseline", "10 OK, 866,166", "10 OK, 863,058", "", ""),
 ("`cpu20` (20 s CPU per case)", "trigger", "2 OK, 8 TLE, inf (no score)", "10 OK, 863,058 (48.95)", "", ""),
 ("`cpu28` (28 s CPU per case)", "trigger", "2 OK, 8 TLE, inf", "10 OK, 863,058", "", ""),
 ("`wall25` (works until 25 s wall clock)", "valid", "10 OK, 866,166", "10 OK, 863,058", "", ""),
 ("`spin40` (bad control, 40 s CPU per case)", "invalid", "10 TLE, inf", "10 TLE, inf", "", ""),
 ("`cpu20` | 8", "valid", "10 OK, 866,166", "10 OK, 863,058", "", ""),
]))

# rust: verbatim eval_cmd, score out of 100; v1 = original grader as shipped, v2 = fixed version.
# The middle image (original grader + the 4 cc files, the publisher's environment) is in results.md:
# starter 3.8189, reference/partial 73.9926, bad 73.8926 (data/README.md says so). The arms are the
# rows of the summary table at the top of the Results section.
add("rust_multicrate_reconstruction", "rust_multicrate_reconstruction v2: paired results", "normalized", [
 ("starter", "baseline", "", "", "1.4711", "5.7236"),
 ("reference", "trigger", "", "", "27.6091", "94.7022"),
 ("partial", "trigger", "", "", "27.6091", "93.9963"),
 ("bad", "invalid", "", "", "27.5091", "94.6022"),
])

for _t, _src, _kind, _rows in CPU_ROWS:
    add(_t, _src, _kind, _rows)

# portfolio (added 2026-10-13, after the CPU rows so earlier CSV line numbers stay stable).
# Full grader: score = TOTAL_SCORE out of 100; result = yearly excess return as the grader prints it.
# Installed functions on authored NAV paths: verdict rows; result = the excess part of the score (of 20).
add("portfolio_risk_calibration", "Full grader (`score.py`)", "raw", [
 ("(a) instructions' formula", "trigger", "3.44%", "3.47%", "32.45", "32.52"),
 ("(b) grader's formula", "valid", "3.44%", "3.47%", "32.45", "32.52"),
 ("(c) wrong", "invalid", "−21.14%", "−21.33%", "0", "0"),
 ("(d) starter", "baseline", "missing submission files: portfolio_optimizer.py",
  "missing submission files: portfolio_optimizer.py", "0", "0"),
 ("(e) image example", "baseline", "−9.28%", "−9.37%", "0", "0"),
])
add("portfolio_risk_calibration", "Near the 12% full-marks line (installed functions)", "verdict", [
 ("T1 instructions' formula gives exactly 12%", "trigger", "19.85", "20.00", "", ""),
 ("T2 original grader's formula gives exactly 12%", "valid", "20.00", "20.00", "", ""),
 ("T3 equal to the benchmark", "valid", "0", "0", "", ""),
 ("T4", "valid", "9.90", "9.98", "", ""),
 ("T5", "valid", "−4.43", "−4.47", "", ""),
])

# juliet (added 2026-10-13): score = the wrapper's `score` (linear 0-100); result = trace quality
# (share of true positives whose trace is accepted), or status for submissions with no findings.
add("juliet_vulnerability_analyzer", "Hidden grading (task `eval_cmd`)", "raw", [
 ("a78_public (public form)", "trigger", "0.0000", "1.0000", "45.66", "60.66"),
 ("a78_input (hidden form)", "valid", "1.0000", "1.0000", "60.66", "60.66"),
 ("a78_wrong (wrong source)", "invalid", "0.0000", "0.0000", "45.66", "45.66"),
 ("r_hidden", "valid", "1.0000", "1.0000", "100.00", "100.00"),
 ("r_public78 (public form)", "trigger", "0.8340", "1.0000", "97.51", "100.00"),
 ("r_sinkonly (wrong in other CWEs)", "invalid", "0.3237", "0.4896", "70.00", "70.00"),
 ("r_wrong78_tr", "invalid", "0.8340", "0.8340", "97.51", "97.51"),
 ("r_wrong78_src", "invalid", "0.8340", "0.8340", "97.51", "97.51"),
 ("starter", "baseline", "— (no findings)", "— (no findings)", "10.00", "10.00"),
 ("crash", "baseline", "`valid: false`", "`valid: false`", "10.00", "10.00"),
])
add("juliet_vulnerability_analyzer", "Public data (same `score.py`, public answers)", "raw", [
 ("a78_public", "valid", "1.0000", "1.0000", "51.17", "51.17"),
 ("a78_input", "valid", "0.0000", "0.0000", "36.17", "36.17"),
 ("a78_wrong", "invalid", "0.0000", "0.0000", "36.17", "36.17"),
])

# Grader CPU count (`docker run --cpus`) of the job that produced each row, from the job's run.sh
# (repairs/<task>-v2/paired/*.sh and evidence/runs/<job>/run.sh, or the per-arm `cpus=` field of the
# job's summary.txt). Empty where no run script states it or nothing ran.
TASK_CPUS = {
    "arc_compiler_runtime": 2, "borden_source_inversion": 2,   # Borden: grading at 2; fitting runs at 8
    "college_english_exam_bank": 2, "cta_risk_budget_optimization": 2, "dabic_gravity_inversion": 8,
    "equivalence_class_divide_and_conquer": 3, "exchange_core_throughput": 8,
    "ffmpeg_swscale_reimplementation": 4, "git_rewrite_in_zig": 8, "graph_node_classification": 4,
    "integer_compression_codec": 4, "jagua_nesting_optimization": 3, "lean_analysis_proofs": 2,
    "order_addition_permutation_optimization": 2, "pfr_formalization": 4,
    "schemathesis_config_modernization": 2, "schemathesis_datagen_pipeline": 2,
    "schemathesis_reporting_observability": 2, "tree_block_partitioning": 2, "treant_forest": 8,
    "portfolio_risk_calibration": 2, "juliet_vulnerability_analyzer": 2,
}
SOURCE_CPUS = {
    ("smt_solver", "Corpus: 69 scoped hidden files (verdict counts)"): 4,
    ("warehouse_forklift_routing", "Paired run"): 2,
    ("triangulation_coloring_optimization", "Full judge (`eval_cmd`, 10 hidden cases)"): 8,
}
CPU_SHARE = {"apple_incremental_game", "vibrating_path_graph_coloring", "triangulation_coloring_optimization",
             "grid_turing_robot", "molecular_self_assembly"}   # summary.txt: c4-* rows cpus=4, c8-* rows cpus=8


def cpus(task, arm, src, v1r):
    if src == "Anchor endpoints":   # Treant's score cap, computed, not run
        return ""
    if src.startswith("CPU share at 4 CPUs") and task == "warehouse_forklift_routing":
        return 4
    if (task, src) in SOURCE_CPUS:
        return SOURCE_CPUS[(task, src)]
    if task in CPU_SHARE and src != "Full judge (`eval_cmd`, 10 hidden cases)":
        if arm.endswith("| 8") or (task in ("grid_turing_robot", "molecular_self_assembly") and arm.startswith("`cpu20`")):
            return 8
        return 4
    return TASK_CPUS.get(task, "")


def changed(v1r, v2r, v1s, v2s):
    if (v1r, v2r) == ("accept", "accept (below the 1e-6 relative tolerance)"):
        return "no"  # same verdict; v2 cell only adds an explanation
    if v1s and v2s:
        return "no" if v1s == v2s else "yes"
    return "no" if (v1r, v1s) == (v2r, v2s) else "yes"

with open(OUT, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["task_id","arm","role","v1_result","v2_result","v1_score","v2_score","score_kind","changed","source","cpus"])
    for t, arm, role, v1r, v2r, v1s, v2s, kind, src in R:
        w.writerow([t, arm, role, v1r, v2r, v1s, v2s, kind, changed(v1r, v2r, v1s, v2s), src, cpus(t, arm, src, v1r)])
print(len(R))
