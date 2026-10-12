# Grid Turing Robot (`grid_turing_robot`)

Status: reviewed by the coordinator, 2026-10-12

- **Domain:** Combinatorial Optimization
- **Decision:** Retain with note. Honest solutions are scored correctly. Three issues need a note, each with its own maximum effect: the baseline anchor offset (2.84 points), the undisclosed rule that one failed case voids the submission (about 20 points), and dependence on the judge's CPU count (up to the full score on a judge with fewer than about 8 CPUs).

## What the task promises

The prompt says: "Your solution is scored on **50 fixed test cases**. Final score = sum of individual case scores. **Lower is better.**" The README gives the per-case score as "If V = K: Score = C + Q", with the penalty "If V < K: Score = 2N^4 + (K − V) × N^2". It promises a "Time limit | 30 seconds / test case" and states: "Each submission returns per-case scores and a total score."

## What we checked and how

- **Independent oracle.** We wrote a parser, simulator and scorer from the README text alone, without importing the task's verifier.
  - A differential test ran 3,000 random rule tables on the 50 grading cases.
  - Full-route agreement was checked on a known-good solution over all 50 cases.
- **Exhaustive search.** We searched every rule table with C+Q ≤ 5 on tiny boards to confirm the minimum-cost bound.
- **Data checks.** We checked all 50 cases for:
  - N and K in range;
  - well-formed walls and full grid connectivity;
  - distinct targets;
  - the relation X ≤ T ≤ 2X, using an independent BFS.
- **Seed search.** We searched generator seeds 0..60,000 for byte matches with the grading cases.
- **Native runs.** We ran the unchanged evaluator in the pinned judge image with `docker run --network none --memory 2g --cpus 4`. The logs were then graded by the repository harness. A fixed-CPU-work solution was also run at `--cpus 2` and at `--cpus 8`.
- **Original identity.**
  - Judge image: `seededge/edgebench.judge.grid_turing_robot@sha256:f67864ad75a3a2af0f7904a05a30b888f66ce2ed5c1f3cac7d7482e578a296c3`.
  - `/tmp/eval_grid_turing_robot.py`: sha256 `99c9c55d618f6bf989389948b3ce3836e4d0ed85d410de78273de76571e717d6`.
  - `tools/src/verifier.py`: `49c99062067d486e2a5466b2d057540bbbeac70de835ae39c0f6026db08039f3`.
  - `tools/bin/tester`: `3928c31acf22b34a350be764423163d7bbe9a6257c9d749078b07ad63217ddad`.
  - Shipped `solution.py`: `9c42b54a…`.

## What we found

**Confirmed: scoring is correct for honest solutions.**

- The differential test found 0 disagreements between the oracle and the original verifier.
- Both give a sum of 94,092 for the known-good solution on all 50 cases.
- All 50 cases are valid.
- No grading case matches generator output for seeds 0..60,000, so the cases are not in the 0..10000 range the solvers may use locally.

**Not material: the earlier "reflected score" hold.** The earlier held concern was about scorer isolation, which is outside this release's scope. It does not change any honest result.

**Confirmed, narrower: (a) one failed case voids the submission.** The prompt does not say this. If a single case crashes, times out or prints malformed output, that case gets an infinite score. The harness then marks the whole submission unrankable.

| solution (all honest) | evaluator per-case result | TOTAL_SCORE | harness valid | normalized |
|---|---|---|---|---|
| `good_stepstate` (known-good) | 50 OK | 94,092 | yes | 19.80 |
| `fail_partial` (well-formed; route cut in half on case 0000) | 50 OK | 202,310 | yes | 19.56 |
| `fail_crash` (raises on case 0000 only) | 0000 RE score=inf | inf | **no** | None |
| `fail_tle` (sleeps 40 s on case 0000) | 0000 TLE score=inf | inf | no | None |

Failures never help a minimizing solver. A failed case is not dropped and is not counted as 0.

Maximum score effect: at most about 20 normalized points for the affected submission, compared with charging that case its smallest penalty. The effect is 0 if an earlier round was valid, because selection keeps the best valid round.

**Confirmed, narrower: (b) offset in the baseline anchor.** The configured rescale baseline is 9,025,986. The shipped do-nothing baseline actually totals 7,744,909 on the 50 grading cases, so it normalizes to **2.84** instead of 0.

Maximum score effect: at most 2.84 points, and only between the baseline and rank30 (the 0–20 band).

**Confirmed, narrower: (c) results depend on the judge's CPU count.** Cases run eight at a time under a 30 s wall-clock limit, and the task pins no `cpu_limit`. A solution doing a fixed 12 s of CPU work per case gave different results on the two allocations:

- at `--cpus 8`: 50 OK, normalized 19.80;
- at `--cpus 2`: **48 TLE**, so the submission was invalid.

Maximum effect: up to the full score for fixed-work solutions on a judge with fewer than about 8 CPUs. Invalidation was measured only at 2 CPUs with one 12 s-per-case solution; 3 to 7 CPUs were not tested. This is a condition of the execution environment, not an error in the task's rules.

## Note for users

No repair. The note says:

1. The configured baseline (9,025,986) is higher than the shipped baseline's actual 7,744,909, so the shipped baseline earns 2.84 points instead of 0. Maximum effect: 2.84 points.
2. One crashed, timed-out or malformed case makes the whole submission unrankable. The prompt does not say so. Maximum effect: about 20 normalized points for the affected submission.
3. Results are reproducible only with at least 8 dedicated judge CPUs, or with evaluator parallelism no greater than the CPUs available. Maximum effect: up to the full score for fixed-work solutions on a judge with fewer than about 8 CPUs.

An optional v2 could pin `cpu_limit` at 8 or more, document the failure rule or replace it with a finite per-case penalty, and set the baseline to 7,744,909. None of these is required to retain the task.

## Limits and what was not run

- No model or solver re-runs were done. Score effects are shown only on authored controls and counterexamples.
- Native runs used local Docker at `--cpus 4`, `--cpus 2` and `--cpus 8`, with `--memory 2g`. The production judge's CPU allocation is unknown.
- Only simple honest solutions were tested. Whether rank1 = 1,575 is achievable was not checked, and the sources of the rank1 and rank30 anchors were not traced.
- The random tables in the differential test produced only partial routes. Agreement on full routes rests on the known-good solution and one half-route case.
- The seed search covered gen.py seeds 0..60,000 only.
- Scorer isolation was not analysed. It is outside scope.

## Reproduce

- Native runs: `evidence/scripts/grid_turing_robot/run_native.sh`, then `grade.py` (output in `native/grade_out.txt`; CPU runs in `native_cpus2/` and `native_cpus8/`)
- Oracle, data checks and tiny-board search: `evidence/scripts/grid_turing_robot/oracle.py` (outputs `data_out.txt` and `brute_out.txt`)
- Differential test: `evidence/scripts/grid_turing_robot/fuzz_agree.py` (output `fuzz_out.txt`)
- Seed search: `evidence/scripts/grid_turing_robot/seeds_header.py` (output `seeds_header_out.txt`)
