# Why the fixed grader rejects Qwen3.5-122B's triangulation submissions

Under the original grader, 74 of the 85 archived Qwen3.5-122B submissions pass 10/10 cases (best 58.07/100). Under the
fixed grader, every one of those gets WA on all 10 cases. The fixed version changes two things: the flip rule
(`is_flippable` now requires the README's convex quadrilateral) and the hidden inputs (regenerated without overlaps
and with the full convex hull). `matrix.sh` separates the two. It runs the best submission (agent-40) and the first
one (agent-1) with each tester (original or fixed rule) on each input set (original or regenerated), one case at a
time, 30 s per case, `--network none --cpus 4 --memory 6g`. The run was on one E2B worker, 2026-10-20, using the
images in `result/images.txt`.

| Submission | Original rule, original inputs | Original rule, new inputs | Fixed rule, original inputs | Fixed rule, new inputs |
|---|---|---|---|---|
| agent-40 | 10/10 scored | 10/10 scored | 0/10 (Invalid flip) | 0/10 (Invalid flip) |
| agent-1  | 10/10 scored | 10/10 scored | 0/10 (Invalid flip) | 0/10 (Invalid flip) |

The rule causes the failures, and the inputs do not. On every case, on both input sets, the solver makes at least
one flip that the README forbids, and the original rule accepts it. Under the documented rules these submissions
score 0. `result/m_*.txt` keeps only the per-case verdict lines; the submissions themselves are not redistributed.
