# smt_solver v2: (1) UF witness values are keyed by function symbol and EVALUATED argument values
# (ground-term keys such as "(f a)" apply wherever f is applied to the value of a), as
# smtlib_spec.md's "canonical ground terms" describes; (2) the evaluator runs at most as many solver
# processes at once as the grader has CPUs (cgroup quota, 1..8), so --parallel 16 becomes at most the
# quota. task.json.in raises eval_timeout to match. Only COPY; nothing is installed.
FROM seededge/edgebench.judge.smt_solver@sha256:2bf3482a5b2952eeadecf16e33041c13c284b7ce5d93f3491b7cfd5088d91fc6
COPY files/evaluate.py /home/workspace/smt_judge/scripts/evaluate.py
