# Side-by-side tests: are they repeatable?

**How to read this file.** Each fixed task was tested side by side: the same test submissions were graded by the original grader (**v1**) and the fixed grader (**v2**). One test submission graded by both is an **arm**. A *trigger* shows the problem, a *valid control* is correct work that must keep its score, and an *invalid control* is wrong work that must stay rejected. The CSV columns use the same names.

Every repair's paired evaluation was run three times: run 1 is the published result, runs 2 and 3 are fresh reruns of the same job on new E2B workers (Lean Analysis locally, one container at a time under a 4 GB cap). OpenRCT2 is excluded: its repair changes only the prompt and has nothing to run.
**Result: 132 executed arms across 22 repair packages, 0 verdict changes.** In all three runs every trigger stayed fixed by v2, every valid control stayed valid, and every invalid control stayed rejected.

## Totals

- Executed arms compared: **132** (of 133 rows in `data/paired-results.csv` for the tasks that were run; openrct2 and derived rows are excluded).
- Arms with all 3 runs: **132** of 132.
- **Verdicts changed across runs: 0 of 132 arms.**

Score spread is reported per arm (min, max, relative spread). Deterministic evaluators reproduce exactly; timing-based scores move as noted, without changing any verdict.

## Per task

Relative spread = (max − min) / |mean| over the runs of one arm and one version; the column shows the largest value over the task's arms. Timing-based scores (exchange, ffmpeg, integer codec) are marked in the arm table below.

| task | arms | arms with 3 runs | verdict stable in every run? | max relative score spread (v1 / v2) | notes |
| --- | ---: | ---: | --- | --- | --- |
| arc_compiler_runtime | 5 | 5 | yes | 0.00% / 0.00% |  |
| borden_source_inversion | 7 | 7 | yes | 0.00% / 0.00% |  |
| college_english_exam_bank | 12 | 12 | yes | 0.00% / 0.00% |  |
| cta_risk_budget_optimization | 7 | 7 | yes | 0.00% / 0.00% |  |
| dabic_gravity_inversion | 4 | 4 | yes | 0.13% / 0.15% |  |
| equivalence_class_divide_and_conquer | 4 | 4 | yes | 0.00% / 0.00% |  |
| exchange_core_throughput | 8 | 8 | yes | 21.20% / 37.82% | Throughput (MT/s) varies up to 38% between runs on the same worker type; the correctness-gate verdicts never change. |
| ffmpeg_swscale_reimplementation | 7 | 7 | yes | 4.18% / 3.73% | Speedups vary up to 4%; trigger arms stay near 0 under v2 in every run. |
| graph_node_classification | 5 | 5 | yes | 0.72% / 0.35% |  |
| integer_compression_codec | 3 | 3 | yes | 24.60% / 21.15% | The speed term varies up to 25% between runs; the starter's v2 score stays near 1 and the corrupting codec stays at 0. |
| jagua_nesting_optimization | 13 | 13 | yes | 0.00% / 0.00% |  |
| lean_analysis_proofs | 6 | 6 | yes | 0.00% / 0.00% |  |
| openrct2_theme_park_ai | 1 | 0 | not run | – | prompt-only repair, nothing executable |
| order_addition_permutation_optimization | 8 | 8 | yes | 267.12% / 267.12% | The 'search' control is a time-limited random search, so its own score differs between runs (relative spread 2.67); pass rates, verdicts and v2's selection of the better submission are stable. |
| schemathesis_config_modernization | 4 | 4 | yes | 0.00% / 0.00% |  |
| schemathesis_datagen_pipeline | 8 | 8 | yes | 0.00% / 0.00% |  |
| schemathesis_reporting_observability | 7 | 7 | yes | 0.00% / 0.00% |  |
| smt_solver | 4 | 4 | yes | 0.00% / 0.00% |  |
| treant_forest | 4 | 3 | yes | 0.00% / 0.00% | 1 derived arm(s) not executed. |
| tree_block_partitioning | 3 | 3 | yes | 0.00% / 0.00% |  |
| triangulation_coloring_optimization | 4 | 4 | yes | 0.00% / 0.00% |  |
| warehouse_forklift_routing | 5 | 5 | yes | 0.00% / 0.00% |  |
| openttd_transport_ai | 5 | 5 | yes | 0.00% / 0.00% |  |

## Arms whose verdict changed

None. In every executed arm the v1 verdict and the v2 verdict were identical in all available runs.

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
| ffmpeg_swscale_reimplementation | reference implementation (run 1) | valid | yes | 0.967353–0.990566 (2.37%) | 0.980056–1.01228 (3.24%) |
| ffmpeg_swscale_reimplementation | reference implementation (run 2) | valid | yes | 0.496127–0.509049 (2.57%) | 0.498528–0.507032 (1.69%) |
| ffmpeg_swscale_reimplementation | shipped scaffold | baseline | yes | 0.440964–0.452737 (2.63%) | 0.012246–0.012416 (1.38%) |
| ffmpeg_swscale_reimplementation | errors on 3:1 downscale | trigger | yes | 2.88176–2.9643 (2.83%) | 0.000449–0.000464 (3.28%) |
| ffmpeg_swscale_reimplementation | silent no-op on 3:1 downscale | trigger | yes | 2.88451–2.98583 (3.44%) | 0.000446–0.000463 (3.73%) |
| ffmpeg_swscale_reimplementation | errors on RGBA→RGB24 | trigger | yes | 1.30586–1.36152 (4.18%) | 0.000451–0.000455 (0.88%) |
| ffmpeg_swscale_reimplementation | unsupported yuv420p→rgb24 | invalid | yes | 0–0 (0.00%) | 0–0 (0.00%) |
| graph_node_classification | baseline (shipped solution.py) | valid | no | 29.178–29.2783 (0.34%) | 29.1906–29.271 (0.27%) |
| graph_node_classification | neighbor (honest neighbour-vote solver, int ids) | valid | no | 24.0017–24.1102 (0.45%) | 24.0194–24.1044 (0.35%) |
| graph_node_classification | nanconf (baseline predictions, NaN confidences) | valid | no | 27.0871–27.1669 (0.29%) | 27.0794–27.1431 (0.24%) |
| graph_node_classification | shrink (one real prediction, rest `"x"`) | trigger | no | 15.912–16.0264 (0.72%) | – |
| integer_compression_codec | shipped Varint starter (unchanged) | trigger | yes | 0.2327–0.2998 (24.60%) | 0.9685–1.0569 (8.83%) |
| integer_compression_codec | delta + zigzag + varint | valid | yes | 0.8253–0.9679 (15.91%) | 6.7024–8.2668 (21.15%) |
| integer_compression_codec | starter with one corrupted value | invalid | yes | 0–0 (0.00%) | 0–0 (0.00%) |
| order_addition_permutation_optimization | search | valid | no | 0.000310698–0.0093733 (267.12%) | 0.000310698–0.0093733 (267.12%) |
| order_addition_permutation_optimization | identity, search | trigger | no | 3.3e-09–3.3e-09 (0.00%) | 0.000310698–0.0093733 (267.12%) |
| order_addition_permutation_optimization | search, identity | valid | no | 0.000310698–0.0093733 (267.12%) | 0.000310698–0.0093733 (267.12%) |
| order_addition_permutation_optimization | dup, identity, search | trigger | no | 3.3e-09–3.3e-09 (0.00%) | 0.000310698–0.0093733 (267.12%) |
| order_addition_permutation_optimization | badcost, identity, search | trigger | no | 3.3e-09–3.3e-09 (0.00%) | 0.000310698–0.0093733 (267.12%) |

## Jobs

44 E2B reruns (22 jobs × 2), all exit 0 with collected results; each worker was killed by exact ID (see evidence/runs/ledger.jsonl). Lean Analysis: 2 local reruns of all 12 cases, exit 0.
Three packages (CTA, Equivalence, Tree) had their parsed summaries regenerated with the package's own summarize.py; that script reproduces run 1's published summary byte for byte.

## Limits

Three runs per arm, on one worker type (8 vCPU, 8 GiB). Different hardware may move timing scores further.
Reruns repeat the authored controls, not model submissions.
College English: after a formal check found gaps in its first fix, the grader was revised (repairs/college_english_exam_bank-v2/paired/results.md). The tables above describe the first fixed version. The revised side-by-side job was itself run three times on fresh workers (evidence/runs/college_english_exam_bank-v2-paired-fix2, -fix2-rep2, -fix2-rep3), with identical graded results apart from timing.
