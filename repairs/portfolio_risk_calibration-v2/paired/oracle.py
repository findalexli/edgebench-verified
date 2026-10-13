"""Independent oracle for the threshold rows: the two excess formulas in 60-digit decimal
arithmetic (Python `decimal`, correctly rounded powers), from the benchmark period return and
date count that threshold_paths.py prints. Pure standard library.

Usage: python3 oracle.py <threshold-v1.log> <threshold-v2.log>
"""
import json
import sys
from decimal import Decimal as D, getcontext

getcontext().prec = 60


def excess(a, b, k):
    stated = (1 + a) ** k - (1 + b) ** k
    grader = (1 + a - b) ** k - 1
    return stated, grader


def score(x):  # copy of score_excess_return (eval_script.py:1000-1012)
    if x >= D('0.12'):
        return D(20)
    if x >= 0:
        return 20 * x / D('0.12')
    return max(D(-10), 10 * x / D('0.10'))


for path in sys.argv[1:]:
    lines = [json.loads(s) for s in open(path) if s.startswith('{')]
    head, rows = lines[0], lines[1:]
    n = head['n_dates']
    k = D(252) / D(n)
    b = D(repr(head['bench_period_return']))
    print(f'{path}: n={n} k=252/{n} b={b}')
    for r in rows:
        a = D(repr(r['a']))
        st, gr = excess(a, b, k)
        inst = D(repr(r['excess_return_annual']))
        print(f"  {r['row']}: stated={st:.10f} grader={gr:.10f} installed(4dp)={inst} "
              f"score(stated,4dp)={score(round(st, 4)):.4f} score(grader,4dp)={score(round(gr, 4)):.4f} "
              f"installed_score={r['score_excess']:.4f}")
