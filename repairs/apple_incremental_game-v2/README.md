# Apple Incremental Game, fixed version: each case keeps a whole CPU for its 30 s limit

## What this fixes

The README promises "Time limit | 30 seconds / test case". The original grader runs 8 cases at once under a 30 s wall-clock limit per case, whatever the number of CPUs it is given. The publisher's leaderboard setting gives the grader 4 CPUs (`judge_cpu_limit: 4`, EdgeBench `examples/all-tasks-k8s/experiment.yaml` (quoted in [`evidence/impact/edgebench-leaderboard-config.md`](../../evidence/impact/edgebench-leaderboard-config.md))), so each case gets about half a CPU, and a single-threaded solution that needs more than about 15 s of CPU per case times out. Each timed-out case scores 0. The fixed version runs at most as many cases at once as the grader has CPUs, so each case keeps a whole CPU for its 30 s. The score scale, the cases, the tester and the per-case scoring are unchanged.

## What changes

### The problem in detail

The grader `/tmp/eval_apple_incremental_game.py` (sha256 `c33f5257…d70c`) runs every case with `subprocess.run(..., timeout=TIME_LIMIT)`, `TIME_LIMIT = 30` (line 9, wall-clock seconds), inside `ProcessPoolExecutor(max_workers=min(8, len(case_files)))` (line 45). A timed-out case scores 0 (line 37). The task JSON sets no CPU count; the publisher's leaderboard setting sets 4. Measured on the original grader with `--cpus 4` (`evidence/runs/apple_incremental_game-cpu4v8-a`, `-b`; ledger jobs `cpu4v8-games-a`, `-b`, both `status: exit=0`): a valid solution doing a fixed 12 or 14 s of CPU work per case passes 50/50, but 20 s per case gives 2 OK + 48 TLE (time limit exceeded) and the total falls from 99,714,418 to 3,955,266, which is 0 out of 100. The same solution at `--cpus 8` passes 50/50 with 99,714,418 (5.04 out of 100).

### Exact change

One file is changed, `/tmp/eval_apple_incremental_game.py` (`repair.patch`). A new function `cpu_quota_workers()`, copied verbatim from `repairs/grid_turing_robot-v2`, reads the grader's CPU quota from the cgroup (`/sys/fs/cgroup/cpu.max`, or `cpu.cfs_quota_us` / `cpu.cfs_period_us` on cgroup v1), rounds it down to whole CPUs, falls back to `os.cpu_count()` when there is no quota, and keeps the result between 1 and 8. The pool line becomes `ProcessPoolExecutor(max_workers=min(cpu_quota_workers(), len(case_files)))`. `docker run --cpus N` and the publisher's k8s backend both set this quota. The file keeps mode 0755 and grows from 2507 to 3414 bytes (sha256 `ba31e840…1931`). In the task JSON only `judge.image_tag` changes (`task.json.in`). Nothing changes in the work image, the prompt, the README, the tester, the cases, the parser or the score scale.

### Why this is the smallest change

The limit itself is kept at the promised 30 s, and it stays a wall-clock limit. Only the number of cases running at once changes, and only when the grader has fewer than 8 CPUs. With 8 or more CPUs the fixed grader runs 8 at once and behaves exactly as the original.

### Grading time stays inside `eval_timeout`

`eval_timeout` is 600 s and stays unchanged. With 4 CPUs the fixed grader runs 50 cases in ⌈50/4⌉ = 13 rounds of at most 30 s each, 390 s plus the tester (the tester's share of the measured 4-CPU runs is about 1 s for all 50 cases: `c4-base` took 1.0 s in total). The 390.8 s is a measurement, not a bound: it is the bad control, a solution that times out on every case, under the fixed version (`paired/results.md`). The original's worst case at 4 CPUs is 7 rounds, 210.7 s measured.

With fewer CPUs the round count grows: 3 CPUs give 17 rounds (510 s), but with 2 CPUs 25 rounds × 30 s = 750 s exceed the 600 s `eval_timeout`. On a grader with fewer than 3 CPUs the `eval_timeout`, not the 30 s per case, is the binding limit (about 24 s per case usable at 2 CPUs; the original gives about 7.5 s of CPU per case there). The grader prints its `CASE` and `TOTAL_SCORE` lines only after every case has finished, so when the `eval_timeout` is hit the harness gets no score lines and the whole submission scores 0. Below 3 CPUs the fixed version can therefore score lower than the original: for example, 10 cases that finish in 1 s and 40 that time out take about 605 s at 2 CPUs under the fixed version (no result at all) and about 210 s under the original, which scores the 10 good cases. This was derived from the code and the round count, not run.

### Are scores comparable?

At 8 or more grader CPUs the fixed version is the original: same parallelism, same outputs, same totals. At 4 CPUs:

- A deterministic solution that finished every case in time under the original gets exactly the same output and score.
- A solution needing between about 15 and 30 s of CPU per case lost those cases under the original; the fixed version scores them.
- A solution that searches until a wall-clock deadline gets about twice the CPU per case under the fixed version (measured: mean 13.00 s against 24.99 s for a 25 s deadline), so its score can improve. Its scores are not comparable with scores from the original grader at 4 CPUs.

Per-case CPU never decreases: with 4 CPUs, the original shares them among 8 running cases and the fixed version among 4.

## How it was checked

Side-by-side run of the original and fixed graders on the same solutions at `--cpus 4`, plus one pair at `--cpus 8`: [paired/results.md](paired/results.md). In plain words: at 4 CPUs, valid solutions using 20 or 28 s of CPU per case time out on 48 of 50 cases under the original grader (total 3,955,266, 0 out of 100) and pass 50/50 (total 99,714,418, 5.04 out of 100) under the fixed version. The honest control alone, a solution that stops at a 25 s wall-clock deadline and the pair at 8 CPUs give the same totals under both. A solution that needs 40 s per case times out on every case under both.

## Build and use

Git does not contain any file copied from the EdgeBench images. It holds only our diff (`repair.patch`) and the recipe for rebuilding the full file. Regenerate it, then build:

```bash
./materialize.sh && docker build -t ebv/apple_incremental_game-judge:v2 .
```

`materialize.sh` pulls the pinned judge image by digest, extracts the original file with `docker create` and `docker cp` (no container runs), checks it against `source-lock.json`, applies `repair.patch` with `patch -p1` and verifies the sha256 of the result against `source-lock.json` → `materialize.outputs`. It was run on a clean copy of this package and reproduced the reference file byte for byte (sha256 `ba31e840…1931`, mode 0755). The clean-machine rebuild check (`evidence/runs/materialize-check-g1`, `status: exit=0`) ran this script unchanged on a fresh E2B worker, rebuilt the image and found the installed file's sha256 equal to the lock.

## Limits

- The fixed grader reads its CPU quota from the cgroup (`cpu.max`). This was tested with `docker run --cpus` only, not inside a Kubernetes pod, which is the backend EdgeBench's leaderboard settings use.
- This fixes only the CPU contention. The case page's other notes (the 1 GB memory limit is not enforced per solution; the upper score anchors were not checked) still apply.
- The test solutions model a single-threaded solver with a fixed amount of CPU work, or one that stops at a 25 s wall-clock deadline. Multi-threaded solvers were not tested.
- Solutions that stop at a wall-clock deadline get more CPU under the fixed version, so their scores at 4 CPUs are not comparable between the original and the fixed version. How much a real deadline-based solver gains was not measured.
- The CPU quota is rounded down: a grader with 2.5 CPUs runs 2 cases at once.
- With fewer than 3 grader CPUs the 600 s `eval_timeout`, not the 30 s per case, becomes the binding limit (above). A submission that reaches it loses its whole output, so there the fixed version can score lower than the original.
- Without a cgroup quota the fixed grader falls back to `os.cpu_count()`, which counts all of the host's CPUs, not the ones the grader may use (`os.sched_getaffinity`). Under a CPU-set limit with no quota (for example `docker run --cpuset-cpus`) it can still run more cases at once than it has CPUs. Using the affinity count would need a new paired run, so it is not changed here.
- No AI model was rerun. The effect on published scores needs regrading of the original submissions or new runs.
