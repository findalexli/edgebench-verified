### Task

vibrating_path_graph_coloring

### Claim

The judge runs 8 cases at once on the official 4 CPUs, so a single-threaded case gets about 15 s of CPU (computed) inside its 30 s wall-clock limit. One timeout makes the whole total `inf`, so valid solvers lose their score, some on every grade and some only on some grades.

### Impact

Measured on 8 vCPU hosts with the judge limited to 4 CPUs. Scores are 0..100.

| Submission | n | Current judge | 4 cases at once (#36) |
|------------|---|---------------|-----------------------|
| Opus 5.5 solver | 15 | `inf` every time, 7-39 of 50 OK | 19.77-19.98, 50 of 50 OK |
| Gemini 4 Argon solver 1 | 3 | 32.49 twice, `inf` once | 32.49, 50 of 50 OK |
| Gemini 4 Argon solver 2 | 3 | `inf` every time, 43-49 of 50 OK | 18.64, 50 of 50 OK |
| Valid answer plus 20 s of CPU per case | 3 | `inf`, 2 of 50 OK | 2.06, 50 of 50 OK |

The Opus file also passed all 7 grades during its own run on the published v1 judge image, so the current grading scores it non-repeatably.

### Evidence and how to reproduce

Wrap a valid `solution.py` so it spins for 20 s of CPU before printing its answer, then grade it:

    python3 tools/judge_local.py --task-dir edgebench/tasks/vibrating_path_graph_coloring --image <judge tag> --archive <submission.tar.gz> --out result.json

### Proposed fix

#36 sets the pool to `min(8, SFORGE_CPUS, cases)`, as SCHEMA asks, and raises `timeout_sec` from 600 to 1200. Solvers that read the clock may get different scores, and old scores have no mapping, so maintainers need to decide whether this needs an exception and a regrade.

### Limits

We hold no v1 leaderboard submissions, so we can't show how far their scores would move. Known issue 3, general host load, remains: the limit is still wall clock.

We found this during [EdgeBench Verified](https://lishengzhi.com/edgebench-verified/tasks/vibrating_path_graph_coloring.html), our audit of EdgeBench's tasks.
