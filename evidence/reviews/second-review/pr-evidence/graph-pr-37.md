## What and why

`problem.md` says prediction keys "can be strings or values convertible to strings", and `test_nodes` arrives as integers. The verifier looks up string IDs only, so a complete answer keyed by integers matches no node. Every quality metric is 0, yet the run is valid because the coverage check only counts keys.

Keys are converted only when none matches as given, the converted keys are exactly the test nodes, and every value converts with `int()`. Everything else takes the old path.

No naturally occurring affected submission is known: the starter and 105 distinct solutions from a public Opus 5.5 run all key by `str(nid)`. The reproducer changes only a real solver's output-key representation, so please decide whether that meets the good-faith-solver criterion.

This fixes complete integer-keyed answers only. Unchanged: mixed keys grade only the string-keyed part, and integer confidence keys with string prediction keys are ignored.

## Checklist for task changes

- [x] `version` in `task.toml` is bumped (any change that can move scores).
- [x] `NOTES.md`: the change and its score effect are under **Changes**; no Known issue covered this.
- [x] Old vs new judge on the same submissions, on the same host, results below.
- [x] New blobs: none.

## Old vs new judge

`tools/judge_local.py`, old judge built from 1187e2c, new judge from this branch, on two workers. Four grades per judge per row, reversing judge order, except the junk-keys row (two). Scores are ranges out of 100 and move only through the solve-time term; `overall` excludes it. The old score for integer keys is about 2, not 0, because this solver is fast enough for a time bonus (Known issue 3).

| Submission | Old | New |
|------------|-----|-----|
| Opus 5.5 solution, string keys | 90.54–90.63, overall 0.885740 | 90.53–90.60, overall 0.885740 |
| Same predictions, integer keys | 1.95–2.01, overall 0 | 90.52–90.57, overall 0.885740 |
| Same, integer prediction keys, string confidence keys | 1.98–2.04, overall 0 | 90.52–90.57, overall 0.885740 |
| Wrong classes, string keys | 8.38–8.45, overall 0.064187 | 8.38–8.41, overall 0.064187 |
| Wrong classes, integer keys | 1.94–2.01, overall 0 | 8.33–8.41, overall 0.064187 |
| Half string, half integer keys | 90.31–90.43, overall 0.884238 | 90.38–90.43, overall 0.884238 |
| String prediction keys, integer confidence keys | 89.37–89.45, overall 0.874201 | 89.36–89.44, overall 0.874201 |
| Integer keys, half of them not test nodes | 1.95–2.02, overall 0 | 1.95–1.97, overall 0 |
| Integer keys, half the nodes | invalid | invalid |
| `predictions` is a list | invalid | invalid |
| `solve` raises | invalid, 0 | invalid, 0 |
| Integer keys, all values `"x"` | 1.97–2.04, overall 0 | 1.95–2.00, overall 0 |

Also graded once per judge: the starter and 103 distinct real Opus 5.5 submissions, all string-keyed. Verdicts did not change. Quality metrics were identical for 102 of the 104. The other two (0.7193 vs 0.7155, 0.8759 vs 0.8738) are multi-threaded solvers. Their keys are strings, so the new code never runs for them. Two runs of the original verifier also differed, by less (0.0005, 0.0002). Three slow submissions were not regraded.


