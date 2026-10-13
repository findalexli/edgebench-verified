# vibrating_path_graph_coloring v2: the evaluator runs at most as many cases at once as the grader has CPUs
# (cgroup CPU quota, 1..8) instead of always 8, so each case keeps a whole CPU for its 30 s limit.
# Only the one changed file is copied; nothing is installed.
FROM seededge/edgebench.judge.vibrating_path_graph_coloring@sha256:db8a9741831762040afb7e9819f997eb5f5293641fd5cd97d27fce3880ce084e
COPY files/eval_vibrating_path.py /tmp/eval_vibrating_path.py
