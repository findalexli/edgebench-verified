# Molecular Self Assembly, fixed version: each case keeps a whole CPU for its 30 s limit

## What this fixes

The README promises "Time limit | 30 seconds / test case". The original grader runs up to 8 cases at once under a 30 s wall-clock limit per case, whatever the number of CPUs it is given. The publisher's leaderboard setting gives the grader 4 CPUs (`judge_cpu_limit: 4`, quoted in [`evidence/impact/edgebench-leaderboard-config.md`](../../evidence/impact/edgebench-leaderboard-config.md)), so each case gets about half a CPU: a single-threaded solution that needs more than about 15 s of CPU per case times out, and a timed-out case scores 0. The fixed version runs at most as many cases at once as the grader has CPUs, so each case keeps a whole CPU for its 30 s. The score scale, the cases and the tester are unchanged.

## What changes

### The problem in detail

The grader `/tmp/eval_molecules.py` runs every case with `subprocess.run(..., timeout=TIME_LIMIT)`, `TIME_LIMIT = 30` (wall-clock seconds), with `max_workers = min(int(os.environ.get("SEBENCH_MOLECULES_WORKERS", "8")), len(case_files))`. Nothing sets that variable, so 8 cases run at once. Measured on the original grader at `--cpus 4` (`evidence/runs/molecular_self_assembly-cpu4v8`, `status: exit=0`): the shipped baseline preceded by a fixed 12 s of CPU work per case passes 50/50 with TOTAL 69,280,072, but with 16, 20 or 28 s per case only 2 cases pass, 48 time out, and TOTAL falls to 2,849,909, which is below the baseline reference point and scores 0. The same solutions at `--cpus 8` all pass 50/50 with TOTAL 69,280,072.

### Exact change

One file is changed, `/tmp/eval_molecules.py` (`repair.patch`). A new function `cpu_quota_workers()` reads the grader's CPU quota from the cgroup (`/sys/fs/cgroup/cpu.max`, or `cpu.cfs_quota_us` / `cpu.cfs_period_us` on cgroup v1), rounds it down to whole CPUs, falls back to `os.cpu_count()` when there is no quota, and keeps the result between 1 and 8. The worker line becomes `max_workers = min(int(os.environ.get("SEBENCH_MOLECULES_WORKERS", "8")), cpu_quota_workers(), len(case_files))`, so the environment variable can still lower the count but can no longer exceed the CPU quota. `docker run --cpus N` and the publisher's k8s backend both set this quota (the harness passes `nano_cpus`, `sforge/harness/config.py:327`). The file keeps mode 0755 and grows from 3037 to 3947 bytes. In the task JSON only `judge.image_tag` changes (`task.json.in`). Nothing changes in the work image, the prompt, the README, the tester, the cases, the parser or the score scale.

### Why this is the smallest change

The limit itself is kept at the promised 30 s, and it stays a wall-clock limit. Only the number of cases running at once changes, and only when the grader has fewer than 8 CPUs. With 8 or more CPUs the fixed grader still runs 8 at once and behaves exactly as the original.

### Grading time stays inside `eval_timeout`

`eval_timeout` is 600 s and stays unchanged. With 4 CPUs the fixed grader runs 50 cases in ⌈50/4⌉ = 13 rounds. The solution part of a case is capped at 30 s by the time limit, and the tester took at most 0.067 s per case on the shipped baseline's output (local measurement at `--cpus 1`, `paired/tester_time.out`). The worst case is therefore 13 × 30 s = 390 s plus testers and start-up, well under 600 s; a solution that times out on every case took 390.9 s (`paired/results.md`) in the paired run. The original grader's worst case at 4 CPUs is 7 × 30 s = 210 s. The tester's own 60 s timeout is never approached by valid outputs; if it were reached on every case, neither version would fit in 600 s (original 7 × 90 s = 630 s).

With fewer CPUs the round count grows: 3 CPUs give 17 rounds (510 s worst case), but with 2 CPUs 25 rounds × 30 s = 750 s exceed the 600 s `eval_timeout`, so on a 2-CPU grader the fixed version can honour about 24 s per case, not 30 (the original gives about 7.5 s of CPU per case there).

### Are scores comparable?

At 8 or more grader CPUs the fixed version is the original: same parallelism, same outputs, same totals. At 4 CPUs:

- A deterministic solution that finished every case in time under the original gets exactly the same output and score.
- A solution needing between about 15 and 30 s of CPU per case lost those cases (score 0 each) under the original; the fixed version scores them.
- A solution that searches until a wall-clock deadline gets about twice the CPU per case under the fixed version, so its score can improve. Its score is not comparable with one from the original grader at 4 CPUs. A third-party Claude Opus 5.5 run on this task graded at 4 CPUs in 178.7 s, consistent with such a deadline of about 25 s (see the case page).

Per-case CPU never decreases: with 4 CPUs, the original shares them among 8 running cases and the fixed version among 4.

## How it was checked

Side-by-side run of the original and fixed graders on the same solutions at `--cpus 4`, plus one pair at `--cpus 8`: [paired/results.md](paired/results.md). In plain words: at 4 CPUs, solutions using 16 or 28 s of CPU per case lose 48 of 50 cases to timeouts under the original grader (TOTAL 2,849,909 instead of 69,280,072, score 0) and pass 50/50 under the fixed version. Faster solutions, a solution that stops at a 25 s wall-clock deadline and a pair run at 8 CPUs give the same results under both. A solution that needs 40 s per case times out on every case under both.

## Build and use

Git does not contain any file copied from the EdgeBench images. It holds only our diff (`repair.patch`) and the recipe for rebuilding the full file. Regenerate it, then build:

```bash
./materialize.sh && docker build -t ebv/molecular_self_assembly-judge:v2 .
```

`materialize.sh` pulls the pinned judge image by digest, extracts the original file with `docker create` and `docker cp` (no container runs), checks it against `source-lock.json`, applies `repair.patch` with `patch -p1` and verifies the sha256 of the result against `source-lock.json` → `materialize.outputs`. It was run on a clean copy of this package and reproduced the reference file byte for byte (sha256 `1cf8f71d…9ef0`, mode 0755).

## Limits

- The fixed grader reads its CPU quota from the cgroup (`cpu.max`). This was tested with `docker run --cpus` only, not inside a Kubernetes pod, which is the backend EdgeBench's leaderboard settings use.
- This fixes only the CPU contention. The other note on the [case page](../../cases/molecular_self_assembly.md) still applies and is not changed here: the README's 1 GB memory limit per solution is not enforced; only the grader container's memory limit applies.
- The test solutions model a single-threaded solver with a fixed amount of CPU work, or one that stops at a 25 s wall-clock deadline. Multi-threaded solvers were not tested.
- The CPU quota is rounded down: a grader with 2.5 CPUs runs 2 cases at once.
- With fewer than 3 grader CPUs the 600 s `eval_timeout`, not the 30 s per case, becomes the binding limit (above).
- No AI model was rerun. The effect on published scores needs regrading of the original submissions or new runs.
