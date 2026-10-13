"""Excess-return threshold check on the INSTALLED grader (original or fixed image), run as
  python3 -I /s/threshold_paths.py           (inside the judge image, --network none)

The grader's own `calculate_benchmark_nav` on the hidden test prices gives the real benchmark and
calendar. Each authored NAV path grows at a constant daily rate over that calendar and ends at
1 + a, so only its period return a differs between rows. The installed
`calculate_metrics_from_data` and the installed score functions are then called exactly as
`main()` calls them (on the 4-decimal values it returns).

Rows:
  T1  a chosen so the instructions' formula gives exactly 12% (the full-marks line):
      (1+a)^k - (1+b)^k = 0.12
  T2  a chosen so the original grader's formula gives exactly 12%: (1+a-b)^k - 1 = 0.12
  T3  a = b (zero excess under both formulas)
  T4  a = 0.30, T5 a = 0.20 (positive and negative excess in the linear part of the score)
"""
import json
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, '/home/workspace/scoring')
import eval_script as E  # noqa: E402

prices = E.load_prices('/home/workspace/scoring/etf_prices_test.csv')
bench = E.calculate_benchmark_nav(prices, E.TEST_START, E.TEST_END)
dates = bench.index
n = len(dates)
k = 252 / n
b = float(bench.iloc[-1] / bench.iloc[0] - 1)

a_t1 = (0.12 + (1 + b) ** k) ** (1 / k) - 1
a_t2 = 1.12 ** (1 / k) - 1 + b
rows = [('T1 instructions formula = 12%', a_t1), ('T2 original-grader formula = 12%', a_t2),
        ('T3 a = b', b), ('T4 a = 0.30', 0.30), ('T5 a = 0.20', 0.20)]

print(json.dumps({'module': E.__file__, 'n_dates': n, 'k': k, 'bench_period_return': b}))
for label, a in rows:
    g = (1 + a) ** (1 / (n - 1))
    nav = [{'date': d.strftime('%Y-%m-%d'), 'nav': float(g ** i)} for i, d in enumerate(dates)]
    nav[-1]['nav'] = 1 + a
    # weights only feed turnover (not scored here); two distinct days keep the function's path normal
    w = [{'date': nav[i]['date'], 'weights': {e: (0.1 if e != E.ALL_ETFS[-1] else 0.0) for e in E.ALL_ETFS}}
         for i in range(n)]
    m, err = E.calculate_metrics_from_data(nav, w, bench)
    out = {'row': label, 'a': a,
           'excess_return_annual': m['excess_return_annual'],
           'information_ratio': m['information_ratio'], 'sortino_ratio': m['sortino_ratio'],
           'annual_return': m['annual_return'], 'benchmark_annual_return': m['benchmark_annual_return'],
           'score_excess': E.score_excess_return(m['excess_return_annual']),
           'score_ir': E.score_information_ratio(m['information_ratio']),
           'score_sortino': E.score_sortino(m['sortino_ratio'])}
    out['score_three_parts'] = out['score_excess'] + out['score_ir'] + out['score_sortino']
    print(json.dumps(out))
