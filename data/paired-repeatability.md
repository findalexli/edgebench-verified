# Side-by-side tests: are they repeatable?

**How to read this file.** Each fixed task was tested side by side: the same test submissions were graded by the original grader (**v1**) and the fixed grader (**v2**). One test submission graded by both is an **arm**. A *trigger* shows the problem, a *valid control* is correct work that must keep its score, and an *invalid control* is wrong work that must stay rejected. The CSV columns use the same names.

Most arms of every repair's paired evaluation were run three times: run 1 is the published result, runs 2 and 3 are fresh reruns of the same job on new E2B workers (Lean Analysis locally, one container at a time under a 4 GB cap). Where a revision job was itself launched three times from the start, its runs are `-rep1`, `-rep2` and `-rep3`. OpenRCT2 is excluded: its repair changes only the prompt and has nothing to run.
**Result: 256 executed arms across 31 repair packages (30 fixed tasks and the removed task's partial fix): 254 graded comparisons and 2 setup runs that prepare inputs. 242 of the 256 have three runs (240 of the 254 graded comparisons), and 1 arm changed its verdict between runs.** The change is Vibrating Path's `wall25` valid control under the *original* grader at 4 CPUs: 36 OK and 14 TLE in run 1, 50/50 in runs 2 and 3 (details below). No verdict under any fixed grader changed. Fourteen graded comparisons have fewer than three runs: the Rust starter's fixed-version score (that job was not repeated, cost); the CTA shipped standard answer in the v2.1 native job (only run 1 included it; runs 2 and 3 repeated the three decisive arms); the six Exchange Core rows at 4 CPUs, which are already one row per run in `data/paired-results.csv` (two arms, each run once in `exchange_core_throughput-v2-cpu4m8g-rep1`, `-rep2` and `-rep3`); FFmpeg's three v2.2 native controls (a single run, `ffmpeg-native-v2.2-20261013`); and Datagen's three v2.1 controls (a single clean run, `schemathesis_datagen_pipeline-v2.1-native-20261013b`, not repeated). In every other arm, all three runs kept the outcome recorded in the package's results: triggers stayed in the state the results describe (for ARC they are unchanged by design, because that fix only adds documentation), valid controls stayed valid, and invalid controls kept their recorded verdict (the datagen `garbage_shape` arm is accepted by the original grader, and the Schemathesis Reporting starter rises from 0.020 to 0.025 under the fixed grader, in every run).
Arms added on 2026-10-12 (Git, PFR, Rust, Grid Turing, Molecular, Vibrating Path, Apple, and the CPU arms of Triangulation and Warehouse) were repeated on 2026-10-13 with each job's own `run.sh` and inputs. Smaller jobs that are not rows of `data/paired-results.csv` are compared under Supplementary jobs. The Portfolio Risk and Juliet arms (added 2026-10-13) were each run three times on fresh E2B workers by their own `run.sh`.
Revision jobs of 2026-10-13 supply the rows of the current fixed versions: Jagua v2.1 (`jagua_nesting_optimization-v2.1-paired-rep1`, `-rep2`, `-rep3`), Triangulation v2.2 (`triangulation-v22-paired`, `-rep2`, `-rep3`; all ten Triangulation rows now compare the original with v2.2, and the earlier v2.1 jobs are kept under Supplementary jobs), College English v2.2 (`college_english_exam_bank-v2-paired-fix3`, `-rep2`, `-rep3`), Graph Node v2.1 (`graph_node_classification-v2-paired-v21a` and `-v21b`, each with `-rep2` and `-rep3`) and CTA v2.1 (`cta_risk_budget_optimization-v2.1-native-rep1`, `-rep2`, `-rep3`). Each row is read from that job's own outputs with the same parser in every run; graded jobs are regraded by the job's own `grade.py` in a scratch copy.

## Totals

- Executed arms compared: **256** (of 257 rows in `data/paired-results.csv` for the tasks that were run; openrct2, derived rows and rows marked not counted in the table below are excluded).
- Of these, 2 are setup runs that prepare an input (role `setup`), so graded comparisons: **254**, of which **240** have all 3 runs.
- Arms with all 3 runs: **242** of 256.
- **Verdicts changed across runs: 1 of 256 arms.**

Score spread is reported per arm (min, max, relative spread). Deterministic evaluators reproduce exactly. Timing-based scores move as noted without changing a verdict. The one verdict change, a wall-clock timeout under the original grader, is listed under Arms whose verdict changed.

## Per task

Relative spread = (max − min) / |mean| over the runs of one arm and one version; the column shows the largest value over the task's arms. Timing-based scores (exchange, ffmpeg, integer codec) are marked in the arm table below.

| task | arms | arms with 3 runs | verdict stable in every run? | max relative score spread (v1 / v2) | notes |
| --- | ---: | ---: | --- | --- | --- |
| arc_compiler_runtime | 5 | 5 | yes | 0.00% / 0.00% |  |
| borden_source_inversion | 7 | 7 | yes | 0.00% / 0.00% |  |
| college_english_exam_bank | 29 | 29 | yes | 0.00% / 0.00% |  |
| cta_risk_budget_optimization | 11 | 10 | yes (only 10/11 arms have 3 runs) | 0.00% / 0.00% | The v2.1 native job's shipped standard answer ran only in run 1 (`-rep1`, which also built the superseded strict candidate); its three decisive arms ran in all three runs. |
| dabic_gravity_inversion | 4 | 4 | yes | 0.13% / 0.15% |  |
| equivalence_class_divide_and_conquer | 4 | 4 | yes | 0.00% / 0.00% |  |
| exchange_core_throughput | 14 | 8 | yes (only 8/14 arms have 3 runs) | 21.20% / 37.82% | Throughput (MT/s) varies up to 38% between runs on the same worker type; the correctness-gate verdicts never change. The six 4-CPU rows are one row per run (`-cpu4m8g-rep1` to `-rep3`), so each has one run. |
| ffmpeg_swscale_reimplementation | 10 | 7 | yes (only 7/10 arms have 3 runs) | 4.18% / 3.73% | Speedups vary up to 4%; trigger arms stay near 0 under v2 in every run. The three v2.2 native rows have one run (`ffmpeg-native-v2.2-20261013`). |
| git_rewrite_in_zig | 10 | 10 | yes | 0.00% / 0.00% |  |
| graph_node_classification | 7 | 7 | yes | 0.76% / 0.60% |  |
| integer_compression_codec | 3 | 3 | yes | 24.60% / 21.15% | The speed term varies up to 25% between runs; the starter's v2 score stays near 1 and the corrupting codec stays at 0. |
| jagua_nesting_optimization | 26 | 26 | yes | 0.00% / 0.00% |  |
| lean_analysis_proofs | 6 | 6 | yes | 0.00% / 0.00% |  |
| openrct2_theme_park_ai | 1 | 0 | not run | – | prompt-only repair, nothing executable |
| order_addition_permutation_optimization | 8 | 8 | yes | 267.12% / 267.12% | The 'search' control is a time-limited random search, so its own score differs between runs (relative spread 2.67); pass rates, verdicts and v2's selection of the better submission are stable. |
| schemathesis_config_modernization | 4 | 4 | yes | 0.00% / 0.00% |  |
| schemathesis_datagen_pipeline | 11 | 8 | yes (only 8/11 arms have 3 runs) | 0.00% / 0.00% | The three v2.1 rows come from one clean run (`schemathesis_datagen_pipeline-v2.1-native-20261013b`), which was not repeated. |
| schemathesis_reporting_observability | 7 | 7 | yes | 0.00% / 0.00% |  |
| smt_solver | 4 | 4 | yes | 0.00% / 0.00% |  |
| treant_forest | 4 | 3 | yes | 0.00% / 0.00% | 1 derived arm(s) not executed. |
| tree_block_partitioning | 3 | 3 | yes | 0.00% / 0.00% |  |
| triangulation_coloring_optimization | 10 | 10 | yes | 0.00% / 0.00% |  |
| warehouse_forklift_routing | 7 | 7 | yes | 0.00% / 0.00% |  |
| openttd_transport_ai | 5 | 5 | yes | 0.00% / 0.00% |  |
| pfr_formalization | 4 | 4 | yes | 0.00% / 0.00% |  |
| grid_turing_robot | 7 | 7 | yes | 0.00% / 0.00% |  |
| molecular_self_assembly | 7 | 7 | yes | 0.00% / 0.00% |  |
| rust_multicrate_reconstruction | 4 | 3 | yes (only 3/4 arms have 3 runs) | 0.00% / 0.00% | The starter's job (`-paired-r2-starter`) was not repeated (about 40 min and up to 19.9 GB disk per run); its original-grader scores are reproduced by round 1. Reference, partial and bad: three runs each. |
| vibrating_path_graph_coloring | 7 | 7 | **no (1 arm(s) changed)** | 0.00% / 0.00% | One valid-control arm (`wall25` at 4 CPUs) changed its original-grader verdict between runs; see Arms whose verdict changed. |
| apple_incremental_game | 6 | 6 | yes | 0.00% / 0.00% |  |
| portfolio_risk_calibration | 10 | 10 | yes | 0.00% / 0.00% |  |
| juliet_vulnerability_analyzer | 13 | 13 | yes | 0.00% / 0.00% |  |

## Arms whose verdict changed

### vibrating_path_graph_coloring: `wall25` (works until 25 s wall clock) (valid)

| run | v1 result | v2 result | v1 score | v2 score |
| --- | --- | --- | --- | --- |
| 1 | OK 36 TLE 14 WA 0 RE 0 | OK 50 TLE 0 WA 0 RE 0 | inf | 24650014 |
| 2 | OK 50 TLE 0 WA 0 RE 0 | OK 50 TLE 0 WA 0 RE 0 | 24650014 | 24650014 |
| 3 | OK 50 TLE 0 WA 0 RE 0 | OK 50 TLE 0 WA 0 RE 0 | 24650014 | 24650014 |

Same solution, same job (`vibrating_path_graph_coloring-v2-paired-b`), fresh 8-vCPU workers. This solution was graded 9 times by the original grader at 4 CPUs (3 runs of `-b`, plus 2 per run of `-c`), and lost cases only once. The fixed version passed 50/50 in all 6 of its gradings. The package's results attribute the 14 TLE to the tester being starved of CPU next to 7 busy cases (an inference, not observed directly). This is an original-grader outcome that is not repeatable. No fixed-version verdict changed, so the fix's acceptance is unaffected (`repairs/vibrating_path_graph_coloring-v2/paired/results.md`, Repeatability).

## Score spread per arm (arms with any numeric spread)

| task | arm | role | timing-based | v1 min–max (rel) | v2 min–max (rel) |
| --- | --- | --- | --- | --- | --- |
| dabic_gravity_inversion | honest model-space D-ABIC (`FORM="model"`) | trigger | no | 25.7525–25.7857 (0.13%) | 26.8105–26.8499 (0.15%) |
| dabic_gravity_inversion | honest data-space D-ABIC (`FORM="data"`) | valid | no | 26.8137–26.8241 (0.04%) | 26.8108–26.8356 (0.09%) |
| dabic_gravity_inversion | data form, log-det via `np.linalg.det` (`make_invalid_variant.py`) | invalid | no | 26.9009–26.9204 (0.07%) | 26.8616–26.9019 (0.15%) |
| exchange_core_throughput | unmodified engine, original image without artifacts ("v1raw") | setup | yes | 0–0 (0.00%) | – |
| exchange_core_throughput | unmodified engine (control, run 1) | valid | yes | 2008–2054 (2.26%) | 2153–3105 (37.82%) |
| exchange_core_throughput | unmodified engine (control, run 2) | valid | yes | 2210–2698 (19.65%) | 2729–2978 (8.83%) |
| exchange_core_throughput | `topo21` honest variant | valid | yes | 2440–3003 (21.20%) | 2387–3222 (30.96%) |
| exchange_core_throughput | `feeswap` (fee swap, balance kept at zero) | trigger | yes | 2269–2643 (15.54%) | 0–0 (0.00%) |
| exchange_core_throughput | `dropevents` (user events not forwarded) | trigger | yes | 2197–2457 (11.32%) | 0–0 (0.00%) |
| exchange_core_throughput | `feeleak` | invalid | yes | 0–0 (0.00%) | 0–0 (0.00%) |
| exchange_core_throughput | `compileerr` | invalid | yes | 0–0 (0.00%) | 0–0 (0.00%) |
| exchange_core_throughput | unmodified engine, 4 CPUs run 1 | valid | yes | – | – |
| exchange_core_throughput | unmodified engine, 4 CPUs run 2 | valid | yes | – | – |
| exchange_core_throughput | unmodified engine, 4 CPUs run 3 | valid | yes | – | – |
| exchange_core_throughput | `topo21`, 4 CPUs run 1 | valid | yes | – | – |
| exchange_core_throughput | `topo21`, 4 CPUs run 2 | valid | yes | – | – |
| exchange_core_throughput | `topo21`, 4 CPUs run 3 | valid | yes | – | – |
| ffmpeg_swscale_reimplementation | forwarding shim, each frame once (`ref_r1`) | valid | yes | 0.967353–0.990566 (2.37%) | 0.980056–1.01228 (3.24%) |
| ffmpeg_swscale_reimplementation | forwarding shim, each frame twice (`ref_r2`, about 2× slower) | valid | yes | 0.496127–0.509049 (2.57%) | 0.498528–0.507032 (1.69%) |
| ffmpeg_swscale_reimplementation | shipped scaffold | baseline | yes | 0.440964–0.452737 (2.63%) | 0.012246–0.012416 (1.38%) |
| ffmpeg_swscale_reimplementation | errors on 3:1 downscale | trigger | yes | 2.88176–2.9643 (2.83%) | 0.000449–0.000464 (3.28%) |
| ffmpeg_swscale_reimplementation | silent no-op on 3:1 downscale | trigger | yes | 2.88451–2.98583 (3.44%) | 0.000446–0.000463 (3.73%) |
| ffmpeg_swscale_reimplementation | errors on RGBA→RGB24 | trigger | yes | 1.30586–1.36152 (4.18%) | 0.000451–0.000455 (0.88%) |
| ffmpeg_swscale_reimplementation | unsupported yuv420p→rgb24 | invalid | yes | 0–0 (0.00%) | 0–0 (0.00%) |
| ffmpeg_swscale_reimplementation | Forward every call to FFmpeg | valid | yes | – | – |
| ffmpeg_swscale_reimplementation | Skip second call of each context | trigger | yes | – | – |
| ffmpeg_swscale_reimplementation | Always return an error | invalid | yes | – | – |
| graph_node_classification | baseline (shipped solution.py) | valid | no | 29.178–29.2783 (0.34%) | 29.1906–29.271 (0.27%) |
| graph_node_classification | neighbor (honest neighbour-vote solver, int ids) | valid | no | 24.0017–24.1102 (0.45%) | 24.0194–24.1044 (0.35%) |
| graph_node_classification | nanconf (baseline predictions, NaN confidences) | valid | no | 27.0871–27.1669 (0.29%) | 27.0794–27.1431 (0.24%) |
| graph_node_classification | shrink (one real prediction, rest `"x"`) | trigger | no | 15.912–16.0264 (0.72%) | – |
| graph_node_classification | neighbor_intkeys | trigger | no | 0–0 (0.00%) | 24.0619–24.2067 (0.60%) |
| graph_node_classification | dupkeys_after_str | invalid | no | 19.8731–20.0246 (0.76%) | – |
| integer_compression_codec | shipped Varint starter (unchanged) | trigger | yes | 0.2327–0.2998 (24.60%) | 0.9685–1.0569 (8.83%) |
| integer_compression_codec | delta + zigzag + varint | valid | yes | 0.8253–0.9679 (15.91%) | 6.7024–8.2668 (21.15%) |
| integer_compression_codec | starter with one corrupted value | invalid | yes | 0–0 (0.00%) | 0–0 (0.00%) |
| order_addition_permutation_optimization | search | valid | no | 0.000310698–0.0093733 (267.12%) | 0.000310698–0.0093733 (267.12%) |
| order_addition_permutation_optimization | identity, search | trigger | no | 3.3e-09–3.3e-09 (0.00%) | 0.000310698–0.0093733 (267.12%) |
| order_addition_permutation_optimization | search, identity | valid | no | 0.000310698–0.0093733 (267.12%) | 0.000310698–0.0093733 (267.12%) |
| order_addition_permutation_optimization | dup, identity, search | trigger | no | 3.3e-09–3.3e-09 (0.00%) | 0.000310698–0.0093733 (267.12%) |
| order_addition_permutation_optimization | badcost, identity, search | trigger | no | 3.3e-09–3.3e-09 (0.00%) | 0.000310698–0.0093733 (267.12%) |

## Supplementary jobs

These jobs add arms beyond `data/paired-results.csv` (extra grader versions, CPU counts, or follow-up checks). Each was run three times like the main jobs, and every label of its own summary is compared across the runs. Throughput numbers (Exchange Core) move between runs, as in the main table. SMT's CPU-quota jobs (`smt_solver-v2-paired-cpu`, `-b-cpu`, `-c-cpu`) are not repeated and not listed: that part of the SMT fix was withdrawn, because the official configs give SMT 16 grader CPUs.

| task | job | what it adds | runs with results | labels compared | labels whose outcome changed | score spread (labels that moved, max relative) |
| --- | --- | --- | --- | ---: | --- | --- |
| schemathesis_reporting_observability | `schemathesis_reporting_observability-v2-paired-rev2` | revised fixed version, all arms incl. the added other-suite and unterminated arms | 1, 2, 3 | 20 | none | – |
| warehouse_forklift_routing | `warehouse_forklift_routing-v2-cpu4-a` | cpu140 at 4 CPUs (fixed and earlier fixed version) | 1, 2, 3 | 2 | none | – |
| warehouse_forklift_routing | `warehouse_forklift_routing-v2-cpu4-b` | cpu80 at 4 CPUs (all three versions) | 1, 2, 3 | 3 | none | – |
| warehouse_forklift_routing | `warehouse_forklift_routing-v2-cpu4-c` | earlier controls at 4 CPUs; cpu80 at 8 CPUs; cpu140 original | 1, 2, 3 | 11 | none | – |
| warehouse_forklift_routing | `warehouse_forklift_routing-v2-cpu4-d` | near-limit control at 4 CPUs | 1, 2, 3 | 2 | none | – |
| triangulation_coloring_optimization | `triangulation-v2-paired-cpu` | CPU arms, original vs the earlier fixed version (v2.1) and the version before it | 1, 2, 3 | 18 | none | – |
| triangulation_coloring_optimization | `triangulation-v2-paired-cpu-controls` | flip-rule controls vs the earlier fixed version (v2.1), 8 and 4 CPUs | 1, 2, 3 | 16 | none | – |
| vibrating_path_graph_coloring | `vibrating_path_graph_coloring-v2-paired-c` | wall25 with tester-start logging | 1, 2, 3 | 3 | none | – |
| exchange_core_throughput | `exchange_core_throughput-v2-paired-shutdownfail` | shutdown-failure triggers | 1, 2, 3 | 8 | none | 5 label(s), max 38.77% |
| college_english_exam_bank | `college_english_exam_bank-v2-paired-multiblock` | multi-block responses (v1, earlier fixed, fixed) | 1, 2, 3 | 15 | none | – |
| triangulation_coloring_optimization | `triangulation-v2-paired` | full judge, original vs the earlier fixed version (v2.1) | 1, 2, 3 | 8 | none | – |
| triangulation_coloring_optimization | `triangulation-v22-paired` | v2.2 job: full judge (8 and 4 CPUs), cross-version case sets and CPU arms of v1, v2.1 and v2.2 | 1, 2, 3 | 54 | none | – |
| jagua_nesting_optimization | `jagua_nesting_optimization-v2.1-paired-rep1, -rep2, -rep3` | v2.1 revision job: witnesses and full scorer under v1, v2 (superseded) and v2.1 | 1, 2, 3 | 69 | none | – |
| college_english_exam_bank | `college_english_exam_bank-v2-paired-fix3` | v2.2 revision job: all 29 responses under v1, the earlier fixed version and v2.2 | 1, 2, 3 | 87 | none | – |
| graph_node_classification | `graph_node_classification-v2-paired-v21a` | v2.1 revision (baseline, neighbor, neighbor_intkeys, dupkeys_after_str) under v1, first fixed and v2.1 | 1, 2, 3 | 12 | none | 8 label(s), max 0.76% |
| graph_node_classification | `graph_node_classification-v2-paired-v21b` | v2.1 revision (shrink, nanconf, missing_half) under v1, first fixed and v2.1 | 1, 2, 3 | 9 | none | 4 label(s), max 0.41% |
| arc_compiler_runtime | `arc_compiler_runtime-hang-suite` | one hidden suite hangs (original grader only) | 1, 2, 3 | 4 | none | – |
| borden_source_inversion | `borden_source_inversion-v2-paired-r3` | controls vs v1, earlier fixed and fixed work image | 1, 2, 3 | 21 | none | – |
| rust_multicrate_reconstruction | `rust_multicrate_reconstruction-v2-paired-r2-reference` | reference: original, original + cc files, fixed | 1, 2, 3 | 3 | none | – |
| rust_multicrate_reconstruction | `rust_multicrate_reconstruction-v2-paired-r2-partial` | partial: original, original + cc files, fixed | 1, 2, 3 | 3 | none | – |
| rust_multicrate_reconstruction | `rust_multicrate_reconstruction-v2-paired-r2-bad` | bad: original, original + cc files, fixed | 1, 2, 3 | 3 | none | – |

## Jobs

44 E2B reruns (22 jobs × 2), all exit 0 with collected results; each worker was killed by exact ID (see evidence/runs/ledger.jsonl). Lean Analysis: 2 local reruns of all 12 cases, exit 0.
2026-10-13: 46 further E2B reruns (23 jobs × 2: Git ×2 jobs, PFR ×2, Rust ×3, Grid Turing, Molecular, Warehouse CPU ×4, Vibrating Path ×3, Apple, Triangulation CPU ×2, Borden r3, Exchange shutdown-failure, College English multi-block, ARC hang suite), at most 4 workers at a time. Each has `status: exit=0` on its first attempt and collected `result/out/`, and its worker was killed. Inputs that are image files or materialized grader files were put in the rerun directories from the internal copies, with sha256 checked against run 1's records, and removed after collection.
Three packages (CTA, Equivalence, Tree) had their parsed summaries regenerated with the package's own summarize.py; that script reproduces run 1's published summary byte for byte.
2026-10-13: Portfolio Risk (`portfolio_risk_calibration-v2-paired`, `-rep2`, `-rep3`) and Juliet (`juliet_vulnerability_analyzer-v2-paired`, `-rep2`, `-rep3`): 6 E2B jobs, each with `status: exit=0` and collected `result/out/`. Each Portfolio job also keeps a first attempt (`attempt1-no-patch/`) that stopped before grading because GNU `patch` was missing on the worker; it is not counted.
2026-10-13, revision jobs: Jagua v2.1 ×3, Triangulation v2.2 ×3, College English v2.2 ×3, Graph Node v2.1 ×6 (two jobs ×3), CTA v2.1 ×3 and Exchange Core at 4 CPUs ×3 on E2B, each with `status: exit=0` and collected `result/out/`, workers killed by exact ID; plus one Datagen v2.1 run and one FFmpeg v2.2 run (single runs). Triangulation's run 2 has one earlier attempt that stopped during the image pull (`exit=2`, kept as `triangulation-v22-paired-rep2-pullfail`); it is not counted.

## Limits

Three runs per arm, on one worker type (8 vCPU, 8 GiB). Different hardware may move timing scores further, and may move wall-clock verdicts near a limit, as the Vibrating Path `wall25` arm shows.
Not repeated: the Rust starter's fixed-version run (1 run), the CTA v2.1 standard answer (1 run), FFmpeg's v2.2 native controls and Datagen's v2.1 controls (1 run each), and SMT's CPU-quota measurements (a withdrawn part of the fix). The Exchange Core 4-CPU rows are one run per row by design.
Reruns repeat the authored controls, not model submissions.
College English: rows A–L compare the original with the first fixed version (package run and its two repeats). After a formal check found gaps, the grader was revised twice; rows GA–QF compare the original with the current v2.2 grader (`college_english_exam_bank-v2-paired-fix3`, `-rep2`, `-rep3`), and the same job's runs grade all 29 responses under v2.2 (Supplementary jobs). The intermediate revision job was also run three times (evidence/runs/college_english_exam_bank-v2-paired-fix2, -fix2-rep2, -fix2-rep3), with identical graded results apart from timing.
