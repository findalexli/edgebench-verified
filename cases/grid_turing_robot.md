# Grid Turing Robot (`grid_turing_robot`)

**Decision:** Retain with note. Honest solutions are scored correctly, but three conditions need a note: the baseline anchor offset (2.84 points), the unstated rule that one failed case voids the submission (about 20 points), and dependence on the judge's CPU count (up to the full score on a judge with fewer than about 8 CPUs).

## What the task asks for

The solver writes a rule table that drives a robot over a grid. The prompt says: "Your solution is scored on **50 fixed test cases**. Final score = sum of individual case scores. **Lower is better.**" The README gives the per-case score as "If V = K: Score = C + Q", with the penalty "If V < K: Score = 2N^4 + (K − V) × N^2", and a "Time limit | 30 seconds / test case". Category: Combinatorial Optimization.

## What goes wrong

The scoring rules are implemented correctly. The issues are about edge conditions.

**(a) One failed case voids the submission.** The prompt does not say this. If a single case crashes, times out or prints malformed output, that case gets an infinite score, and the harness marks the whole submission unrankable.

| solution (all honest) | evaluator per-case result | TOTAL_SCORE | harness valid | normalized |
|---|---|---|---|---|
| `good_stepstate` (known-good) | 50 OK | 94,092 | yes | 19.80 |
| `fail_partial` (well-formed; route cut in half on case 0000) | 50 OK | 202,310 | yes | 19.56 |
| `fail_crash` (raises on case 0000 only) | 0000 RE score=inf | inf | **no** | None |
| `fail_tle` (sleeps 40 s on case 0000) | 0000 TLE score=inf | inf | no | None |

A failure never helps a minimizing solver. A failed case is not dropped and is not counted as 0.

**(b) Offset in the baseline anchor.** The configured rescale baseline is 9,025,986. The shipped do-nothing baseline actually totals 7,744,909 on the 50 grading cases, so it normalizes to **2.84** instead of 0.

**(c) Results depend on the judge's CPU count.** Cases run eight at a time under a 30 s wall-clock limit, and the task pins no `cpu_limit`. A solution doing a fixed 12 s of CPU work per case gave:

- at `--cpus 8`: 50 OK, normalized 19.80;
- at `--cpus 2`: **48 TLE**, so the submission was invalid.

This is a condition of the execution environment, not an error in the task's rules.

The note that ships with the task:

1. The configured baseline (9,025,986) is higher than the shipped baseline's actual 7,744,909, so the shipped baseline earns 2.84 points instead of 0.
2. One crashed, timed-out or malformed case makes the whole submission unrankable.
3. Results are reproducible only with at least 8 dedicated judge CPUs, or with evaluator parallelism no greater than the CPUs available.

## Impact

- (a) At most about 20 normalized points for the affected submission, compared with charging that case its smallest penalty. The effect is 0 if an earlier round was valid, because selection keeps the best valid round.
- (b) At most 2.84 points, and only between the baseline and rank30 (the 0–20 band).
- (c) Up to the full score for fixed-work solutions on a judge with fewer than about 8 CPUs. Invalidation was measured only at 2 CPUs with one 12 s-per-case solution; 3 to 7 CPUs were not tested.

## Fix (v2)

No change; the note above ships with the task. An optional v2 could pin `cpu_limit` at 8 or more, document the failure rule or replace it with a finite per-case penalty, and set the baseline to 7,744,909. None of these is required to retain the task.

## How we know

- **Original evaluator in the pinned image.** The unchanged evaluator ran in the judge image (`sha256:f67864ad75a3…`) with `docker run --network none --memory 2g --cpus 4`, and the logs were graded by the repository harness. The fixed-CPU-work solution was also run at `--cpus 2` and `--cpus 8`.
- **Independent oracle.** A parser, simulator and scorer were written from the README text alone, without importing the task's verifier. A differential test over 3,000 random rule tables on the 50 grading cases found 0 disagreements. Both give a sum of 94,092 for the known-good solution on all 50 cases.
- **Exhaustive search.** Every rule table with C+Q ≤ 5 was searched on tiny boards to confirm the minimum-cost bound.
- **Data checks.** All 50 cases are valid: N and K in range, well-formed walls and full grid connectivity, distinct targets, and X ≤ T ≤ 2X by an independent BFS.
- **Seed search.** No grading case matches generator output for seeds 0..60,000, so the cases are not in the 0..10000 range solvers may use locally.

## Limits

- No model or solver runs. Score effects are shown only on authored controls and counterexamples.
- Native runs used local Docker at `--cpus 4`, `--cpus 2` and `--cpus 8`, with `--memory 2g`. The production judge's CPU allocation is unknown.
- Only simple honest solutions were tested. Whether rank1 = 1,575 is achievable was not checked, and the sources of the rank1 and rank30 anchors were not traced.
- The random tables in the differential test produced only partial routes. Agreement on full routes rests on the known-good solution and one half-route case.
- The seed search covered gen.py seeds 0..60,000 only.

## Reproduce

- Native runs: `evidence/scripts/grid_turing_robot/run_native.sh`, then `grade.py` (output in `native/grade_out.txt`; CPU runs in `native_cpus2/` and `native_cpus8/`).
- Oracle, data checks and tiny-board search: `evidence/scripts/grid_turing_robot/oracle.py` (outputs `data_out.txt` and `brute_out.txt`).
- Differential test: `evidence/scripts/grid_turing_robot/fuzz_agree.py` (output `fuzz_out.txt`).
- Seed search: `evidence/scripts/grid_turing_robot/seeds_header.py` (output `seeds_header_out.txt`).
