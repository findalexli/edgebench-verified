# Second regrade of the third-party Opus 5.5 run: combined results

`summary.json` is `analyze.py` over every `opus55-regrade2-*/result/out/derived.json`: per submission the original
recorded score, the v1 and v2 regrade scores (all reps), validity and wall time; per task the run's selected score
under EdgeBench's own `select_best` with the task's selection policy, for the original record, the v1 regrade and the
v2 regrade (reps aggregated by mean, min and max). `grade_rg2.py` turns raw captures into `derived.json`;
`collect.sh` checks `status: exit=0`, grades, and moves raw captures to `.internal/`.
