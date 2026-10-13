# molecular_self_assembly v2: the evaluator runs at most as many cases at once as the grader has CPUs
# (cgroup CPU quota, 1..8) instead of 8 by default, so each case keeps a whole CPU for its 30 s limit.
# Only the one changed file is copied; nothing is installed.
FROM seededge/edgebench.judge.molecular_self_assembly@sha256:8afd932de7e54bacee44bcc33ceb4dab1125ad563aa81c1141717f1fc25c6da5
COPY files/eval_molecules.py /tmp/eval_molecules.py
