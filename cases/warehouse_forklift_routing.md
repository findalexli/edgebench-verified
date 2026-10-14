# Warehouse Forklift Routing (`warehouse_forklift_routing`)

**Outcome:** Checker fix tested; a needed change to how EdgeBench waits for the last results is tested in parts, not yet in a full run. <mark>The grader gives 60 s per five-case input while the prompt promises 30 s per test case, and on the publisher's 4-CPU grader it runs 8 inputs at once, so each input gets about half a CPU; the fixed version raises the limit to the promised 150 s per input, runs at most as many inputs at once as the grader has CPUs, keeps the score scale unchanged and documents a ceiling of about 30.6 points out of 100 (30.3 before display rounding), which follows from a Lean-checked lower bound on the raw total.</mark>

![Time bars per input from 0 to 150 s. Original checker: about 30 s of computing, then the 60 s limit, and the promised range from 60 to 150 s marked as timed out. Fixed checker: a full 150 s bar, at most 4 inputs at once with one CPU each. A table shows three test submissions (13 s per case, 80 s and 140 s of computing per input): all 50 inputs time out with no score on the original checker, all 50 scored on the fixed one. A box notes the documented, unfixed ceiling of about 30.6 out of 100 (30.3 before rounding).](figures/warehouse_forklift_routing.svg)

*Warehouse Forklift Routing solutions that use the time the instructions promise get no score. The instructions promise 30 s per test case, or 150 s per five-case input, but the original checker stops each input at 60 s. On EdgeBench's 4-CPU setting it also runs 8 inputs at once, so each gets only about 30 s of computing, and one timeout leaves the whole submission without a score. Test submissions that wait 13 s per case or compute 80 or 140 s per input got no score under the original checker. Under the fixed one, which allows 150 s and runs no more inputs at once than it has CPUs, all 50 inputs were scored. (The fix also needs a longer final wait in EdgeBench's runner, which is tested only in parts.) A separate limit is documented, not fixed: no valid answer can score above about 30.6 out of 100.*

## What the task asks

The task is an adaptation of the CodeChef problem WAREHOUS. The solver must output forklift command strings that store R·C−1 arriving goods on an R x C grid and then dispatch them in order. The goal is to "Minimize the total instruction string length". The prompt states "T=5 test cases per input" and "Time limit: 30 seconds per test case". The README says "Final score = sum of per-input average scores." Lower raw results are better. Category: Combinatorial Optimization.

## What goes wrong

### 1. The time limit is stricter than promised

The prompt promises 30 s per test case, with 5 test cases per input, which is 150 s per input. The grader sets `TIME_LIMIT = 60` for the whole input and runs 8 inputs in parallel. A timeout scores `inf`, so a single timeout makes `TOTAL_SCORE` `inf`. EdgeBench's harness keeps such a result (`valid: true`) with raw score `inf`, gives it no score out of 100 (`rescale_score` returns None for a non-finite total, `sforge/harness/score_rescale.py:75-76`), and prefers any finished submission to it under `minimize`. A single timeout therefore costs the whole submission.

On the original grader, a test submission with a time budget (it sleeps) spends 13 s per test case, less than half the promised limit. It gets 50 TLE (time limit exceeded), a total of `inf` and no score, where the prompt leads it to expect all 50 inputs scored.

The local tools give no warning, because `tools/bin/tester` only scores an output file. A solver that follows the promised budget loses its whole score.

On the publisher's 4-CPU grader, the original's 60 s per input is about 30 s of CPU; the same fixed version corrects this. The limit is wall-clock time, and the grader runs `ProcessPoolExecutor(max_workers=min(8, len(case_files)))` whatever the CPU count. EdgeBench's leaderboard settings give this grader 4 CPUs (the default, with no override for this task; quoted in [`evidence/impact/edgebench-leaderboard-config.md`](../evidence/impact/edgebench-leaderboard-config.md)), so each of 8 running inputs gets about half a CPU. Under the original grader a single-threaded solver therefore loses its whole score above about 30 s of CPU per input (60 s of wall time at half a CPU; arithmetic, the measured arms all exceed it). Raising the limit to 150 s alone would still cut such a solver at about 75 s of CPU. We measured this at `--cpus 4` with that limit-only version (150 s, 8 at once). Valid solutions doing a fixed 80 s or 140 s of CPU work per input got 2 OK + 48 TLE and no score (`evidence/runs/warehouse_forklift_routing-v2-cpu4-b/result/out/summary.txt`, `-cpu4-a`). The original grader gives both 50 TLE (`-cpu4-b`, `-cpu4-c`).

### 2. The reference points of the score scale cannot be reached

Every string the tester accepts satisfies S ≥ 2RC(R+C−1) − 6(R+C−2) − 2, so every valid per-case score is ≥ 20 − 6(R+C−2)/(R+C−1). On the 50 grading inputs every valid TOTAL is ≥ 198283458104808536/278277680055375 ≈ 712.538. That stays above the "rank1" reference point even after the rounding used for display.

TOTAL ≥ 712.538 > rank1 395.80, and the "super_anchor" reference point (293.51) is also below it. Under the task's own score scale, no valid submission can score above about 30.3 out of 100 (30.308 at the exact bound; 30.586 at 710.2, the lowest total possible after display rounding).

The 0 to 100 scale therefore has a ceiling well below 100. The order of submissions is preserved.

### Checked and found not to change scores

- The tester lets an empty forklift enter occupied cells. This rule is looser than the original CodeChef rule, but the prompt discloses it. Solvers that follow either rule are accepted.
- The diagonal construction scores exactly 20.0. Adding an E,W detour gives 20.2.
- The tester prints each input's score to 1 decimal place. This shifts TOTAL by at most 2.5 raw (the lowest reachable displayed TOTAL is 710.2), or about 0.3 points out of 100 at the ceiling (30.308 → 30.586, `evidence/scripts/warehouse_forklift_routing/lean_bound/recompute_total.out.txt`).
- Failures add up to `inf`, so the submission gets no score, which matches the README's "sum".
- Scoring is deterministic.
- The data are well-formed. Replaying generator seeds 0..300,000 reproduced none of the 50 grading files, so the grading inputs are not in the public seed range.

## How much it matters

- Because of the time limit, a solver that takes 60 to 150 s on any input, within the promised budget, loses its whole score. On the publisher's 4-CPU grader the same holds for a single-threaded solver using more than about 30 s of CPU on any input, because each of the 8 inputs running at once gets about half a CPU. Faster solvers are unaffected. A solver that searches until a wall-clock deadline (below 60 s) gets about half a CPU per input at 4 CPUs; we did not measure how much more it would score with a whole CPU.
- Because of the ceiling, every solver's score out of 100 is capped at about 30.6 (30.3 before display rounding). This is an upper bound; the best reachable score is not known and may be lower (Limits).

## The fix

The fixed version makes two changes in `/tmp/eval_warehouse_manager.py`. First, `TIME_LIMIT = 60` becomes `TIME_LIMIT = 150`. The value is 30 s per test case × T=5, as the prompt promises. Second, a new function `cpu_quota_workers()` reads the grader's CPU quota from the cgroup (`cpu.max`, or the cgroup v1 quota and period), rounds it down to whole CPUs, falls back to `os.cpu_count()` when there is no quota, and keeps the result between 1 and 8; the pool becomes `ProcessPoolExecutor(max_workers=min(cpu_quota_workers(), len(case_files)))`. At `--cpus 1/2/4/8` the fixed grader runs 1/2/4/8 inputs at once (`evidence/runs/warehouse_forklift_routing-v2-cpu4-a/result/out/v2_workers.txt`); with 8 or more CPUs it runs 8 at once, as the original does. `eval_timeout` stays at 3600. The earlier version of this fix changed only the time limit (sha256 `eff6a69b…7b95`); the current fixed grader is sha256 `afccb3bb…5a76`. The task JSON changes only `judge.image_tag`. The work image, prompt, README, tester, cases, parser, selection and score scale are unchanged.

The fix keeps the `piecewise_log_min` reference points instead of replacing them. The proven floor is a lower bound, not a known optimum, so putting 100 there would be an invented recalibration. Keeping the reference points keeps scores comparable with the original version. The release notes state the ceiling (≈30.3 at the exact bound, ≈30.6 after display rounding).

| Submission | Role | Original grader | Fixed grader |
| --- | --- | --- | --- |
| generic valid test submission | correct | OK 50/50, TOTAL 46676.8 | OK 50/50, TOTAL 46676.8 |
| one ordinary bug | invalid | 49 OK + 1 WA → inf | 49 OK + 1 WA → inf |
| shipped starter | invalid | 50 WA → inf | 50 WA → inf |
| **13 s per test case (uses the promised budget)** | **shows the problem** | **50 TLE → inf** | **50 OK, TOTAL 46676.8** |
| near the 150 s per-input limit | shows the problem | 50 TLE → inf | 50 OK, TOTAL 46676.8 |

(WA = wrong answer, TLE = time limit exceeded. The table comes from `repairs/warehouse_forklift_routing-v2/paired/results.md`, "Paired run", three runs at `--cpus 2` with the earlier, limit-only fixed version. We re-ran all five rows at `--cpus 4` with the current fixed version and got the same results (`evidence/runs/warehouse_forklift_routing-v2-cpu4-c`, `-cpu4-d`).)

The CPU-share runs at the publisher's 4 CPUs are in `evidence/runs/warehouse_forklift_routing-v2-cpu4-a` to `-d`, `result/out/summary.txt`.

| Submission | CPUs | Original grader | Limit-only fix (150 s, 8 at once) | Fixed version |
| --- | ---: | --- | --- | --- |
| **80 s of CPU per input** | 4 | 50 TLE → inf | **2 OK + 48 TLE → inf** | **50 OK, TOTAL 46676.8** |
| **140 s of CPU per input** | 4 | 50 TLE → inf | **2 OK + 48 TLE → inf** | **50 OK, TOTAL 46676.8** |
| 80 s of CPU per input | 8 | not run | 50 OK, TOTAL 46676.8 | 50 OK, TOTAL 46676.8 |

Under the fixed version the slowest 140 s input took 140.58 s from start to end. Grading at 4 CPUs took at most 1825.2 s, inside the 3600 s `eval_timeout`; the worst case is ⌈50/4⌉ = 13 rounds × (150 s + 30 s tester timeout) = 2340 s.

Scores from the fixed version equal those from the original for every deterministic submission whose solver finishes each input within 60 s on the grader used. The two are not comparable for a submission that takes 60 to 150 s on any input, because the original invalidates the whole submission while the fixed version scores it. On a grader with fewer than 8 CPUs a solver that searches until a wall-clock deadline gets more CPU per input under the fixed version (1 CPU instead of about 0.5 at 4 CPUs), so its scores under the two graders are not comparable. A run near the limit can also change outcome with machine speed, as in any timed task. Because the reference points are unchanged, the 0 to 100 scale (including the ceiling of ≈30.3, or ≈30.6 after display rounding) is the same in both versions.

## How we checked it

- We ran the verbatim `eval_cmd` in the original grader image, pinned by digest, with `--network none` and the solution mounted read-only, and graded the result with the repository's harness. The test submissions were a generic valid one, a repeat of it, the shipped starter, one with an ordinary bug, and solvers with a time budget. 16 hand-written outputs ran through the tester in the grader image with 0 mismatches against the oracle's predictions.
- As an independent oracle, we wrote a simulator from the statement text, with exact `Fraction` scoring and two rule modes (the prompt's rule and the stricter CodeChef rule). A differential test against the original tester program used 20,000 random command strings plus 2,000 outputs of the test submissions (half of them with one-character edits); all agreed. Exact optima for tiny grids came from Dijkstra's shortest-path search on 2x2, 2x3 and 3x2, under both rule sets. Data checks covered all 50 grading inputs (250 subcases) and generator seeds 0..300,000.
- For the formal check in Lean 4, the per-case bound is the theorem `EbvWarehouse.lower_bound` in `formal/lean/ebv/Ebv/WarehouseBound.lean`. Lean's kernel checked it under Lean v4.34.1 and Mathlib `d13f23b7`, with no `sorry` and no `native_decide`, and we recompiled it independently. It depends only on Lean's standard axioms `[propext, Classical.choice, Quot.sound]`. `EbvWarehouse.score_bound` gives the per-case score bound. In `Ebv/WarehouseData.lean`, `totalLB_eq` and `totalLB_gt` give the bound on TOTAL, and `displayed_gt_rank1` covers display rounding. The theorem is not vacuous. The model accepts a 42-character optimum (`opt23_accepted`), and Lean proves that a stronger bound without the −6(R+C−2) term is false (`too_strong_bound_false`). That stronger bound fails on 239 of 248 optima found by brute force. The proof does not use the guard on moving into occupied cells, so it holds under both the prompt's rule and the CodeChef rule.
- We did the side-by-side run of the original and the limit-only fixed version at `--cpus 2` three times, and no result changed (`data/paired-repeatability.md`). The CPU-share runs at `--cpus 4` and `--cpus 8` (`evidence/runs/warehouse_forklift_routing-v2-cpu4-a` to `-d`, each `status: exit=0`) ran three times each (`-rep2`, `-rep3`), with identical OK/TLE/WA/RE counts and totals (`repairs/warehouse_forklift_routing-v2/paired/results.md`, Repeatability).

## Limits

- The fixed grader reads its CPU quota from the cgroup (`cpu.max`). We tested this with `docker run --cpus` only, not inside a Kubernetes pod, which is the backend EdgeBench's leaderboard settings use.
- Without a cgroup quota the fixed grader falls back to `os.cpu_count()`, which counts all of the host's CPUs, not the ones the grader may use (`os.sched_getaffinity`). Under a CPU-set limit with no quota (for example `docker run --cpuset-cpus`), or where the pod cannot see its own `cpu.max`, it can still run more cases at once than it has CPUs, as the original does. Using the affinity count would need a new paired run, so we did not change it.
- The upstream harness waits only 900 s for final grading and can omit a repaired evaluation (1,825.2 s measured). Use the separate [final-drain harness overlay](../repairs/harness-final-drain-v1/README.md) with this judge package. The overlay waits for terminal history with a queue-aware deadline and fails visibly on incomplete collection. Deterministic patched-source tests pass; a complete Docker/Kubernetes run through the overlay is still unverified. The overlay changes final collection for every task run through its materialized harness, not only Warehouse, and can wait up to `300 + n·(eval_timeout + 300)` s (4,200 s for one pending Warehouse submission) while the work sandbox stays allocated; see its README. The image-only repair does not fix this host-side boundary. We did not establish that every originally scored submission fits the 900 s drain, and we withdraw that claim.
- We ran no AI model or solver. The effects shown come only from the test submissions we wrote.
- The valid test submission is generic and weak (0.0 out of 100). We built no competitive solver, so we did not measure the best score reachable between the floor (712.5 raw) and about 1000 raw (the diagonal construction).
- The test submissions with a time budget use `sleep`; they show that the limit is enforced per input as promised. We show the CPU contention with single-threaded submissions doing a fixed 80 s or 140 s of CPU work per input, and did not test multi-threaded solvers or 3, 5, 6 and 7 CPUs.
- At 4 CPUs the fixed version leaves about 9 s of margin for 140 s of CPU per input (slowest input 140.58 s).
- With fewer than 3 grader CPUs the 3600 s `eval_timeout` binds before the 150 s per input. At 2 CPUs, 25 rounds × 150 s = 3750 s, so only about 144 s per input is usable. The quota is rounded down, so 2.5 CPUs run 2 inputs at once.
- The match between the Lean model and the tester is a line-by-line mapping done by hand, backed by a runtime differential test on 294 strings with 0 mismatches. It is not a kernel-checked proof. We checked the case hypotheses (permutation, last arrival ≠ 1) and the extraction of (R,C) in Python. The ceiling on the 0 to 100 scale comes from the harness's floating-point conversion code, not from Lean.
- We do not know where the reference points come from.
- Scorer isolation is outside this release's scope (an EdgeBench design choice); findings that affect solvers that follow the rules are reported above.

## Reproduce

- Grader image: `sha256:ac7fdf03…`.
- Checks on the host: `evidence/scripts/warehouse_forklift_routing/` (`oracle_sim.py`, `diff_fuzz.py`, `authored_cases.py`, `data_and_bound.py`, `tiny_optimum.py`, `native/run_native.sh`, `harness_grade.py`; checksums in `SHA256SUMS`).
- Lean bound: `evidence/formal/lean/ebv/Ebv/Warehouse{Bound,Check,Data}.lean`, compiled with `evidence/scripts/warehouse_forklift_routing/lean_bound/compile_capped.sh`. Exact totals: `lean_bound/recompute_total.py`. Brute force: `lean_bound/brute_force.py`.
- Side-by-side run: `repairs/warehouse_forklift_routing-v2/paired/run.sh` (as run: `evidence/runs/warehouse_forklift_routing-v2-paired-b/run.sh`). CPU-share runs: `repairs/warehouse_forklift_routing-v2/paired/run-cpu4.sh` (as run: `evidence/runs/warehouse_forklift_routing-v2-cpu4-a/run.sh` to `-d`).
- Pinned identity: grader image `seededge/edgebench.judge.warehouse_forklift_routing@sha256:ac7fdf03…`; `/tmp/eval_warehouse_manager.py` sha256 `c5ff0c26…`; `tools/bin/tester` sha256 `277f4841…`; the 50 grading inputs (concatenated) sha256 `04b8cd29…`; task JSON sha256 `78002570…`.
- Supporting records: `repairs/warehouse_forklift_routing-v2/` (the folder holding the fixed version: README, `repair.patch`, `source-lock.json`), `evidence/reviews/warehouse_forklift_routing.md`, `evidence/reviews/warehouse_lower_bound_lean.md`.
