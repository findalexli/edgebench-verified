# apple_incremental_game v2: the evaluator runs at most as many cases at once as the grader has CPUs
# (cgroup CPU quota, 1..8) instead of always 8, so each case keeps a whole CPU for its 30 s limit.
# Only the one changed file is copied; nothing is installed.
FROM seededge/edgebench.judge.apple_incremental_game@sha256:d3af7b43331078bb3ef29fab70c502cbb72d0e08d52e59cf9bdb044105d63f39
COPY files/eval_apple_incremental_game.py /tmp/eval_apple_incremental_game.py
