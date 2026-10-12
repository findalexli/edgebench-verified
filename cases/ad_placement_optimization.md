# Ad Placement Optimization (`ad_placement_optimization`)

**Decision:** Retain with note. The original tester applies the AHC001 rules correctly, and no defect found can mis-score an honest solver.

## What the task asks for

The solver places one rectangle per company on a 10000x10000 grid: "Each company i wants an ad space containing point (x_i+0.5, y_i+0.5) with area as close to r_i as possible. Maximize the total satisfaction." The README says that "Different rectangles may share edges but must not overlap (common area must be zero)", and that "Final score = sum of scores across all 50 public test cases". Category: Combinatorial Optimization.

## What goes wrong

No material defect. We checked the rules that decide whether an output is legal:

- Shared edges and shared corners are accepted. For example, `edge_touch` and `corner_touch` each scored `Score = 1000000000`, the same as the oracle.
- Any overlap with positive area is rejected when the later-indexed rectangle of the pair contains its own point. This includes a single unit cell, a contained rectangle and identical rectangles. Each was reported as `wrong answer` with overlap as the reason.
- Bounds, positive area and point containment are checked exactly.
- A timeout, runtime error or wrong answer scores 0 for that case. The case is still listed and is never silently dropped. This matches the AHC001 system-test rule.

One inherited ordering quirk is not material. The tester and the oracle disagreed on 1 of 23 hand-written outputs. It involves a rectangle that already scores p_i = 0 because it misses its own point; whether its overlap is checked depends on output order. The official AHC001 code behaves the same way, and the affected output gains nothing.

The note says:

1. The 50 graded inputs are the public generator seeds 0–49, which are also the official AHC001 example inputs. They are not a holdout.
2. The rank30 and rank1 anchors come from AtCoder results on different instances. Their source was not checked.
3. The evaluator runs `min(nproc,2)` cases in parallel. `nproc` ignores a Docker CPU quota, and the task sets no `cpu_limit`. So the compute available to a time-budgeted solver depends on the judge's CPU allocation. The size of this effect was not measured.

## Impact

Maximum score effect for honest solvers: 0. The note items affect how scores should be read (public inputs, anchor origin, CPU allocation), not how any output is scored.

## Fix (v2)

No change; the note above ships with the task.

## How we know

- **Original evaluator in the pinned judge image** (`sha256:997d10b59ba0…`), run with `--network none --memory 2g --cpus 2|1`, one container at a time. Seven constructive controls on all 50 grading cases gave 350 per-case results. Every per-case status and score equals an exact-rational oracle written from the README:

| control | what it exercises | TOTAL_SCORE (native = oracle) | CASES_OK | normalized |
|---|---|---|---|---|
| unit | unit cells, no contact | 826577 | 50 | 0.00035 |
| tile_full | guillotine tiling of the full square: every tile shares edges and corners, coordinates 0 and 10000 used | 27114970588 | 50 | 11.50 |
| tile_fit | point-containing sub-rectangles sized toward r_i within the tiles | 38525222727 | 50 | 16.33 |
| overlap1 | tile_full with one area-1 overlap per case | 0 | 0 (50 WA) | 0 |
| nocontain | unit cells, company 0 moved off its point | 824412 | 50 | 0.00035 |
| oob | company 0 x2 = 10001 | 0 | 0 (50 WA) | 0 |
| mixed | per case: 2 TLE, 7 RE, 7 WA, 4 CRLF/odd-whitespace, 30 plain | 26265417491 | 34 | 11.14 |

- **Micro fixtures.** 23 hand-written outputs ran through the original tester binary and were compared with the oracle. They cover shared edges, shared corners, overlaps, out-of-range coordinates, zero area, malformed tokens and whitespace variants.
- **Source comparison.** The task's scoring source matches the official AHC001 visualizer's scoring code statement by statement. The only differences are in input parsing and in how invalid output is reported.
- **Timing control.** A solver that busy-waits to 4.9 s of wall time was run at `--cpus 2` and `--cpus 1`.
- **Data.** The image's own generator on seeds 0–49 reproduced all 50 grading inputs byte for byte. These equal the official AHC001 example inputs. An independent constraint scan found no failures and no byte duplicates.

## Limits

- No model or solver runs. Score effects are shown only on authored controls and counterexamples.
- The tester was not rebuilt from source. Source–binary equivalence is inferred from matching behaviour on every branch exercised.
- No real optimizing solver was run, so the effect of CPU allocation on scores is unmeasured.
- The origin of the rank anchors, and whether they are comparable to seeds 0–49, was not checked.

## Reproduce

- Micro fixtures: `evidence/scripts/ad_placement_optimization/micro/run_micro.sh` (fixtures in `micro/fixtures.tsv`; results in `micro/tester_results.tsv` and `micro/oracle_results.tsv`)
- Native controls: `evidence/scripts/ad_placement_optimization/native/run_native.sh`, then `native/compare.py` (output in `native/compare_output.txt`)
- Exact-rational oracle: `evidence/scripts/ad_placement_optimization/oracle.py`
- Data: `evidence/scripts/ad_placement_optimization/data/regen_in_image.sh` and `data/check_constraints.py`
- Full judge image digest and key file hashes: `evidence/reviews/ad_placement_optimization.md`
