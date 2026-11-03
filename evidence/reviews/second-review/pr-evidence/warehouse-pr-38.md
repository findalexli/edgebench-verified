## What and why

The instruction says "T=5 test cases per input" (line 24) and "30 seconds per test case" (line 55), and the README agrees, but `TIME_LIMIT = 60` kills an input at 60 s. One timeout invalidates the whole submission, so a solver using the stated budget gets no score. `NOTES.md` lists this as a known issue. `TIME_LIMIT` is now 150 s; the pool stays at 8.

The README also calls the 50 inputs "test cases" (line 65), which could be read as 30 s per input. A wall-clock deadline below 150 s now passes on either reading; 30 s of CPU per test case does not. No real submission is shown affected: an Opus 5.5 run chose 20 s per input and noted the limit is ambiguous. The deadline rows below are edited versions of it, and they score slightly worse than the 20 s original.

**This is a partial fix.** Eight inputs share 4 CPUs, so a solver doing fixed work above a computed 75 s of CPU per input still times out (last row). A pool change would fix that but moves the scores of deadline searches, so it is left out and noted under Known issues.

Nominal grading time is at most 7 rounds x (150 s + 30 s tester) = 1260 s, excluding overhead, inside `timeout_sec` (3600). That can outlast the 900 s final wait in `sforge run` (`run_agent.py:860`), so we ran the real harness on both judges, with a scripted stand-in for the model and auto-eval off. Each agent ended right after a background submit, the worst case for that wait:

| Submissions, the last still grading when the agent ended | n | Old best | New best |
|------------------------------------------------------------|---|----------|----------|
| 125 s deadline | 2 | none | 19.49 |
| 140 s deadline | 2 | none | none (still grading at the 900 s wait) |
| 20 s deadline, then 140 s deadline | 1 old, 2 new | 19.51 | 19.51 |

The old judge gives the 140 s submission no score either, so losing that grade changes nothing, and an earlier valid score survives. After the timed-out wait, `sforge run` exited 0 and left the judge container running. Auto-eval grades can overlap more (up to 5 judges, was 3); not measured.

## Checklist for task changes

- [x] `version` in `task.toml` is bumped (any change that can move scores).
- [x] `NOTES.md`: the change and its score effect are under **Changes**, and the fixed entry is removed from **Known issues**.
- [x] Old vs new judge on the same submissions, on the same host, results below.
- [x] New blobs: none.

## Old vs new judge

Both judges built from source on 8-vCPU workers, judge at 4 CPUs, with `judge_local.py` and `sforge eval`. Raw score with 0..100 in brackets; n per judge. `invalid` means `inf`. The deadline rows are the Opus solver with its default deadline and hill-climbing share changed. Both new 140 s runs and the new 100 s CPU run overlapped another 4-CPU judge.

| Submission | n | Old | New |
|------------|---|-----|-----|
| Generic valid control | 3 | 46676.8 (0.00) | same |
| Opus 5.5 final submission, unchanged, 20 s deadline | 2 old, 3 new | 873.5-873.7 (19.51) | 873.7 (19.51) |
| Opus 5.5 best in-run submission, unchanged, 23 s deadline | 2 | 873.6-873.8 (19.51) | 873.5-873.6 (19.51) |
| 45 s deadline, valid on both | 2 | 878.8-878.9 (19.48) | 878.8 (19.48) |
| One bug; shipped starter | 2 each | invalid | invalid |
| **125 s deadline** | 2 | invalid, 0 of 50 OK | 877.3-877.9 (19.48-19.49), 50 of 50 OK |
| **140 s deadline** | 2 | invalid, 0 of 50 OK | 877.3 (19.49), 50 of 50 OK, 958 s |
| Sleeps 170 s (over the limit) | 2 | invalid, 0 of 50 OK | invalid, 0 of 50 OK |
| Fixed 100 s of CPU per input | 2 old, 1 new | invalid, 0 of 50 OK | invalid, 2 of 50 OK |

Valid scores moved by at most 0.15 raw (0.001 points) between judge means, inside the spread of repeats on one judge. The tested patch differs from this branch only in `NOTES.md`.


