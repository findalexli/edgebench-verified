# v2 judge image: convex-quadrilateral flip rule + 10 regenerated hidden cases + evaluator parallelism at most
# the grader's CPU quota (cgroup, 1..8) instead of always 8. COPY only.
FROM --platform=linux/amd64 seededge/edgebench.judge.triangulation_coloring_optimization@sha256:beeea76373084ef4e1fe5324172cf4d5fbc166943daf4cd8b60306cd89dcf671
COPY files/tools/src/triangulation.py /home/workspace/triangulation_coloring/tools/src/triangulation.py
COPY files/cases/ /home/workspace/triangulation_coloring/cases/
COPY files/eval_triangulation_coloring.py /tmp/eval_triangulation_coloring.py
