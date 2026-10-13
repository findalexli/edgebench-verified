"""Drive the INSTALLED original CTAEvaluator._evaluate_risk_constraints cross-border block.

Run inside the pinned judge image (read-only mount of this dir at /s):
  docker run --rm --network none --memory 2g --cpus 1 -v $PWD:/s:ro --entrypoint python3 IMAGE -I /s/repro_cross_border.py

Only the cross-border sub-score (cs['cross_border']) is examined. Gates that need a full
portfolio (participation stats) are stubbed to 'pass'; nav_history is omitted so the
drawdown/vol veto is not triggered. No evaluator source is modified.
"""
import sys, io, contextlib
from fractions import Fraction as F
import pandas as pd
if 'eval_script' not in sys.modules: sys.path.insert(0, '/home/workspace/scoring')
import eval_script as E
print('module file:', E.__file__)

def run(raw, holdings, trades, cost_fx_score):
    ev = E.CTAEvaluator('/nonexistent', '/home/workspace/input')
    ev.raw_data = raw
    frames = {'holdings_detail': holdings.copy(), 'trade_records': trades, 'nav_history': None}
    ev._load_df = lambda k: None if frames.get(k) is None else frames[k].copy()
    ev._compute_exposure_stats = lambda *a, **k: {'participation_status': 'pass'}
    ev.details['backtest_verification'] = {'costs_fx': {'score': cost_fx_score}}
    ev.scores['backtest_verification'] = 10
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        ev._evaluate_risk_constraints()
    line = [l for l in buf.getvalue().splitlines() if 'Overseas ratio' in l]
    return ev.details['risk_constraints']['cross_border'], line

def cny_share(raw, holdings, fx):
    """Independent oracle: exact-fraction overseas share in common CNY."""
    spec = raw['specs'].set_index('ticker')
    px = pd.concat([raw['domestic'], raw['overseas']]).set_index(['date', 'ticker'])['close']
    out = {}
    for d, g in holdings.groupby('date'):
        on = tn = F(0); onn = tnn = F(0)
        for _, r in g.iterrows():
            n = F(abs(r['lots'])) * F(str(spec.loc[r['ticker'], 'multiplier'])) * F(str(px[(d, r['ticker'])]))
            c = fx(d) if spec.loc[r['ticker'], 'currency'] == 'USD' else F(1)
            tn += n * c; tnn += n
            if r['ticker'] in E.OVERSEAS_TICKERS: on += n * c; onn += n
        out[d] = (onn / tnn, on / tn)
    return out

# ---- Case A: synthetic exact witness (prices 1, multipliers 1, USDCNY = 7) ----
d = pd.Timestamp('2021-01-04')
synth = {
    'domestic': pd.DataFrame({'date': [d], 'ticker': ['CU.SHF'], 'close': [1.0]}),
    'overseas': pd.DataFrame({'date': [d], 'ticker': ['GC.CME'], 'close': [1.0]}),
    'specs': pd.DataFrame({'ticker': ['CU.SHF', 'GC.CME'], 'multiplier': [1.0, 1.0], 'currency': ['CNY', 'USD']}),
    'fx': pd.DataFrame({'date': [d], 'USDCNY': [7.0]}),
}
tr_none = pd.DataFrame({'ticker': ['CU.SHF']})
tr_ov = pd.DataFrame({'ticker': ['GC.CME']})
cases = {
    'A_mixed_2CNY_1USD': pd.DataFrame({'date': [d, d], 'ticker': ['CU.SHF', 'GC.CME'], 'lots': [2, 1]}),
    'A_ctrl_domestic_only': pd.DataFrame({'date': [d], 'ticker': ['CU.SHF'], 'lots': [2]}),
    'A_ctrl_over_limit_native_too': pd.DataFrame({'date': [d, d], 'ticker': ['CU.SHF', 'GC.CME'], 'lots': [1, 1]}),
}
fx7 = lambda _d: F(7)
for name, h in cases.items():
    for tr, cfx in [(tr_none, 0), (tr_ov, 2)]:
        cb, line = run(synth, h, tr, cfx)
        print(name, 'trades_overseas=%s cost_fx=%d' % (len(tr[tr.ticker.isin(E.OVERSEAS_TICKERS)]) > 0, cfx),
              '-> cross_border', cb, line, 'oracle(native,cny)=', [tuple(map(str, v)) for v in cny_share(synth, h, fx7).values()])

# ---- Case B: the real task data (one real trading day, real prices/multipliers/USDCNY) ----
raw = {}
ev0 = E.CTAEvaluator('/nonexistent', '/home/workspace/input')
with contextlib.redirect_stdout(io.StringIO()):
    ev0._load_raw_data()
raw = ev0.raw_data
for k in ('domestic', 'overseas', 'fx'):
    raw[k]['date'] = pd.to_datetime(raw[k]['date'])
common = sorted(set(raw['domestic'].date) & set(raw['overseas'].date))
day = [x for x in common if x >= pd.Timestamp('2021-06-01')][0]
fxs = raw['fx'].drop_duplicates('date').set_index('date')['USDCNY'].sort_index()
fxr = lambda dd: F(str(float(fxs.asof(dd))))
# 10 lots CU.SHF vs 2 lots GC.CME (realistic sizes)
for gc_lots in (2, 8, 30):
  hB = pd.DataFrame({'date': [day, day], 'ticker': ['CU.SHF', 'GC.CME'], 'lots': [10, gc_lots]})
  for tr, cfx in [(tr_none, 0), (tr_ov, 2)]:
    cb, line = run(raw, hB, tr, cfx)
    print('  GC lots', gc_lots)
    o = list(cny_share(raw, hB, fxr).values())[0]
    print('B_real_day', day.date(), 'USDCNY', float(fxs.asof(day)), 'cost_fx=%d' % cfx, '-> cross_border', cb, line,
          'oracle native=%.4f cny=%.4f' % (float(o[0]), float(o[1])))
