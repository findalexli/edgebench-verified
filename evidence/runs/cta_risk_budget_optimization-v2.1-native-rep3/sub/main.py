#!/usr/bin/env python3
"""Synthetic but internally consistent CTA submission (EdgeBench Verified scorer control).

Constant-weight portfolio rebalanced to the weights in config.json, sized on total CNY NAV.
NAV, positions, trades, costs and FX are generated from the task input files with the same
accounting as the grader's replay (previous-day lots x multiplier x close change x same-day
USDCNY, minus per-lot round-trip cost x FX). It is a scorer test fixture, not a strategy.
Optional config key "drop_nav_dates": dates removed from nav_history.csv only (to model a
NAV file that lacks a holdings date).
"""
import json, os
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
def inp(name):
    for d in (HERE, os.path.join(HERE, 'input'), '/home/workspace/input'):
        p = os.path.join(d, name)
        if os.path.exists(p):
            return p
    raise FileNotFoundError(name)

cfg = json.load(open(os.path.join(HERE, 'config.json')))
W = cfg['weights']; NAV0 = float(cfg.get('initial_nav_cny', 1.5e9)); BAND = float(cfg.get('rebalance_band', 0.02))
px = pd.read_excel(inp('futures_price_data.xlsx'), sheet_name=None)
raw = pd.concat([px['domestic_futures'][['date', 'ticker', 'close']], px['overseas_futures'][['date', 'ticker', 'close']]])
raw['date'] = pd.to_datetime(raw['date'])
P = raw.pivot_table(index='date', columns='ticker', values='close').sort_index().ffill()
specs = pd.read_excel(inp('futures_contract_specs.xlsx'), sheet_name='contract_specs')
costs = pd.read_excel(inp('futures_contract_specs.xlsx'), sheet_name='transaction_costs')
fxd = pd.read_excel(inp('macro_factors_data.xlsx'), sheet_name='fx_rates_daily')
fxd['date'] = pd.to_datetime(fxd['date'])
FX = fxd.drop_duplicates('date').set_index('date')['USDCNY'].astype(float).sort_index()
mult = {str(r.ticker): float(r.multiplier) for r in specs.itertuples()}
ccy = {str(r.ticker): str(r.currency).upper() for r in specs.itertuples()}
sector = {str(r.ticker): str(getattr(r, 'sector', '')) for r in specs.itertuples()} if 'sector' in specs.columns else {}
cpl = {str(r.ticker): (float(r.total_round_trip_cost_per_lot), str(r.currency).upper()) for r in costs.itertuples()}
def fx(d, c):
    if c != 'USD':
        return 1.0
    v = FX.asof(pd.Timestamp(d))
    return 7.0 if pd.isna(v) else float(v)

dates = list(P.index); tick = sorted(W)
lots = {t: 0.0 for t in tick}; nav = NAV0; peak = NAV0
nav_rows, pos_rows, trd_rows = [], [], []
for i, d in enumerate(dates):
    pnl = 0.0
    if i > 0:
        pd_ = dates[i - 1]
        for t in tick:
            if lots[t]:
                pnl += lots[t] * mult[t] * (P.at[d, t] - P.at[pd_, t]) * fx(d, ccy[t])
    pre = nav + pnl
    cost = 0.0
    if i > 0:
        for t in tick:
            unit = mult[t] * P.at[d, t] * fx(d, ccy[t])
            tgt = float(np.round(W[t] * pre / unit))
            if lots[t] == 0 or abs(tgt - lots[t]) > BAND * abs(tgt):
                dl = tgt - lots[t]
                if dl:
                    c, cc = cpl[t]; tc = abs(dl) * c * fx(d, cc); cost += tc
                    trd_rows.append({'date': d.date(), 'ticker': t, 'lots_change': dl, 'side': 'BUY' if dl > 0 else 'SELL',
                                     'price': P.at[d, t], 'multiplier': mult[t], 'currency': ccy[t], 'fx_rate': fx(d, ccy[t]),
                                     'notional_cny': abs(dl) * unit, 'transaction_cost_cny': tc})
                    lots[t] = tgt
    new_nav = pre - cost
    daily_pnl = new_nav - nav
    ret = daily_pnl / nav if i > 0 else 0.0
    nav = new_nav; peak = max(peak, nav)
    gross = ovs = net = 0.0; npos = 0
    for t in tick:
        if lots[t]:
            n = lots[t] * mult[t] * P.at[d, t] * fx(d, ccy[t]); npos += 1
            gross += abs(n); net += n
            if ccy[t] == 'USD': ovs += abs(n)
            pos_rows.append({'date': d.date(), 'ticker': t, 'lots': lots[t], 'notional_cny': n, 'weight': n / nav,
                             'price': P.at[d, t], 'currency': ccy[t], 'sector': sector.get(t, '')})
    nav_rows.append({'date': d.date(), 'nav_cny': nav, 'unit_nav': nav / NAV0, 'daily_pnl_cny': daily_pnl if i else 0.0,
                     'daily_return': ret, 'drawdown': (peak - nav) / peak, 'dd_scale': 1.0,
                     'gross_exposure': gross / nav, 'net_exposure': net / nav, 'overseas_exposure': ovs / nav,
                     'num_positions': npos})

os.makedirs(os.path.join(HERE, 'outputs'), exist_ok=True)
o = lambda n: os.path.join(HERE, 'outputs', n)
navdf = pd.DataFrame(nav_rows)
drop = set(cfg.get('drop_nav_dates', []))
navdf[~navdf['date'].astype(str).isin(drop)].to_csv(o('nav_history.csv'), index=False)
pd.DataFrame(pos_rows).to_csv(o('positions.csv'), index=False)
pd.DataFrame(trd_rows).to_csv(o('trades.csv'), index=False)
r = P.pct_change()
sig = []
for t in tick:
    s = pd.DataFrame({'date': [x.date() for x in dates], 'ticker': t,
                      'TSMOM': np.sign(P[t].pct_change(120)).fillna(0).values,
                      'XSMOM': (r.rolling(60).sum().rank(axis=1, pct=True)[t] - 0.5).fillna(0).values,
                      'CARRY': 0.0, 'BREAKOUT': np.sign(P[t] - P[t].rolling(20).mean()).fillna(0).values,
                      'MEANREV': (-(P[t] - P[t].rolling(20).mean()) / P[t].rolling(20).std()).clip(-2, 2).fillna(0).values})
    sig.append(s)
pd.concat(sig).to_csv(o('signal_matrix.csv'), index=False)
pd.DataFrame([{'date': dates[0].date(), 'strategy': k, 'risk_budget': 0.2, 'portfolio_scale': 1.0}
              for k in ['TSMOM', 'XSMOM', 'CARRY', 'BREAKOUT', 'MEANREV']]).to_csv(o('risk_budget_allocation.csv'), index=False)
s = navdf['nav_cny'].values; dr = np.diff(s) / s[:-1]
txt = (f"Final NAV {s[-1]:.0f} CNY; annual vol {np.std(dr)*np.sqrt(252):.4f}; max drawdown {navdf['drawdown'].max():.4f}.\n")
for n in ['performance_report.md', 'stress_test_report.md', 'sensitivity_analysis_report.md']:
    open(o(n), 'w').write('# ' + n[:-3] + '\n\nSynthetic scorer-control portfolio.\n' + txt)
json.dump({'random_seed': None, 'deterministic': True, 'weights': W, 'rebalance_band': BAND,
           'fx_source': 'macro_factors_data.xlsx fx_rates_daily USDCNY', 'cost_source': 'transaction_costs'},
          open(o('diagnostics.json'), 'w'), indent=1)
print('wrote', len(nav_rows), 'nav rows', len(pos_rows), 'positions', len(trd_rows), 'trades')
