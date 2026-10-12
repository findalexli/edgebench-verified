# smt_solver v2: UF witness values are keyed by function symbol and EVALUATED argument values
# (ground-term keys such as "(f a)" apply wherever f is applied to the value of a), as
# smtlib_spec.md's "canonical ground terms" describes. Only COPY; nothing is installed.
FROM seededge/edgebench.judge.smt_solver@sha256:2bf3482a5b2952eeadecf16e33041c13c284b7ce5d93f3491b7cfd5088d91fc6
COPY files/evaluate.py /home/workspace/smt_judge/scripts/evaluate.py
