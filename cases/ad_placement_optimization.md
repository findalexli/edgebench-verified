# Ad Placement Optimization (`ad_placement_optimization`)

Status: reviewed by the coordinator, 2026-10-12

- **Domain:** Combinatorial Optimization
- **Decision:** Retain with note. The original tester applies the AHC001 rules correctly and no defect can mis-score an honest solver. The note covers provenance and calibration only.

## What the task promises

The prompt asks for one rectangle per company on a 10000x10000 grid: "Each company i wants an ad space containing point (x_i+0.5, y_i+0.5) with area as close to r_i as possible. Maximize the total satisfaction." The README says that "Different rectangles may share edges but must not overlap (common area must be zero)". It also says "Final score = sum of scores across all 50 public test cases", which it calls "50 fixed public test cases that you cannot view directly".

## What we checked and how

- An earlier audit placed this task on hold under the label "ad-overlap". That hold was an automatic content-filter stop of an earlier review agent, not a recorded task defect. The overlap probe never ran, and no saved specification for it exists. We took it to mean the question of whether the tester accepts legal contact between rectangles and rejects real overlap.
- **Source comparison.** We compared the task's scoring source with the official AHC001 visualizer's scoring code statement by statement. The rules match. The only differences are in input parsing and in how invalid output is reported.
- **Micro fixtures.** We ran 23 hand-written outputs through the original judge tester binary and compared each result with an oracle written from the README. The fixtures cover shared edges, shared corners, overlaps, out-of-range coordinates, zero area, malformed tokens and whitespace variants.
- **Native runs.** The full original evaluator ran in the pinned judge image locally, with `--network none --memory 2g --cpus 2|1` and one container at a time. We used 7 constructive controls on all 50 grading cases, which gives 350 per-case results. Each was compared with an exact-rational oracle and graded by the repository harness.
- **Timing control.** A solver that busy-waits to 4.9 s of wall time was run at `--cpus 2` and `--cpus 1`.
- **Data checks.** We regenerated the inputs with the image's own generator on seeds 0–49, compared them with the official AHC001 example inputs, and ran an independent constraint scan.
- **Original identity.** Judge image `seededge/edgebench.judge.ad_placement_optimization@sha256:997d10b59ba063f23429fb8eace84b0cb28ea22b0f9fe5243ef64a2310e19ba9`. Key files: task JSON sha256 `972a31a5…7531`, `/tmp/eval_ahc.sh` `8445b091…036ed`, `tools/bin/tester` `2498e6a2…dcb`, `tools/bin/gen` `e68b36f6…2d42d`.

## What we found

**Not material: the earlier "ad-overlap" hold.** The hold recorded no defect. Re-checking showed that the tester enforces the README and AHC001 rules for honest output:

- Shared edges and shared corners are accepted. For example, `edge_touch` and `corner_touch` each scored `Score = 1000000000`, the same as the oracle.
- Any overlap with positive area is rejected, including a single unit cell, a contained rectangle and identical rectangles. Each of these was reported as `wrong answer` with overlap as the reason.
- Bounds, positive area and point containment are checked exactly.

**Native results.** On all 50 grading cases, every per-case status and score from the native run equals the exact-rational oracle. Totals for the original evaluator:

| control | what it exercises | TOTAL_SCORE (native = oracle) | CASES_OK | normalized |
|---|---|---|---|---|
| unit | unit cells, no contact | 826577 | 50 | 0.00035 |
| tile_full | guillotine tiling of the full square: every tile shares edges and corners, coordinates 0 and 10000 used | 27114970588 | 50 | 11.50 |
| tile_fit | point-containing sub-rectangles sized toward r_i within the tiles | 38525222727 | 50 | 16.33 |
| overlap1 | tile_full with one area-1 overlap per case | 0 | 0 (50 WA) | 0 |
| nocontain | unit cells, company 0 moved off its point | 824412 | 50 | 0.00035 |
| oob | company 0 x2 = 10001 | 0 | 0 (50 WA) | 0 |
| mixed | per case: 2 TLE, 7 RE, 7 WA, 4 CRLF/odd-whitespace, 30 plain | 26265417491 | 34 | 11.14 |

**Failed cases.** A timeout, runtime error or wrong answer scores 0 for that case. The case is still listed and is never silently dropped, which matches the AHC001 system-test rule.

**Not material: an inherited ordering quirk.** The tester and oracle disagreed on 1 of the 23 micro fixtures. The difference involves a rectangle that already scores p_i = 0 because it misses its own point, and whether its overlap check depends on output order. The official AHC001 code behaves the same way, and the affected output gains nothing. Maximum score effect for honest solvers: 0.

**Confirmed: earlier data statements.** The judge image's generator on seeds 0–49 reproduced all 50 grading inputs byte for byte. These are also the official AHC001 example inputs. The constraint scan found no failures and no byte duplicates. The `unit` control reproduces the earlier total of 826577.

## Note for users

No repair. The note says:

1. The 50 graded inputs are the public generator seeds 0–49, which are also the official AHC001 example inputs. The README calls these cases ones "you cannot view directly", but they are not a holdout.[^1]
2. The rank30 and rank1 anchors come from AtCoder results on different instances. Their source was not checked.
3. The evaluator runs `min(nproc,2)` cases in parallel. `nproc` ignores a Docker CPU quota, and the task sets no `cpu_limit`. As a result, the compute available to a time-budgeted solver depends on the judge's CPU allocation. The size of this effect was not measured.

## Limits and what was not run

- No model or solver re-runs were done. Score effects are shown only on authored controls and counterexamples.
- We did not rebuild the tester from source. Equivalence of source and binary is inferred from matching behavior on every branch exercised.
- No real optimizing solver was run, so the effect of CPU allocation on scores is unmeasured.
- The origin of the rank anchors, and whether they are comparable to seeds 0–49, was not checked.
- The exact content of the earlier, never-run overlap probe is not recorded anywhere. Its scope here is reconstructed from the earlier task-card blocker and the earlier controls.

## Reproduce

- Micro fixtures: `evidence/scripts/ad_placement_optimization/micro/run_micro.sh` (fixtures in `micro/fixtures.tsv`; results in `micro/tester_results.tsv` and `micro/oracle_results.tsv`)
- Native controls: `evidence/scripts/ad_placement_optimization/native/run_native.sh`, then `native/compare.py` (output in `native/compare_output.txt`)
- Exact-rational oracle: `evidence/scripts/ad_placement_optimization/oracle.py`
- Data: `evidence/scripts/ad_placement_optimization/data/regen_in_image.sh` and `data/check_constraints.py`

[^1]: The review quotes the README phrase "cannot view directly". The coordinator's ledger notes that this wording was reported by the reviewer but not re-located by the coordinator.
