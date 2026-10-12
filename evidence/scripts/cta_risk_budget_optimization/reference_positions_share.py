"""Overseas share of the image's shipped standard-answer positions.csv: evaluator (native units)
vs common-CNY (USDCNY from macro_factors_data.xlsx). Runs inside the judge image."""
import tarfile, io, sys
import pandas as pd
sys.path.insert(0, '/home/workspace/scoring')
import eval_script as E
tf = tarfile.open('/home/workspace/scoring/standard_answer_artifacts.tar.gz')
pos = pd.read_csv(tf.extractfile('./backtest_results/positions.csv'))
print('positions columns', list(pos.columns), len(pos))
I = '/home/workspace/input/'
px = pd.concat([pd.read_excel(I + 'futures_price_data.xlsx', sheet_name=s)[['date', 'ticker', 'close']] for s in ('domestic_futures', 'overseas_futures')])
px['date'] = pd.to_datetime(px['date'])
spec = pd.read_excel(I + 'futures_contract_specs.xlsx', sheet_name='contract_specs').set_index('ticker')
fx = pd.read_excel(I + 'macro_factors_data.xlsx', sheet_name='fx_rates_daily'); fx['date'] = pd.to_datetime(fx['date'])
fxs = fx.drop_duplicates('date').set_index('date')['USDCNY'].sort_index()
tcol = [c for c in pos.columns if 'ticker' in c.lower()][0]
lcol = [c for c in pos.columns if 'lots' in c.lower() or 'position' in c.lower()][0]
dcol = [c for c in pos.columns if 'date' in c.lower()][0]
p = pos[[dcol, tcol, lcol]].rename(columns={dcol: 'date', tcol: 'ticker', lcol: 'lots'})
p['date'] = pd.to_datetime(p['date']); p = p[p['lots'] != 0]
p = p.merge(px, on=['date', 'ticker'], how='left').fillna({'close': 0})
p['mult'] = p['ticker'].map(spec['multiplier']).fillna(1)
p['fx'] = [float(fxs.asof(d)) if spec['currency'].get(t) == 'USD' else 1.0 for d, t in zip(p['date'], p['ticker'])]
p['n_native'] = p['lots'].abs() * p['mult'] * p['close']; p['n_cny'] = p['n_native'] * p['fx']
p['ov'] = p['ticker'].isin(E.OVERSEAS_TICKERS)
g = p.groupby('date').apply(lambda d: pd.Series({'native': d.loc[d.ov, 'n_native'].sum() / d['n_native'].sum(),
                                                'cny': d.loc[d.ov, 'n_cny'].sum() / d['n_cny'].sum()}))
print('days', len(g))
print(g.describe().to_string())
print('days >40%: native', int((g.native > 0.4).sum()), ' cny', int((g.cny > 0.4).sum()))
