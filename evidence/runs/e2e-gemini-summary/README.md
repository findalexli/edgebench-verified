# End-to-end agent runs on the original and fixed tasks (Gemini 4 Argon, 2 h)

This sweep checks that every repaired task runs end to end under EdgeBench's own harness, and compares the
original task (v1) with the fixed one (v2). For each task it runs a real agent twice, once per version, with
the same agent, model and limits. Then every submission of both runs is graded with both judges, so each
comparison also has a paired form on identical inputs.

## Setup

- **Harness:** `sforge/` exactly as published (`sforge pull`, `sforge serve`, `sforge run --backend docker`),
  agent `opencode`, auto-eval every 300 s (EdgeBench's default), selection with each task's own policy.
- **Model:** `gemini-4-argon` on the Gemini API's flex tier, through a small proxy on the worker that adds the
  key and `serviceTier: flex` (`tools/flex_proxy.py`; every script of the sweep is in `tools/`). The agent never sees the key. Flex is
  cheaper and slower: calls took a median of 20–27 s, so an agent spends much of its time waiting.
- **Time:** 2 h of agent time per run (EdgeBench reports checkpoints from 2 h to 12 h).
- **Workers:** one E2B sandbox per run (`harbor-worker-v4-s99-25g`, 8 vCPU, 8 GiB, 30 GB disk). A sandbox on
  this account lives at most 1 h, so the controller (`e2e_run.py`) pauses and resumes it every 48 min; a
  pause takes about 6 s and every process keeps running. Each worker pulls the original images by tag; a v2
  worker then runs the repair package's `materialize.sh` and builds the fixed images under the names sforge
  derives from `task.json.in`, which replaces the task file.
- **Cross-grade:** `xg-<run>` jobs grade each archived submission with the original judge (the pinned digest
  in the repair's `Dockerfile`) and the fixed judge, one container at a time, `--network none --cpus 4
  --memory 6g`, the same method as `../qwen35-regrade-summary/`. Tasks whose repair does not change the
  judge image (arc_compiler_runtime, borden_source_inversion, openrct2_theme_park_ai, openttd_transport_ai,
  treant_forest) have no cross-grade; for them the two runs are the comparison.

## Deviations from the official settings, and their effect

- **Memory.** The official limits are 16 GB for the agent's container and 8 GB for the judge. A worker has
  8 GiB in all, so runs used 4 GB and 3 GB. Some judges need more: in the graph_node_classification v2 run,
  16 of 27 in-run grades failed with `BrokenProcessPool` (worker processes killed), while the same
  submissions all graded validly (0.29–0.62) in the 6 GB cross-grade. In-run scores of memory-heavy tasks are
  therefore lower bounds; the cross-grade is the fairer measure.
- **Network.** The original exchange_core_throughput judge downloads build files, so it scores every
  submission 0 under the cross-grade's `--network none` (the repair ships those files; see its README). For
  that task the v1 comparison uses the harness's in-run score, whose judge had network access.
- **Disk.** pfr_formalization's two images (10.5 + 11 GB) fit only after switching the worker's dockerd from
  the containerd image store (which keeps compressed layers too) to overlay2 (`DOCKER_OVERLAY2=1`).
  lean_analysis_proofs' judge image alone unpacks to about 33 GB and does not fit any worker available to
  this account, so it was not run.
- **Timing-dependent solvers.** Some agent solutions stop on a clock, so their score follows the machine's
  speed. In the tree_block_partitioning v1 run, in-run grades passed 52–180 of 7,200 cases across
  near-identical submissions, while the cross-grade gave 52 nearly every time under both judges. Compare
  the two judges within a cross-grade, not a cross-grade with an in-run score.
- **Time.** 2 h instead of 12 h, and one run per version. Differences between the two runs mix the effect of
  the fix with the agent's own run-to-run variation; the paired cross-grade separates the two.

## Files

- `e2e-gemini-s2h-<task>-<v1|v2>/`: one run. `params.env` and `run.sh` are the inputs; `result/worker.json` is the
  controller's record (`recovered: true` where the result was taken from a complete error-time snapshot);
  `result/summary.json` holds the harness's final result and token usage; `result/out/reports.jsonl` has one line
  per submission (score, validity, pass rate, summary, submission order); `result/out/proxy.jsonl` logs every model
  call (status, tier, tokens, latency). `result-attempt*/` are failed attempts, kept for the record.
- `xg-e2e-gemini-s2h-<task>-<version>[-xN]/`: the cross-grade of that run (`-xN`: follow-up shards for rounds that
  did not fit in the first worker's time). `result/out/derived.json` is the graded result per round and judge.
- Bulky files (submission archives, full harness logs and agent transcripts, raw judge captures, and each job's
  copy of `sforge/`, `tasks/` and the repair package) are kept outside the repository; every job's
  `artifacts-manifest.tsv` lists each one with its sha256 and size.
- `analyze.py OUT.json` combines both, applying EdgeBench's `select_best` and each version's rescale.

## Results (60 of 62 runs; pfr_formalization not runnable on E2B, lean_analysis_proofs not run)

Table generated by `analyze.py` (`analysis.json`). Scores are 0–100 where the version defines a rescale,
otherwise raw (`r`). "none" means no valid submission. The two right-hand columns grade the **same
submissions** with the original and the fixed judge, so a difference there is the effect of the fix alone.

| Task | v1 run (harness) | v2 run (harness) | v1 run: v1 judge / v2 judge | v2 run: v1 judge / v2 judge |
|---|---|---|---|---|
| apple_incremental_game | 20.26 | 0.00 | 20.26 / 20.26 | 0.00 / 0.00 |
| arc_compiler_runtime | 35.59 | 73.47 | - / - | - / - |
| borden_source_inversion | 7.012r | 100.00 | - / - | - / - |
| college_english_exam_bank | 0r | 0r | 0r / 0r | 0r / 0r |
| cta_risk_budget_optimization | 40.9375r | 12.5r | 40.9375r / 40.9375r | 12.5r / 12.5r |
| dabic_gravity_inversion | none | none | none / none | none / none |
| equivalence_class_divide_and_conquer | 24.20 | 20.00 | 24.20 / 24.20 | 20.00 / 20.00 |
| exchange_core_throughput | 10.40 | 7.35 | 0.00 / 12.10 | 0.00 / 10.32 |
| ffmpeg_swscale_reimplementation | 0.00 | 0.00 | 0.00 / 0.00 | 0.00 / 0.00 |
| git_rewrite_in_zig | 0.01 | 0.01 | 0.01 / 0.01 | 0.01 / 0.01 |
| graph_node_classification | 26.64 | 28.09 | 29.53 / 29.52 | 62.02 / 62.01 |
| grid_turing_robot | 2.84 | 54.58 | 2.84 / 2.84 | 54.58 / 54.58 |
| integer_compression_codec | 63.66 | 0.00 | 65.16 / 40.40 | 0.31 / 0.02 |
| jagua_nesting_optimization | 43.2955r | 44.1276r | 43.2955r / 47.0058r | 44.3123r / 44.5067r |
| juliet_vulnerability_analyzer | 10.00 | 79.48 | 10.00 / 10.00 | 77.91 / 79.48 |
| molecular_self_assembly | 56.36 | 0.01 | 60.99 / 59.90 | 0.01 / 0.01 |
| openrct2_theme_park_ai | 26.03 | 27.50 | - / - | - / - |
| openttd_transport_ai | 0.00 | 0.00 | - / - | - / - |
| order_addition_permutation_optimization | 0.00 | 25.04 | 0.00 / 7.70 | 0.00 / 25.04 |
| pfr_formalization | - | - | - / - | - / - |
| portfolio_risk_calibration | 0r | 31.56r | 0r / 0r | 31.61r / 31.56r |
| rust_multicrate_reconstruction | 13.99 | 2.39 | 13.99 / 25.47 | 3.77 / 7.33 |
| schemathesis_config_modernization | 3.15 | 3.15 | 3.15 / 3.15 | 3.15 / 3.15 |
| schemathesis_datagen_pipeline | 32.35 | 32.35 | 32.35 / 32.35 | 32.35 / 32.35 |
| schemathesis_reporting_observability | 2.00 | 2.50 | 2.00 / 2.50 | 2.00 / 2.50 |
| smt_solver | 0.00 | 0.00 | 0.00 / 0.00 | 0.00 / 0.00 |
| treant_forest | 20.32 | 92.71 | - / - | - / - |
| tree_block_partitioning | 1.25 | 13.50 | 0.36 / 0.36 | 13.00 / 12.75 |
| triangulation_coloring_optimization | 67.01 | 72.23 | 67.42 / 67.31 | 70.18 / 71.99 |
| vibrating_path_graph_coloring | 18.64 | 32.49 | 18.64 / 18.64 | 32.49 / 32.49 |
| warehouse_forklift_routing | none | 7.06 | none / none | 7.06 / 7.06 |

### What the paired grades show

**The fix changes the score of identical submissions:**
- *order_addition_permutation_optimization*: 0 → 7.70 (v1 run) and 0 → 25.04 (v2 run). Under the original
  judge one test always fails on an outdated helper fingerprint (4/5 passed), so pass-rate-first selection
  stays on the run's first valid submission (3.3e-09) and ignores every better one. This is the documented
  defect, reproduced on new submissions.
- *rust_multicrate_reconstruction*: 13.99 → 25.47 (v1 run) and 3.77 → 7.33 (v2 run): crates that cannot build
  offline under the original judge build under the fixed one.
- *jagua_nesting_optimization*: 43.30 → 47.01 raw (v1 run), 44.31 → 44.51 (v2 run).
- *juliet_vulnerability_analyzer*: 77.91 → 79.48 (v2 run); the v1 run's best submission is unchanged (10.00).
- *schemathesis_reporting_observability*: 2.00 → 2.50 in both runs.
- *integer_compression_codec*: 65.16 → 40.40 (v1 run), 0.31 → 0.02 (v2 run). The fix redefines the scale (the
  documented starter scores 0), so these are a change of unit, not of quality.
- *exchange_core_throughput*: the original judge cannot build without network (0 offline). With network, in
  the run, it gave the v1 run 10.40; the fixed judge, offline, gives the same submissions 12.10 (within
  throughput noise). The best engines of both runs pass the fixed judge's 33 integration tests; 6 of 26 (v1 run)
  and 10 of 25 (v2 run) submissions score 0 under it.

**The fix leaves rule-following work unchanged:** triangulation_coloring_optimization keeps Gemini's
submissions (67.42 → 67.31; 70.18 → 71.99), unlike the Qwen3.5 run, whose submissions all used flips the
README forbids. graph, tree_block, molecular, portfolio, vibrating, warehouse, grid, cta, equivalence,
apple, schemathesis_datagen, git, ffmpeg, smt, college and dabic give the same or nearly the same selected
score under both judges (several of these because Gemini's 2 h submissions score 0 or near it).

**Fixes outside the judge** (no paired grade; the two runs are the comparison, so they include run-to-run
variation):
- *treant_forest* (scale only): the runs' raw best scores, 89,473 and 85,820, read 20.32 and 19.43 on the
  original scale and 96.82 and 92.71 on the fixed one.
- *borden_source_inversion*: the v1 run stays at the documented baseline (7.01 raw). The v2 run, given the
  grader's forward model, recovered the source exactly from the noise-free public data and reached the
  theoretical maximum of 109 raw (hidden-well rRMSE 5×10⁻¹³) on its first agent submission, 68 min in.
  It is scored correctly, but the fixed task saturates: it no longer separates strong solvers.
- *arc_compiler_runtime* 35.59 → 73.47 and *openrct2_theme_park_ai* 26.03 → 27.50 (work image or prompt changes).
- *openttd_transport_ai*: 0.00 in both runs. The v1 run is partial: the worker ran out of memory at the end,
  after 16 of its 23 submissions had been graded in the run (`result/summary.json`, `partial: true`).

### Not verified end to end

- **pfr_formalization**: both versions ran out of disk on every E2B worker. With overlay2 the two images
  (10.7 GB each) leave 4.6 GB, and the agent's and judge's Lean builds need more (`result-attempt*-nospace/`).
- **lean_analysis_proofs**: the judge image alone unpacks to about 33 GB, more than any worker's disk.

Both need a machine with more disk. Docker Desktop on the audit host failed to start (a stale
`dockerInference` socket file); see the session notes.
