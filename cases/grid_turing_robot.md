# Grid Turing Robot (`grid_turing_robot`)

**Outcome:** Kept, with a note. <mark>Honest solutions are scored correctly, but three conditions need a note: an offset in the score scale's starting point (2.84 points), the unstated rule that one failed case voids the submission (about 20 points), and dependence on the grader's CPU count (up to the full score on a grader with fewer than about 8 CPUs).</mark>

## What the task asks

The solver writes a rule table, like the transition table of a Turing machine, that drives a robot over a grid. The task text says: "Your solution is scored on **50 fixed test cases**. Final score = sum of individual case scores. **Lower is better.**" The README gives the score for one case as "If V = K: Score = C + Q", with the penalty "If V < K: Score = 2N^4 + (K − V) × N^2", and a "Time limit | 30 seconds / test case". Category: Combinatorial Optimization.

## What we checked

The scoring rules are implemented correctly. The issues are about edge conditions.

**(a) One failed case voids the submission.** The task text does not say this. If a single case crashes, times out or prints malformed output, that case gets an infinite score, and the harness marks the whole submission as unrankable.

| Solution (all honest) | Grader result per case | TOTAL_SCORE | Valid for the harness | Score out of 100 |
|---|---|---|---|---|
| `good_stepstate` (known to be good) | 50 OK | 94,092 | yes | 19.80 |
| `fail_partial` (well-formed; route cut in half on case 0000) | 50 OK | 202,310 | yes | 19.56 |
| `fail_crash` (raises an error on case 0000 only) | 0000 RE score=inf | inf | **no** | None |
| `fail_tle` (sleeps 40 s on case 0000) | 0000 TLE score=inf | inf | no | None |

A failure never helps a solver, because lower is better. A failed case is not dropped and is not counted as 0.

**(b) Offset in the starting point of the score scale.** The configured reference point for 0 (the baseline) is 9,025,986. The shipped do-nothing starting solution actually totals 7,744,909 on the 50 grading cases. It therefore scores **2.84** out of 100 instead of 0.

**(c) Results depend on the grader's CPU count.** Cases run eight at a time under a 30 s wall-clock limit, and the task sets no `cpu_limit`. A solution doing a fixed 12 s of CPU work per case gave:

- at `--cpus 8`: 50 OK, score 19.80 out of 100;
- at `--cpus 2`: **48 TLE** (time limit exceeded), so the submission was invalid.

This is a condition of the execution environment, not an error in the task's rules.

The note that ships with the task:

1. The configured baseline (9,025,986) is higher than the shipped baseline's actual 7,744,909, so the shipped baseline earns 2.84 points instead of 0.
2. One crashed, timed-out or malformed case makes the whole submission unrankable.
3. Results are reproducible only with at least 8 dedicated judge CPUs, or with evaluator parallelism no greater than the CPUs available.

## How much it matters

- (a) At most about 20 points out of 100 for the affected submission, compared with charging that case its smallest penalty. The effect is 0 if an earlier submission in the run was valid, because the run keeps its best valid submission.
- (b) At most 2.84 points, and only between the reference point for 0 and the reference point for the 30th-ranked level (rank30), that is, the 0–20 band.
- (c) Up to the full score for solutions with a fixed amount of work, on a grader with fewer than about 8 CPUs. Invalidation was measured only at 2 CPUs, with one solution doing 12 s of work per case. 3 to 7 CPUs were not tested.

No change is made; the note above ships with the task. An optional fixed version could set `cpu_limit` to 8 or more, document the failure rule or replace it with a finite penalty per case, and set the baseline to 7,744,909. None of these is required to keep the task.

## How we checked it

- **Original grader in the original public image, pinned by digest.** The unchanged grader ran in the grader image with `docker run --network none --memory 2g --cpus 4`, and the repository harness graded the logs. The solution with fixed CPU work was also run at `--cpus 2` and `--cpus 8`.
- **Independent implementation.** A parser, simulator and scorer were written from the README text alone, without importing the task's verifier. A comparison over 3,000 random rule tables on the 50 grading cases found 0 disagreements. Both implementations give a sum of 94,092 for the known-good solution on all 50 cases.
- **Exhaustive search.** Every rule table with C+Q ≤ 5 was searched on tiny boards to confirm the bound on the minimum cost.
- **Data checks.** All 50 cases are valid: N and K are in range, walls are well-formed, the grid is fully connected, targets are distinct, and X ≤ T ≤ 2X by an independent breadth-first search (BFS).
- **Seed search.** No grading case matches generator output for seeds 0..60,000. The cases are therefore not in the 0..10000 range that solvers may use locally.

## Limits

- No AI model or solver runs were made. Score effects are shown only on test submissions and counterexamples that we wrote.
- Runs of the original grader used local Docker at `--cpus 4`, `--cpus 2` and `--cpus 8`, with `--memory 2g`. The CPU allocation of the production grader is unknown.
- Only simple honest solutions were tested. Whether the reference point for 100 (rank1 = 1,575) is achievable was not checked, and the sources of the rank1 and rank30 reference points were not traced.
- The random tables in the comparison produced only partial routes. Agreement on full routes rests on the known-good solution and one half-route case.
- The seed search covered gen.py seeds 0..60,000 only.

## Reproduce

- Grader image digest: `sha256:f67864ad75a3…`.
- Runs of the original grader: `evidence/scripts/grid_turing_robot/run_native.sh`, then `grade.py` (output in `native/grade_out.txt`; CPU runs in `native_cpus2/` and `native_cpus8/`).
- Independent implementation, data checks and tiny-board search: `evidence/scripts/grid_turing_robot/oracle.py` (outputs `data_out.txt` and `brute_out.txt`).
- Comparison over random rule tables: `evidence/scripts/grid_turing_robot/fuzz_agree.py` (output `fuzz_out.txt`).
- Seed search: `evidence/scripts/grid_turing_robot/seeds_header.py` (output `seeds_header_out.txt`).
