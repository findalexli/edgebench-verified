# Grid Turing Robot, fixed version: each case keeps a whole CPU for its 30 s limit

## What this fixes

The README promises "Time limit | 30 seconds / test case". The original grader runs 8 cases at once under a 30 s wall-clock limit per case, whatever the number of CPUs it is given. The publisher's leaderboard setting gives the grader 4 CPUs (`judge_cpu_limit: 4`, quoted in [`evidence/impact/edgebench-leaderboard-config.md`](../../evidence/impact/edgebench-leaderboard-config.md)), so each case gets about half a CPU, and a single-threaded solution that needs more than about 15 s of CPU per case times out. One timed-out case voids the whole submission. The fixed version runs at most as many cases at once as the grader has CPUs, so each case keeps a whole CPU for its 30 s. The score scale, the cases, the tester and the rule that one failed case voids the submission are unchanged.

## What changes

### The problem in detail

See the [case page](../../cases/grid_turing_robot.md), part (c). The grader `/tmp/eval_grid_turing_robot.py` runs every case with `subprocess.run(..., timeout=TIME_LIMIT)`, `TIME_LIMIT = 30` (wall-clock seconds), inside `ProcessPoolExecutor(max_workers=min(8, len(case_files)))`. The task JSON sets no CPU count; the publisher's leaderboard setting sets 4. Measured on the original grader with `--cpus 4` (`evidence/runs/grid_turing_robot-cpu4v8-a`, `status: exit=0`): a valid solution doing a fixed 12 or 14 s of CPU work per case passes 50/50, but 16, 20, 24 or 28 s per case gives 2 OK + 48 TLE (time limit exceeded) and an invalid submission. The same solutions at `--cpus 8` all pass 50/50 with TOTAL 94,092 (`evidence/runs/grid_turing_robot-cpu4v8-b`).

### Exact change

One file is changed, `/tmp/eval_grid_turing_robot.py` (`repair.patch`). A new function `cpu_quota_workers()` reads the grader's CPU quota from the cgroup (`/sys/fs/cgroup/cpu.max`, or `cpu.cfs_quota_us` / `cpu.cfs_period_us` on cgroup v1), rounds it down to whole CPUs, falls back to `os.cpu_count()` when there is no quota, and keeps the result between 1 and 8. The pool line becomes `ProcessPoolExecutor(max_workers=min(cpu_quota_workers(), len(case_files)))`. `docker run --cpus N` and the publisher's k8s backend both set this quota (the harness passes `nano_cpus`, `sforge/harness/config.py:327`). The file keeps mode 0755 and grows from 2532 to 3439 bytes. In the task JSON only `judge.image_tag` changes (`task.json.in`). Nothing changes in the work image, the prompt, the README, the tester, the cases, the parser or the score scale.

### Why this is the smallest change

The limit itself is kept at the promised 30 s, and it stays a wall-clock limit. Only the number of cases running at once changes, and only when the grader has fewer than 8 CPUs. With 8 or more CPUs the fixed grader still runs 8 at once and behaves exactly as the original.

### Grading time stays inside `eval_timeout`

`eval_timeout` is 600 s and stays unchanged. With 4 CPUs the fixed grader runs 50 cases in ⌈50/4⌉ = 13 rounds. The solution part of a case is capped at 30 s by the time limit, and the tester took at most 0.042 s per case on the known-good output (local measurement at `--cpus 1`, `paired/tester_time.out`). The worst case is therefore 13 × 30 s = 390 s plus testers and start-up, well under 600 s; a solution that times out on every case took 390.9 s (`paired/results.md`) in the paired run. The original grader's worst case at 4 CPUs is 7 × 30 s = 210 s. The tester's own 60 s timeout is never approached by valid outputs; if it were reached on every case, neither version would fit in 600 s (original 7 × 90 s = 630 s).

With fewer CPUs the round count grows: 3 CPUs give 17 rounds (510 s worst case), but with 2 CPUs 25 rounds × 30 s = 750 s exceed the 600 s `eval_timeout`, so on a 2-CPU grader the fixed version can honour about 24 s per case, not 30 (the original gives about 7.5 s of CPU per case there).

### Are scores comparable?

At 8 or more grader CPUs the fixed version is the original: same parallelism, same outputs, same totals. At 4 CPUs:

- A deterministic solution that finished every case in time under the original gets exactly the same output and score.
- A solution needing between about 15 and 30 s of CPU per case timed out (and voided the submission) under the original; the fixed version scores it.
- A solution that searches until a wall-clock deadline gets about twice the CPU per case under the fixed version, so its score can improve. Its score is not comparable with one from the original grader at 4 CPUs.

Per-case CPU never decreases: with 4 CPUs, the original shares them among 8 running cases and the fixed version among 4.

## How it was checked

Side-by-side run of the original and fixed graders on the same solutions at `--cpus 4`, plus one pair at `--cpus 8`: [paired/results.md](paired/results.md). In plain words: at 4 CPUs, valid solutions using 16 or 28 s of CPU per case time out on 48 of 50 cases under the original grader, which voids the submission, and pass 50/50 with the usual TOTAL of 94,092 under the fixed version. Faster solutions, a solution that stops at a 25 s wall-clock deadline and a pair run at 8 CPUs give the same results under both. A solution that needs 40 s per case times out on every case under both.

## Build and use

Git does not contain any file copied from the EdgeBench images. It holds only our diff (`repair.patch`) and the recipe for rebuilding the full file. Regenerate it, then build:

```bash
./materialize.sh && docker build -t ebv/grid_turing_robot-judge:v2 .
```

`materialize.sh` pulls the pinned judge image by digest, extracts the original file with `docker create` and `docker cp` (no container runs), checks it against `source-lock.json`, applies `repair.patch` with `patch -p1` and verifies the sha256 of the result against `source-lock.json` → `materialize.outputs`. It was run on a clean copy of this package and reproduced the reference file byte for byte (sha256 `285229ee…3a22`, mode 0755).

## Limits

- The fixed grader reads its CPU quota from the cgroup (`cpu.max`). This was tested with `docker run --cpus` only, not inside a Kubernetes pod, which is the backend EdgeBench's leaderboard settings use.
- This fixes only the CPU contention. The other notes on the [case page](../../cases/grid_turing_robot.md) still apply and are not changed here: one failed case voids the whole submission (unstated), and the configured baseline 9,025,986 is above the shipped baseline's 7,744,909 (2.84 points).
- The test solutions model a single-threaded solver with a fixed amount of CPU work, or one that stops at a 25 s wall-clock deadline. Multi-threaded solvers were not tested.
- The CPU quota is rounded down: a grader with 2.5 CPUs runs 2 cases at once.
- With fewer than 3 grader CPUs the 600 s `eval_timeout`, not the 30 s per case, becomes the binding limit (above).
- No AI model was rerun. The effect on published scores needs regrading of the original submissions or new runs.
