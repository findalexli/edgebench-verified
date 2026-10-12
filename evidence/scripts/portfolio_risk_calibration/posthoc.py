"""After the original evaluator ran in /home/workspace, recompute excess under the contract formula
from the same backtest_results.json and the evaluator's own benchmark NAV."""
import sys, json, os
sys.path.insert(0, '/home/workspace/scoring'); os.chdir('/home/workspace')
import eval_script as E
import pandas as pd
r = json.load(open('backtest_results.json'))
prices = E.load_prices()
bn = E.calculate_benchmark_nav(prices, E.TEST_START, E.TEST_END)
m, _ = E.calculate_metrics_from_data(r['daily_nav'], r['daily_weights'], bn)
df = pd.DataFrame(r['daily_nav']); df['date'] = pd.to_datetime(df['date']); s = df.set_index('date')['nav'].astype(float)
s = s[s.index >= E.TEST_START]; ci = s.index.intersection(bn.index); N = len(ci); k = 252 / N
a = s[ci].iloc[-1] / s[ci].iloc[0] - 1; b = bn[ci].iloc[-1] / bn[ci].iloc[0] - 1
orig = (1 + a - b) ** k - 1; con = (1 + a) ** k - (1 + b) ** k
scale = con / orig if orig else float('nan')
print(json.dumps({'aligned_N': N, 'k': k, 'agent_period': a, 'bench_period': b, 'excess_orig': orig, 'excess_contract': con,
  'evaluator_metrics': m,
  'score_excess_orig': E.score_excess_return(orig), 'score_excess_contract': E.score_excess_return(con),
  'IR_orig': m['information_ratio'], 'IR_contract': m['information_ratio'] * scale,
  'score_IR_orig': E.score_information_ratio(m['information_ratio']), 'score_IR_contract': E.score_information_ratio(m['information_ratio'] * scale),
  'sortino_orig': m['sortino_ratio'], 'sortino_contract': m['sortino_ratio'] * scale,
  'score_sortino_orig': E.score_sortino(m['sortino_ratio']), 'score_sortino_contract': E.score_sortino(m['sortino_ratio'] * scale)}, indent=1, default=float))
