# Ad Placement Optimization (`ad_placement_optimization`)

**Outcome:** Kept, with a note. <mark>The original grader applies the rules of the AtCoder contest AHC001 correctly, and we found no problem that would score a solver that follows the rules wrongly.</mark>

## What the task asks

The solver places one rectangle per company on a 10000x10000 grid. The task statement says: "Each company i wants an ad space containing point (x_i+0.5, y_i+0.5) with area as close to r_i as possible. Maximize the total satisfaction." The README says that "Different rectangles may share edges but must not overlap (common area must be zero)", and that "Final score = sum of scores across all 50 public test cases". The task is in the Combinatorial Optimization category.

## What we checked

We found no problem that changes scores. We checked the rules that decide whether an output is legal:

- The grader accepts shared edges and shared corners. The test outputs `edge_touch` and `corner_touch`, for example, each scored `Score = 1000000000`, the same as the independent reference implementation (the "oracle").
- The grader rejects any overlap with positive area when the later-indexed rectangle of the pair contains its own point. We tried a single unit cell, a contained rectangle and identical rectangles, and the grader reported each as `wrong answer`, giving overlap as the reason.
- It checks bounds, positive area and point containment exactly.
- A timeout, runtime error or wrong answer scores 0 for that case. The grader still lists the case and never drops it silently, which matches the AHC001 system-test rule.

The contest code has one ordering quirk, and the task inherits it, but it gives nothing to a solver that follows the rules. The grader and the oracle disagree on 1 of 23 hand-written outputs. That output contains a rectangle that misses its own point, so it already scores p_i = 0, and whether the grader checks its overlap depends on the order of the output. The official AHC001 code behaves the same way. The overlap itself earns nothing. At most it saves a solver some room it would otherwise have to free, and a valid output can recover that room at a cost of at most about 0.004 points out of 100 per affected company per case (`evidence/reviews/ad_placement_optimization.md`, "Does it accept real overlaps?").

The note says:

1. The 50 graded inputs are the public generator seeds 0–49. These are also the official AHC001 example inputs. They are not held out.
2. Two reference points of the 0–100 scale (the "rank30" and "rank1" points) come from AtCoder results on different inputs. We did not check their source.
3. The grader runs `min(nproc,2)` cases in parallel. `nproc` ignores a Docker CPU quota, and the task sets no `cpu_limit`, so the computing power a time-limited solver gets depends on how many CPUs the grader's machine gives it. We did not measure the size of this effect.

The shipped note leaves out two points:

- The 5 s limit is wall-clock time (`timeout 5` in `eval_ahc.sh`). A solver that budgets about 4.9 s of CPU time (for example with `clock()`) needs about 9.8 s of wall time when two cases share one CPU, so it times out and scores 0 for that case. A solver that budgets wall-clock time finished in time at `--cpus 1` (see the timing check below).
- The task text states "Memory limit: 1 GB". The grader does not enforce it, because `eval_ahc.sh` sets no memory limit and the task sets no `mem_limit`.

## How much it matters

For a solver that follows the rules, the scoring rules change the score by 0 at most. An output that exploits the ordering quirk gains at most about 0.004 points per affected company per case. We did not measure the effect of CPU allocation. On a grader with less than 2 CPUs of quota, a solver that budgets CPU time instead of wall-clock time can time out on every case. The other note items (public inputs, origin of the score scale, unenforced memory limit) change how to read the scores. They do not change how the grader scores any output.

## How we checked it

- We ran the original grader from the public image, pinned by digest, with `--network none --memory 2g --cpus 2|1` and one container at a time. Seven test submissions, each built to exercise one rule, ran on all 50 grading cases, giving 350 per-case results. Every per-case status and score equals that of an exact-fraction oracle we wrote from the README:

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

- We ran 23 small hand-written outputs through the original grader program and compared the results with the oracle. They cover shared edges, shared corners, overlaps, out-of-range coordinates, zero area, malformed tokens and whitespace variants.
- We compared the source. The task's scoring source matches the scoring code of the official AHC001 visualizer statement by statement, apart from input parsing and the way it reports invalid output.
- For the timing check, a solver that busy-waits until 4.9 s of wall time ran at `--cpus 2` and at `--cpus 1`.
- For the data, the image's own generator, run on seeds 0–49, reproduces all 50 grading inputs byte for byte. These equal the official AHC001 example inputs. A separate scan of the input constraints found no failures and no byte-identical duplicates.

## Limits

- We ran no AI model or solver. The score effects shown come only from the test submissions and counterexamples we wrote.
- We did not rebuild the grader program from source. We infer that the source and the program behave the same from their matching behaviour on every branch we exercised.
- We ran no real optimizing solver, so the effect of CPU allocation on scores is not measured. The timing check used a wall-clock spin, which cannot show the effect on a solver that budgets CPU time.
- We did not check the origin of the rank30 and rank1 reference points, or whether they are comparable to seeds 0–49.

## Reproduce

- Grader image: `sha256:997d10b59ba0…` (full digest and key file hashes in `evidence/reviews/ad_placement_optimization.md`).
- Small hand-written outputs: `evidence/scripts/ad_placement_optimization/micro/run_micro.sh` (fixtures in `micro/fixtures.tsv`; results in `micro/tester_results.tsv` and `micro/oracle_results.tsv`)
- Test submissions on the original grader: `evidence/scripts/ad_placement_optimization/native/run_native.sh`, then `native/compare.py` (output in `native/compare_output.txt`)
- Exact-fraction oracle: `evidence/scripts/ad_placement_optimization/oracle.py`
- Data: `evidence/scripts/ad_placement_optimization/data/regen_in_image.sh` and `data/check_constraints.py`
- Full grader image digest and key file hashes: `evidence/reviews/ad_placement_optimization.md`
