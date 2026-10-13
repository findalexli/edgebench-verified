#!/usr/bin/env python3
"""Test submission for the portfolio_risk_calibration paired run (EdgeBench Verified).

A deliberately simple, documented strategy, written by us; it is not an AI solver and not tuned
for score. Only data up to the previous close is used for each decision.

- Signal: trailing 20-day return (momentum). Long the strongest two equity ETFs, the strongest
  commodity ETF and both bond ETFs; short the weakest shortable equity ETF.
- Risk scale: 20-day vs 60-day realized volatility of the equal-weight basket, in [0.6, 2.0];
  exposure is divided by the scale.
- Rebalancing: every 20 trading days, plus an extra one (trigger "risk_scale_change") when the
  scale moves by 0.15 or more, at least 5 trading days after the previous rebalance.
- VaR: parametric 95% VaR of the held weights from a 60-day covariance window, recalibrated
  every 20 days from the observed breach rate.

GROSS (overall exposure), SIGN and EXCESS_FORMULA are the only arm parameters; the paired run
writes one copy of this file per arm with different values. SIGN = -1 ranks the momentum signal the
wrong way round. EXCESS_FORMULA only changes the self-reported `excess_return_annual`:
'stated' = strategy annualized return - benchmark annualized return (the task instructions);
'grader' = (1 + strategy period return - benchmark period return)^(252/N) - 1 (the original grader).
The grader does not read the self-reported excess, so it cannot change the score.
"""
import json
import os
import sys

import numpy as np
import pandas as pd

GROSS = 1.0
SIGN = 1
LOOKBACK = 20
EXCESS_FORMULA = 'stated'   # how this submission computes its own self-reported excess return

ETFS = ['510300.XSHG', '159935.XSHE', '159915.XSHE', '513660.XSHG', '513500.XSHG',
        '511010.XSHG', '511220.XSHG', '518880.XSHG', '510410.XSHG', '159001.XSHE']
EQUITY = ETFS[:5]
BONDS = ['511010.XSHG', '511220.XSHG']
COMMOD = ['518880.XSHG', '510410.XSHG']
COMMISSION = 0.0005
SHORT_RATE = 0.04
CAPITAL = 10_000_000


def load():
    for f in ('etf_prices_test.csv', 'etf_info.csv', 'test_period.txt'):
        if not os.path.exists(f):
            raise SystemExit(f'missing evaluation file {f}')
    start, end = open('test_period.txt', encoding='utf-8').read().strip().split(',')
    df = pd.read_csv('etf_prices_test.csv', encoding='utf-8-sig')
    df['date'] = pd.to_datetime(df['date'])
    df = df[(df['date'] >= start) & (df['date'] <= end)]
    close = df.pivot(index='date', columns='stock_code', values='close')[ETFS].ffill()
    return close


def target_weights(close, i, scale):
    """Weights decided at the close of day i (uses rows 0..i only)."""
    hist = close.iloc[:i + 1]
    if len(hist) < 21:
        w = {e: 0.10 for e in EQUITY}
        w.update({b: 0.15 for b in BONDS})
        w.update({c: 0.06 for c in COMMOD})
        w['513500.XSHG'] = -0.12
    else:
        mom = SIGN * (hist.iloc[-1] / hist.iloc[-1 - min(LOOKBACK, len(hist) - 1)] - 1)
        eq = mom[EQUITY].sort_values(ascending=False)
        w = {e: 0.0 for e in ETFS}
        w[eq.index[0]] = 0.22
        w[eq.index[1]] = 0.18
        w[eq.index[-1]] = -0.16
        w[mom[COMMOD].idxmax()] = 0.14
        for b in BONDS:
            w[b] = 0.20
    g = GROSS / scale
    out = {}
    for e in ETFS:
        x = w.get(e, 0.0) * g
        out[e] = float(np.clip(x, -0.25, 0.25))
    # class caps (sum of absolute weights)
    for cls, cap in ((EQUITY, 0.60), (BONDS, 0.60), (COMMOD, 0.15)):
        tot = sum(abs(out[e]) for e in cls)
        if tot > cap:
            for e in cls:
                out[e] *= cap / tot
    return {e: round(out[e], 6) for e in ETFS}


def risk_scale(close, i):
    r = close.iloc[:i + 1][EQUITY + COMMOD].pct_change().mean(axis=1).dropna()
    if len(r) < 20:
        return 1.2
    v20 = r.iloc[-20:].std()
    v60 = r.iloc[-60:].std()
    return float(np.clip(1.2 * v20 / v60 if v60 > 0 else 1.2, 0.6, 2.0))


def main():
    close = load()
    rets = close.pct_change()
    dates = close.index
    n = len(dates)
    nav = [1.0]
    weights = [None] * n
    rebal = []
    scales = []
    var_hist = []
    var_breaks = []
    vol_events = []
    trades = []
    open_pos = {}   # etf -> (open_date, open_price, qty, direction)
    last_rebal = -100
    var_mult = 1.645
    cur = {e: 0.0 for e in ETFS}

    def rebalance(i, new, trigger, scale):
        nonlocal cur, last_rebal
        d = dates[i].strftime('%Y-%m-%d')
        for e in ETFS:
            if abs(new[e] - cur[e]) < 1e-9:
                continue
            if e in open_pos:
                od, op, qty, dr = open_pos.pop(e)
                cp = float(close[e].iloc[i])
                ret = (cp / op - 1) * (1 if dr == 'long' else -1)
                trades.append({'open_date': od, 'close_date': d, 'stock_code': e, 'direction': dr,
                               'open_price': round(op, 4), 'close_price': round(cp, 4), 'qty': qty,
                               'return': round(ret, 6)})
            if abs(new[e]) > 1e-9:
                p = float(close[e].iloc[i])
                qty = max(100, int(abs(new[e]) * nav[-1] * CAPITAL / p / 100) * 100)
                open_pos[e] = (d, p, qty, 'long' if new[e] > 0 else 'short')
        rebal.append({'date': d, 'trigger': trigger, 'risk_scale': round(scale, 4)})
        cur = dict(new)
        last_rebal = i

    scale = risk_scale(close, 0)
    rebalance(0, target_weights(close, 0, scale), 'initial', scale)
    prev_scale_at_rebal = scale
    for i in range(n):
        d = dates[i].strftime('%Y-%m-%d')
        if i > 0:
            w = cur
            r = rets.iloc[i].fillna(0.0)
            gross = sum(w[e] * r[e] for e in ETFS)
            nav.append(nav[-1] * (1 + gross - sum(abs(w[e]) for e in ETFS if w[e] < 0) * SHORT_RATE / 365))
        held = dict(cur)
        weights[i] = held
        # VaR for the weights held over (i-1, i], estimated from returns up to i-1
        past = rets.iloc[max(1, i - 60):i]
        if len(past) >= 10:
            cov = past.cov().fillna(0.0).values
            wv = np.array([held[e] for e in ETFS])
            var95 = float(var_mult * np.sqrt(max(wv @ cov @ wv, 1e-12)))
        else:
            var95 = 0.02
        var_hist.append({'date': d, 'var_95': round(var95, 6)})
        if i > 0 and nav[-1] / nav[-2] - 1 < -var95:
            var_breaks.append({'date': d, 'return': round(nav[-1] / nav[-2] - 1, 6), 'var_95': round(var95, 6)})
        if i % 20 == 0 and i >= 40:
            rate = len(var_breaks) / max(1, i)
            var_mult = float(np.clip(var_mult * (1 + (rate - 0.05) * 4), 1.2, 2.3))
        # decide at the close of day i for day i+1
        s = risk_scale(close, i)
        scales.append({'date': d, 'scale_factor': round(s, 4)})
        if i == n - 1:
            break
        since = i - last_rebal
        if since >= 5 and abs(s - prev_scale_at_rebal) >= 0.15:
            vol_events.append({'date': d, 'scale_before': round(prev_scale_at_rebal, 4), 'scale_after': round(s, 4)})
            new = target_weights(close, i, s)
            new_cost = sum(abs(new[e] - cur[e]) for e in ETFS) * COMMISSION
            rebalance(i, new, 'risk_scale_change', s)
            nav[-1] *= (1 - new_cost)
            prev_scale_at_rebal = s
        elif since >= 20:
            new = target_weights(close, i, s)
            new_cost = sum(abs(new[e] - cur[e]) for e in ETFS) * COMMISSION
            rebalance(i, new, 'scheduled', s)
            nav[-1] *= (1 - new_cost)
            prev_scale_at_rebal = s
    # close every open position on the last day
    dlast = dates[-1].strftime('%Y-%m-%d')
    for e, (od, op, qty, dr) in list(open_pos.items()):
        cp = float(close[e].iloc[-1])
        ret = (cp / op - 1) * (1 if dr == 'long' else -1)
        trades.append({'open_date': od, 'close_date': dlast, 'stock_code': e, 'direction': dr,
                       'open_price': round(op, 4), 'close_price': round(cp, 4), 'qty': qty, 'return': round(ret, 6)})

    # weights[i] are the weights held over (i-1, i]: they earn day i's return
    daily_weights = [{'date': dates[i].strftime('%Y-%m-%d'), 'weights': weights[i]} for i in range(n)]
    daily_nav = [{'date': dates[i].strftime('%Y-%m-%d'), 'nav': round(nav[i], 8)} for i in range(n)]

    s = pd.Series(nav)
    r = s.pct_change().dropna()
    sharpe = float(r.mean() * 252 / (r.std() * np.sqrt(252)))
    mdd = float(((s - s.cummax()) / s.cummax()).min())
    tw = pd.DataFrame([dw['weights'] for dw in daily_weights])
    turnover = float(tw.diff().abs().sum(axis=1).sum() / 2 / max(len(r) / 252, 0.5))
    vb = len(var_breaks) / max(1, n - 1)
    # 60/30/10 benchmark as the instructions describe it (equal weights inside each class, daily)
    br = (0.6 * rets[EQUITY].mean(axis=1) + 0.3 * rets[BONDS].mean(axis=1)
          + 0.1 * rets[COMMOD].mean(axis=1)).fillna(0.0)
    bnav = (1 + br).cumprod()
    k = 252 / n
    a_tot = nav[-1] / nav[0] - 1
    b_tot = float(bnav.iloc[-1] / bnav.iloc[0] - 1)
    if EXCESS_FORMULA == 'stated':
        excess = ((1 + a_tot) ** k - 1) - ((1 + b_tot) ** k - 1)
    else:
        excess = (1 + a_tot - b_tot) ** k - 1
    res = {
        'daily_nav': daily_nav,
        'daily_weights': daily_weights,
        'trades': trades,
        'metrics': {'sharpe_ratio': round(sharpe, 4), 'max_drawdown': round(mdd, 4),
                    'annual_turnover': round(turnover, 4), 'var_break_rate': round(vb, 4),
                    'total_return': round(nav[-1] - 1, 4),
                    'excess_return_annual': round(excess, 6), 'excess_formula': EXCESS_FORMULA},
        'risk_calibration': {'scale_factor_history': scales, 'var_history': var_hist,
                             'rebalance_history': rebal, 'var_break_events': var_breaks,
                             'volatility_events': vol_events},
    }
    with open('backtest_results.json', 'w', encoding='utf-8') as f:
        json.dump(res, f)
    print(f'excess({EXCESS_FORMULA})={excess:.6f} nav={nav[-1]:.4f} sharpe={sharpe:.3f} mdd={mdd:.4f} turnover={turnover:.3f} var_break={vb:.4f}')


if __name__ == '__main__':
    if '--backtest' not in sys.argv and not os.path.exists('etf_prices_test.csv'):
        raise SystemExit('run with --backtest in the evaluation directory')
    main()
