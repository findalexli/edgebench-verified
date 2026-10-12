"""Call the INSTALLED original calculate_metrics_from_data (pinned judge image) on authored NAV paths.
Run: docker run --rm --network none --memory 2g --cpus 1 -v $PWD:/s:ro --entrypoint python3 IMAGE -I /s/witness.py
"""
import sys
from fractions import Fraction as F
import pandas as pd
sys.path.insert(0, '/home/workspace/scoring')
import eval_script as E
print('module', E.__file__)

def paths(n, a_tot, b_tot):
    dates = pd.bdate_range('2025-01-02', periods=n)
    # geometric paths (constant daily growth) ending exactly at 1+a_tot, 1+b_tot
    ga = (1 + a_tot) ** (1 / (n - 1)); gb = (1 + b_tot) ** (1 / (n - 1))
    nav = [{'date': d.strftime('%Y-%m-%d'), 'nav': ga ** i} for i, d in enumerate(dates)]
    nav[-1]['nav'] = 1 + a_tot
    bench = pd.Series([gb ** i for i in range(n)], index=dates); bench.iloc[-1] = 1 + b_tot
    w = [{'date': nav[0]['date'], 'weights': {'x': 0.5}}, {'date': nav[1]['date'], 'weights': {'x': 0.5}}]
    return nav, w, bench

for n, a, b in [(126, 0.20, 0.10), (243, 0.20, 0.10), (243, 0.1587, 0.10), (252, 0.20, 0.10), (126, -0.05, 0.10)]:
    nav, w, bench = paths(n, a, b)
    m, err = E.calculate_metrics_from_data(nav, w, bench)
    k = 252 / n
    orig = (1 + a - b) ** k - 1
    contract = (1 + a) ** k - (1 + b) ** k
    line = f'n={n} a={a} b={b} evaluator excess={m["excess_return_annual"]} (formula {orig:.6f}) contract={contract:.6f} ' \
           f'score_excess orig={E.score_excess_return(m["excess_return_annual"]):.3f} contract={E.score_excess_return(contract):.3f} ' \
           f'annual_return={m["annual_return"]} bench_annual={m["benchmark_annual_return"]} IR={m["information_ratio"]} sortino={m["sortino_ratio"]}'
    if n == 126 and a == 0.20:
        kk = F(252, 126)
        line += f' | exact: orig={(1 + F(1, 5) - F(1, 10)) ** 2 - 1} contract={(F(6, 5)) ** 2 - (F(11, 10)) ** 2} geometric={(F(6,5)/F(11,10))**2-1}'
    print(line)
