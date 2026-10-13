# grid_turing_robot v2: the evaluator runs at most as many cases at once as the grader has CPUs
# (cgroup CPU quota, 1..8) instead of always 8, so each case keeps a whole CPU for its 30 s limit.
# Only the one changed file is copied; nothing is installed.
FROM seededge/edgebench.judge.grid_turing_robot@sha256:f67864ad75a3a2af0f7904a05a30b888f66ce2ed5c1f3cac7d7482e578a296c3
COPY files/eval_grid_turing_robot.py /tmp/eval_grid_turing_robot.py
