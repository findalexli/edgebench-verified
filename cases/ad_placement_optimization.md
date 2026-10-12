# Ad Placement Optimization (`ad_placement_optimization`)

**Outcome:** Kept, with a note. The original grader applies the rules of the AtCoder contest AHC001 correctly, and no problem found can score an honest solver wrongly.

## What the task asks

The solver places one rectangle per company on a 10000x10000 grid. The task statement says: "Each company i wants an ad space containing point (x_i+0.5, y_i+0.5) with area as close to r_i as possible. Maximize the total satisfaction." The README says that "Different rectangles may share edges but must not overlap (common area must be zero)", and that "Final score = sum of scores across all 50 public test cases". Category: Combinatorial Optimization.

## What we checked

There is no problem that changes scores enough to matter. We checked the rules that decide whether an output is legal:

- Shared edges and shared corners are accepted. For example, the test outputs `edge_touch` and `corner_touch` each scored `Score = 1000000000`, the same as the independent reference implementation (the "oracle").
- Any overlap with positive area is rejected when the later-indexed rectangle of the pair contains its own point. This includes a single unit cell, a contained rectangle and identical rectangles. Each was reported as `wrong answer`, with overlap as the reason.
- Bounds, positive area and point containment are checked exactly.
- A timeout, runtime error or wrong answer scores 0 for that case. The case is still listed and is never silently dropped. This matches the AHC001 system-test rule.

One ordering quirk, inherited from the contest code, does not change scores. The grader and the oracle disagree on 1 of 23 hand-written outputs. That output contains a rectangle that misses its own point, so it already scores p_i = 0. Whether its overlap is checked depends on the order of the output. The official AHC001 code behaves the same way, and the affected output gains nothing.

The note says:

1. The 50 graded inputs are the public generator seeds 0–49. These are also the official AHC001 example inputs. They are not held out.
2. Two reference points of the 0–100 scale (the "rank30" and "rank1" points) come from AtCoder results on different inputs. Their source was not checked.
3. The grader runs `min(nproc,2)` cases in parallel. `nproc` ignores a Docker CPU quota, and the task sets no `cpu_limit`. So the computing power available to a time-limited solver depends on how many CPUs the grader's machine gives it. The size of this effect was not measured.

## How much it matters

The largest score change for an honest solver is 0. The note items affect how scores should be read (public inputs, origin of the score scale, CPU allocation). They do not affect how any output is scored.

## How we checked it

- **Original grader, from the public image pinned by digest.** It ran with `--network none --memory 2g --cpus 2|1`, one container at a time. Seven test submissions, each built to exercise one rule, ran on all 50 grading cases, giving 350 per-case results. Every per-case status and score equals that of an exact-fraction oracle written from the README:

| Test submission | What it exercises | `TOTAL_SCORE` (grader = oracle) | `CASES_OK` | Score out of 100 |
|---|---|---|---|---|
| unit | unit cells, no contact | 826577 | 50 | 0.00035 |
| tile_full | guillotine tiling of the full square: every tile shares edges and corners, coordinates 0 and 10000 used | 27114970588 | 50 | 11.50 |
| tile_fit | point-containing sub-rectangles sized toward r_i within the tiles | 38525222727 | 50 | 16.33 |
| overlap1 | tile_full with one area-1 overlap per case | 0 | 0 (50 WA) | 0 |
| nocontain | unit cells, company 0 moved off its point | 824412 | 50 | 0.00035 |
| oob | company 0 x2 = 10001 | 0 | 0 (50 WA) | 0 |
| mixed | per case: 2 TLE, 7 RE, 7 WA, 4 CRLF/odd-whitespace, 30 plain | 26265417491 | 34 | 11.14 |

(WA = wrong answer, TLE = time limit exceeded, RE = runtime error.)

- **Small hand-written outputs.** 23 hand-written outputs ran through the original grader program and were compared with the oracle. They cover shared edges, shared corners, overlaps, out-of-range coordinates, zero area, malformed tokens and whitespace variants.
- **Source comparison.** The task's scoring source matches the scoring code of the official AHC001 visualizer statement by statement. The only differences are in input parsing and in how invalid output is reported.
- **Timing check.** A solver that busy-waits until 4.9 s of wall time ran at `--cpus 2` and at `--cpus 1`.
- **Data.** The image's own generator, run on seeds 0–49, reproduces all 50 grading inputs byte for byte. These equal the official AHC001 example inputs. A separate scan of the input constraints found no failures and no byte-identical duplicates.

## Limits

- No AI model or solver was run. Score effects are shown only on the test submissions and counterexamples we wrote.
- The grader program was not rebuilt from source. That the source and the program behave the same is inferred from matching behaviour on every branch exercised.
- No real optimizing solver was run, so the effect of CPU allocation on scores is not measured.
- The origin of the rank30 and rank1 reference points, and whether they are comparable to seeds 0–49, was not checked.

## Reproduce

- Grader image: `sha256:997d10b59ba0…` (full digest and key file hashes in `evidence/reviews/ad_placement_optimization.md`).
- Small hand-written outputs: `evidence/scripts/ad_placement_optimization/micro/run_micro.sh` (fixtures in `micro/fixtures.tsv`; results in `micro/tester_results.tsv` and `micro/oracle_results.tsv`)
- Test submissions on the original grader: `evidence/scripts/ad_placement_optimization/native/run_native.sh`, then `native/compare.py` (output in `native/compare_output.txt`)
- Exact-fraction oracle: `evidence/scripts/ad_placement_optimization/oracle.py`
- Data: `evidence/scripts/ad_placement_optimization/data/regen_in_image.sh` and `data/check_constraints.py`
- Full grader image digest and key file hashes: `evidence/reviews/ad_placement_optimization.md`
