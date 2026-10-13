# Vibrating Path Graph Coloring, fixed version: each case keeps a whole CPU for its 30 s limit

## What this fixes

The README promises "Time limit | 30 seconds / test case" (README line 54). The original grader runs 8 cases at once under a 30 s wall-clock limit per case, whatever the number of CPUs it is given. The publisher's leaderboard setting gives the grader 4 CPUs (`judge_cpu_limit: 4`, EdgeBench `examples/all-tasks-k8s/experiment.yaml` (quoted in [`evidence/impact/edgebench-leaderboard-config.md`](../../evidence/impact/edgebench-leaderboard-config.md))), so each case gets about half a CPU, and a single-threaded solution that needs more than about 14 s of CPU per case times out. One timed-out case makes the total infinite, so the whole submission gets no score. The fixed version runs at most as many cases at once as the grader has CPUs, so each case keeps a whole CPU for its 30 s, and it raises the whole-run `eval_timeout` from 600 to 900 s so that the slower grading still fits. The score scale, the cases, the tester and the rule that one failed case voids the submission are unchanged.

## What changes

### The problem in detail

See the [case page](../../cases/vibrating_path_graph_coloring.md). The grader `/tmp/eval_vibrating_path.py` (sha256 `934a2b9d…9350`) runs every case with `subprocess.run(..., timeout=TIME_LIMIT)`, `TIME_LIMIT = 30` (line 9, wall-clock seconds), inside `ProcessPoolExecutor(max_workers=min(8, len(case_files)))` (line 45); a timed-out case scores `float('inf')` (line 37) and is added to the total. The task JSON sets no CPU count; the publisher's leaderboard setting sets 4. Measured on the original grader with `--cpus 4` (`evidence/runs/vibrating_path_graph_coloring-cpu4v8-a`, `-b`, both `status: exit=0`): a valid solution doing a fixed 12 or 14 s of CPU work per case passes 50/50 (at 14 s the slowest case took 29.9 s), but 20 s per case gives 2 OK + 48 TLE (time limit exceeded) and `TOTAL_SCORE inf`, which has no score out of 100 (`sforge/harness/score_rescale.py`). The same solution at `--cpus 8` passes 50/50 with TOTAL 24,650,014 (2.06 out of 100). The window starts below 15 s because the task's Python tester for earlier cases (up to 19 s of CPU per case, `paired/tester_time.out`) shares the same 4 CPUs.

### Exact change

1. `/tmp/eval_vibrating_path.py` (`repair.patch`). A new function `cpu_quota_workers()`, copied verbatim from `repairs/grid_turing_robot-v2`, reads the grader's CPU quota from the cgroup (`/sys/fs/cgroup/cpu.max`, or `cpu.cfs_quota_us` / `cpu.cfs_period_us` on cgroup v1), rounds it down to whole CPUs, falls back to `os.cpu_count()` when there is no quota, and keeps the result between 1 and 8. The pool line becomes `ProcessPoolExecutor(max_workers=min(cpu_quota_workers(), len(case_files)))`. `docker run --cpus N` and the publisher's k8s backend both set this quota. The file keeps mode 0755 and grows from 2523 to 3430 bytes (sha256 `3b72b9ed…bd23`).
2. `task.json.in`: `judge.image_tag` → `eb22343ce84e-ebv-v2`, and `judge.eval_timeout` 600 → 900 (below).

Nothing changes in the work image, the prompt, the README, the tester, the cases, the parser or the score scale.

### Why this is the smallest change

The per-case limit is kept at the promised 30 s, and it stays a wall-clock limit. Only the number of cases running at once changes, and only when the grader has fewer than 8 CPUs. With 8 or more CPUs the fixed grader runs 8 at once and grades exactly as the original.

### Why `eval_timeout` is raised to 900 s

Unlike grid_turing_robot, this task's tester is slow. On the honest control's outputs the pinned `tools/bin/tester` took 5.6–19.0 s per case at 1 CPU, 579.6 s in total over the 50 cases (`paired/tester_time.out`, measured in the original image). With the cap at 4 CPUs each worker runs a case's solution and then its tester. The worst case for valid solutions is therefore about (50 × 30 s + 579.6 s) / 4 = 520 s of work per CPU, plus a tail of at most 3/4 × 49 s (the longest single case, 30 s + 19 s) when the last rounds are unbalanced: 557 s. That is under 600 s, but only by 7%, and tester time depends on the solution's output. The fixed version therefore sets 900 s. The measured runs agree with the arithmetic: under the fixed version at 4 CPUs a 28 s-per-case solution took 508.6 s to grade and a 25 s wall-deadline solution up to 558.0 s (`paired/results.md`). Under the original at 4 CPUs grading is shorter (at most 7 rounds of 30 s plus testers) because most slow solutions are killed.

At 3 CPUs the same bound is 2,080 / 3 + 2/3 × 49 = 726 s, inside 900 s. At 2 CPUs it is 1,040 + 25 = 1,065 s, over 900 s, so with fewer than 3 grader CPUs `eval_timeout` can bind for solutions near the 30 s limit.

### Are scores comparable?

At 8 or more grader CPUs the fixed version grades as the original: same parallelism, same outputs, same totals. At 4 CPUs:

- A deterministic solution that finished every case in time under the original gets exactly the same output and score.
- A solution needing between about 14 and 30 s of CPU per case got `inf` (no score) under the original; the fixed version scores it.
- A solution that searches until a wall-clock deadline gets about twice the CPU per case under the fixed version, so its score can improve. Its scores are not comparable with scores from the original grader at 4 CPUs.

Per-case CPU never decreases: with 4 CPUs, the original shares them among 8 running cases (and their testers) and the fixed version among 4.

## How it was checked

Side-by-side runs of the original and fixed graders on the same solutions at `--cpus 4`, plus one pair at `--cpus 8`: [paired/results.md](paired/results.md). In plain words: at 4 CPUs, valid solutions using 20 or 28 s of CPU per case time out on 48 of 50 cases under the original grader (total `inf`, no score) and pass 50/50 with the usual total of 24,650,014 under the fixed version. The honest control alone, a solution that stops at a 25 s wall-clock deadline and the pair at 8 CPUs give the same totals under both. A solution that needs 40 s per case times out on every case under both. In one of nine original-grader gradings of the 25 s deadline solution, 14 cases timed out and the submission got no score; all 14 are among the cases with the slowest tester, so the grader's own 60 s tester timeout at half a CPU is the likely cause (inferred, not observed; details in `paired/results.md`). Under the fixed version each tester gets a whole CPU.

## Build and use

Git does not contain any file copied from the EdgeBench images. It holds only our diff (`repair.patch`) and the recipe for rebuilding the full file. Regenerate it, then build:

```bash
./materialize.sh && docker build -t ebv/vibrating_path_graph_coloring-judge:v2 .
```

`materialize.sh` pulls the pinned judge image by digest, extracts the original file with `docker create` and `docker cp` (no container runs), checks it against `source-lock.json`, applies `repair.patch` with `patch -p1` and verifies the sha256 of the result against `source-lock.json` → `materialize.outputs`. It was run on a clean copy of this package and reproduced the reference file byte for byte (sha256 `3b72b9ed…bd23`, mode 0755).

## Limits

- The fixed grader reads its CPU quota from the cgroup (`cpu.max`). This was tested with `docker run --cpus` only, not inside a Kubernetes pod, which is the backend EdgeBench's leaderboard settings use.
- This fixes only the CPU contention. The case page's other notes still apply: the tester accepts a zero-hit answer only in two lines, and one failed case voids the whole submission.
- The test solutions model a single-threaded solver with a fixed amount of CPU work, or one that stops at a 25 s wall-clock deadline. Multi-threaded solvers were not tested.
- Solutions that stop at a wall-clock deadline get more CPU under the fixed version, so their scores at 4 CPUs are not comparable between the original and the fixed version. How much a real deadline-based solver gains was not measured.
- The tester times are for the honest control's outputs; other outputs may take longer to check. The 900 s `eval_timeout` is set from that measurement with margin, not from a worst case over all outputs.
- The CPU quota is rounded down: a grader with 2.5 CPUs runs 2 cases at once. Below 3 grader CPUs `eval_timeout` can bind (above).
- No AI model was rerun. The effect on published scores needs regrading of the original submissions or new runs.
