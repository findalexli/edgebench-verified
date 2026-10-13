# Warehouse Forklift Routing, fixed version: the grader's time limit matches the promised 30 s per test case, with a whole CPU per input

This judge-image repair also requires the [opt-in final-drain harness overlay](../harness-final-drain-v1/README.md) to prevent final results from being collected before long evaluations finish. The overlay has paired component tests; a full harness run remains unverified.

## What this fixes

The prompt promises 30 s per test case, which is 150 s for each five-case input, but the original grader allows only 60 s per input, and one timeout costs the whole submission. The fixed grader allows the promised 150 s per input. It also runs at most as many inputs at once as the grader has CPUs: the original runs 8 at once, so on the publisher's 4-CPU leaderboard setting each input gets about half a CPU, and a solver needing more than about 75 s of CPU per input would still time out under the 150 s limit. The score scale is unchanged, and its ceiling of about 30.6 out of 100 (30.3 before display rounding), which follows from a Lean-checked lower bound on the raw total, is documented.

## What changes

### The problem in detail

See the [review](../../evidence/reviews/warehouse_forklift_routing.md), H5. The prompt and the
README both promise "Time limit: 30 seconds per test case", and both say "T=5 test cases per
input". Each of the 50 grading inputs therefore carries a promised budget of 5 × 30 s = 150 s. The
grader `/tmp/eval_warehouse_manager.py` runs `solution.py` once per input with
`TIME_LIMIT = 60`, which is 12 s per test case on average. A timeout scores `inf`, so a single timeout makes
the total `inf`, which EdgeBench's harness ranks below any finished submission and gives no score out of 100. In the review's
run on the original grader, an honest solver that spent 13 s per test case (less than half the promise) got
50/50 TLE (time limit exceeded), a total of `inf` and no score. The local tools give no warning, because `tools/bin/tester`
only scores an output file and does not time anything.

**CPU contention (found and fixed 2026-10-12).** The limit is wall-clock time, and the grader runs
`ProcessPoolExecutor(max_workers=min(8, len(case_files)))` whatever the CPU count. The publisher's leaderboard
setting gives the grader 4 CPUs (`judge_cpu_limit: 4`, quoted in [`evidence/impact/edgebench-leaderboard-config.md`](../../evidence/impact/edgebench-leaderboard-config.md)), so each input gets about half a CPU. Under the original
60 s limit that voids a single-threaded solver above about 30 s of CPU per input. Measured at
`--cpus 4` on the earlier fixed version (150 s, 8 at once): valid solutions doing a fixed 80 s or 140 s of CPU
work per input got 2 OK + 48 TLE and no score (`evidence/runs/warehouse_forklift_routing-v2-cpu4-b` and `-a`).
The same problem affects the grid_turing_robot and molecular_self_assembly graders and is fixed the same way there.

### Exact change

One file is changed, `/tmp/eval_warehouse_manager.py` (`repair.patch`), in two places:

1. `TIME_LIMIT = 60` becomes `TIME_LIMIT = 150`. The value comes straight from the prompt: 30 s per test
   case × T=5 test cases per input.
2. A new function `cpu_quota_workers()` reads the grader's CPU quota from the cgroup (`/sys/fs/cgroup/cpu.max`,
   or `cpu.cfs_quota_us` / `cpu.cfs_period_us` on cgroup v1), rounds it down to whole CPUs, falls back to
   `os.cpu_count()` when there is no quota, and keeps the result between 1 and 8. The pool line becomes
   `ProcessPoolExecutor(max_workers=min(cpu_quota_workers(), len(case_files)))`. `docker run --cpus N` and the
   publisher's k8s backend both set this quota (the harness passes `nano_cpus`, `sforge/harness/config.py:327`).

The file keeps mode 0755 and is 3247 bytes instead of 2339 (sha256 `afccb3bb…5a76`). The earlier fixed
version, with change 1 only (2340 bytes, sha256 `eff6a69b…7b95`), is superseded; `source-lock.json` records
both. In the task JSON, only `judge.image_tag` changes (`task.json.in`, `d342863c29cc` →
`d342863c29cc-ebv-v2.1`). Tag `d342863c29cc-ebv-v2` (v1.0 package) is superseded; rebuild. Nothing changes in the work
image, prompt, README, tester, cases, parser or selection.

### Grading time stays inside `eval_timeout`

`eval_timeout` stays at 3600 s. With 4 CPUs the fixed grader runs 50 inputs in ⌈50/4⌉ = 13 rounds; the worst
case is 13 × (150 s + 30 s tester timeout) = 2340 s, well under 3600 s. In the paired runs at 4 CPUs, a solution
using 140 s of CPU per input took 1825.2 s in total and one sleeping 135 s per input took 1757.4 s
(`paired/results.md`). 3 CPUs give 17 rounds (17 × 150 s = 2550 s, plus testers); with 2 CPUs, 25 rounds × 150 s =
3750 s exceed 3600 s, so on a 2-CPU grader the 3600 s `eval_timeout` caps the usable time at about 144 s per input.

### Why this is the smallest change

The timeout feeds only the `subprocess.run(..., timeout=TIME_LIMIT)` call for the
solution. Any run that finished within 60 s under the original version finishes, and is scored, the same way under
the fixed version: same stdout, same tester and same totals. The only runs whose result changes are those
that took between 60 and 150 s. The original marked them TLE/`inf`, and the fixed version scores their output.
The parallelism change matters only on a grader with fewer than 8 CPUs; with 8 or more it still runs 8 at once,
as the original does. It keeps the limit a wall-clock limit and changes only how many inputs share the CPUs. The other
fix the review suggests, rewording the prompt to "60 s per input", would make the task consistent by withdrawing a promise that solvers have already been shown. Raising the limit keeps
the promise that was made.

### Are scores comparable?

Scores from the fixed version equal those from the original for every submission whose solver finishes
each input within 60 s. They are not comparable for a submission that takes 60–150 s on any
input: the original gives the whole submission no score, while the fixed version scores it. On a grader with fewer
than 8 CPUs, a solver that searches until a wall-clock deadline also gets more CPU per input under the fixed version
(1 CPU instead of about 0.5 at 4 CPUs), so its score can improve. A run near the limit can also
change outcome with machine speed, as in any timed task.

### Score scale: kept unchanged, with a proven ceiling (decision 2026-10-12)

The reference points of the `piecewise_log_min` score scale are unchanged in the fixed version. A Lean 4 proof, checked by Lean's kernel and
recompiled independently ([review](../../evidence/reviews/warehouse_lower_bound_lean.md)), shows that every valid submission
has a raw TOTAL ≥ 198283458104808536/278277680055375 ≈ 712.538 on these 50 inputs (lower is better). The rank1 (395.80)
and super_anchor (293.51) reference points are therefore out of reach, and **no valid submission can score
above ≈30.3 out of 100**, or ≈30.6 once the tester's 1-decimal display rounding is included (lowest
reachable TOTAL 710.2, rescale 30.586; `evidence/scripts/warehouse_forklift_routing/lean_bound/recompute_total.out.txt`).
The step from the raw bound to the 0–100 ceiling uses the harness's floating-point rescale, not Lean. It is
an upper bound; the best reachable score is not known. The scale is not given new reference points: the proven floor is a lower bound, not a known
optimum. Putting 100 there would move the original rank-30 reference point from 20 to 96.5, which would be an
invented recalibration. Keeping the reference points keeps scores comparable with the original version. The release notes
state the ceiling (≈30.3, ≈30.6 after display rounding), as is done for the disclosed 30-point cap of the Bipedal task.

## How it was checked

Side-by-side run of the original and fixed graders: [paired/results.md](paired/results.md). In plain words: a generic valid test submission gets the same TOTAL of 46676.8 under both graders. Submissions with a bug, and the shipped starter, are rejected under both. A solver that uses 13 s per test case, within the promised budget, times out on all 50 inputs under the original grader and is scored normally (TOTAL 46676.8) under the fixed one. At the publisher's 4 CPUs, solvers doing 80 s or 140 s of real CPU work per input time out on 48 of 50 inputs under the earlier fixed version (150 s, 8 at once) and on all 50 under the original, and pass 50/50 under the current fixed version; at 8 CPUs the earlier and current fixed versions give the same result. All controls were re-run at 4 CPUs with the current fixed version.

## Build and use

Git does not contain any file copied from the EdgeBench images. It holds only our diff (`repair.patch`) and the recipe for rebuilding the full files. Regenerate them, then build:

```bash
./materialize.sh && docker build -t ebv/warehouse_forklift_routing-judge:v2 .
```

`materialize.sh` takes the following steps:

1. Pull the pinned image(s) by digest, unless already present.
2. Extract the original files with `docker create` and `docker cp`. No container runs in this step.
3. Check each original against `source-lock.json`.
4. Apply `repair.patch` with `patch -p1`.
5. Verify the sha256 of every file under `files/` (and `orig/`) against `source-lock.json` → `materialize.outputs`. Any mismatch fails loudly.

After that, the `Dockerfile` builds without changes. Regenerated files keep the file mode they have in the image.
See `../MATERIALIZE-CHECK.md` for how each package was verified.

## Limits

- The fixed grader reads its CPU quota from the cgroup (`cpu.max`). This was tested with `docker run --cpus` only, not inside a Kubernetes pod, which is the backend EdgeBench's leaderboard settings use.
- The upstream harness waits only 900 s for final grading and can omit a repaired evaluation (1,825.2 s measured). Use the separate [final-drain harness overlay](../harness-final-drain-v1/README.md) with this judge package: it waits for terminal history with a queue-aware deadline and fails visibly on incomplete collection. Deterministic patched-source tests pass; a complete Docker/Kubernetes run through the overlay is still unverified. The image-only repair does not fix this host-side boundary. Claims that every originally scored submission fits the 900 s drain were not established and are withdrawn.
- This fixes only the time limit and its CPU share; the ceiling of the score scale is documented, not changed (above).
- The `time_budget` and `near_limit` submissions use `sleep`; the `cpu80` and `cpu140` submissions do real
  single-thread CPU work. Multi-threaded solvers were not tested.
- The CPU quota is rounded down: a grader with 2.5 CPUs runs 2 inputs at once. With fewer than 3 grader CPUs the
  3600 s `eval_timeout`, not the 150 s per input, becomes the binding limit (above).
- A 140 s CPU solution took at most 140.58 s per input at 4 CPUs under the fixed version, so the margin to the
  150 s limit is about 9 s; Python start-up and the tester are inside the per-input budget.
- The valid test submission is generic and weak (0.0 out of 100). The score of a competitive solver is
  not measured.
- The side-by-side job for the time limit was run three times on fresh E2B workers at `--cpus 2`
  (`evidence/runs/warehouse_forklift_routing-v2-paired-b`, `-rep2`, `-rep3`, each `status: exit=0`), with the same
  result for every arm, before the parallelism change. The CPU runs (`-cpu4-a` to `-d`) ran three times each (`-rep2`, `-rep3`), with identical results (`paired/results.md`, Repeatability).
