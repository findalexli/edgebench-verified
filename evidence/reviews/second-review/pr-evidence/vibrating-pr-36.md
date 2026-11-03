Task finding: #40.

## What and why

The README limits each case to 30 s of wall clock. The judge runs 8 cases at once on the official 4 CPUs, so a single-threaded case gets about 15 s of CPU, and one timeout makes the total `inf` (unrankable). SCHEMA says a parallel grader "sizes the pool with `SFORGE_CPUS`, not `nproc`".

This PR sets the pool to `min(8, SFORGE_CPUS, cases)`, defaulting to 4. Grading now takes longer, so `timeout_sec` goes from 600 to 1200: a valid solver using 28 s of CPU per case took 525-624 s, and local runs at `timeout_sec` 600 reached 622.5 s, passing only through `judge_local.py`'s 30 s grace. Nominal solver and tester budgets at 4 workers total 13 rounds x 90 s = 1170 s, excluding overhead.

## Decision for maintainers

CONTRIBUTING asks a fix to keep the scores of correct work or say how old scores map. This fix may move the scores of solvers that read the clock, and we have no mapping. Please decide whether it needs an exception and a regrade before comparing with v1 leaderboard entries.

- Gemini solver 1 does not read the clock. It got raw 3019260 on all five valid grades across both judges. One solver can't establish this for others.
- The Opus solver does read the clock. On the old judge, this file passed all 7 grades during its own run but only 3 of 9 later grades on the published v1 image (another worker, 3 GB memory). Its valid raw scores were 3303703-3348662 there and 3295581-3374197 on the new judge here.
- The deadline variants below timed out less often, but too few old grades were valid to establish stability. NOTES shows a time-budgeted submission moving 10.82-14.26 with load.

## Old vs new judge

| Submission | n | Old | New |
|------------|---|-----|-----|
| Opus 5.5 solver | 15 | `inf` every time, 7-39 of 50 OK | 19.77-19.98, 50 of 50 OK |
| Gemini 4 Argon solver 1 | 3 | 32.49 twice, `inf` once (49 of 50 OK) | 32.49, 50 of 50 OK |
| Gemini 4 Argon solver 2 | 3 | `inf` every time, 43-49 of 50 OK | 18.64, 50 of 50 OK |
| Gemini 4 Argon solver 3 | 3 | `inf` every time, 20-24 of 50 OK | `inf` every time, 24 of 50 OK (26 wrong answers) |
| 12 s CPU per case | 3 | 2.06 once, `inf` twice, 27-50 of 50 OK | 2.06, 50 of 50 OK |
| 20 s CPU per case | 3 | `inf`, 2 of 50 OK | 2.06, 50 of 50 OK |
| 28 s CPU per case | 3 | `inf`, 2 of 50 OK | 2.06, 50 of 50 OK |
| 40 s CPU per case (over the limit) | 3 | `inf`, 0 of 50 OK | `inf`, 0 of 50 OK |
| Opus variant, 5 s deadline search | 3 | 10.96-10.99, `inf` once | 10.90-11.15 |
| Opus variant, 15 s deadline search | 3 | 10.88, `inf` twice | 10.43-11.10 |

Scores are 0..100 and n is per judge. "12 s CPU" and similar rows are a valid answer plus a fixed CPU spin. The variants set `TL` to 5 or 15 and `LSIT` to 0.

We graded with `tools/judge_local.py`: the old judge from 1187e2c, the new judge from this branch (later edits changed comments, NOTES and `timeout_sec`). Each row used three workers, six for the Opus solver, and judge order varied except on the 28 s row (old first).

`sforge eval`, which sets `SFORGE_CPUS=4`, gave the same 2.06 on the 28 s row at `timeout_sec` 600 and 1200, in 525-584 s, n=2 each. On the final code, one more worker took the Opus solver from `inf` (24 of 50 OK) to 19.96 (50 of 50 OK) and `sforge eval` on the 28 s row gave 2.06 in 597 s.

## Checklist for task changes

- [x] `version` in `task.toml` is bumped (any change that can move scores).
- [x] `NOTES.md`: the change and its score effect are under **Changes**. No Known issues entry is fully fixed; issue 3 remains.
- [x] Old vs new judge on the same submissions, on the same host, results above.
- [x] New blobs: none.

We first found this in [EdgeBench Verified](https://lishengzhi.com/edgebench-verified/tasks/vibrating_path_graph_coloring.html), our audit of EdgeBench's tasks. Its repair of v1 used the same pool change with a 900 s limit, measured separately.

