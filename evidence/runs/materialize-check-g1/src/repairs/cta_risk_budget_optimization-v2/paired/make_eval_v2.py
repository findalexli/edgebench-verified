"""Write the v2 eval_script.py: convert USD-denominated notionals to CNY (USDCNY, same series and
same fallback as the evaluator's own fx_for) inside the cross-border overseas-ratio check.
This is the exact textual change that scripts/cta_risk_budget_optimization/repro_repaired.py tested.
Usage: python3 -I make_eval_v2.py <original eval_script.py> <out eval_script.py>"""
import sys, hashlib
raw = open(sys.argv[1], 'rb').read()
assert hashlib.sha256(raw).hexdigest() == '252f864a1a515fb48283644268938afd75f417fcfe34bba09fc8bab49cd41300'
src = raw.decode('utf-8')
old = "                        n = l * m * p; tn += n\n"
assert src.count(old) == 1
new = ("                        fx = 1.0\n"
       "                        if ccy_lk.get(t, 'CNY') == 'USD':\n"
       "                            v = fx_s.asof(pd.Timestamp(date)) if len(fx_s) else float('nan')\n"
       "                            fx = 7.0 if pd.isna(v) else float(v)\n"
       "                        n = l * m * p * fx; tn += n\n")
anchor = "                violations = 0; days = 0\n"
assert src.count(anchor) == 1
pre = ("                ccy_lk = {}\n"
       "                if 'specs' in self.raw_data:\n"
       "                    for _, r in self.raw_data['specs'].iterrows(): ccy_lk[r['ticker']] = str(r.get('currency', 'CNY')).upper()\n"
       "                fx_s = pd.Series(dtype=float)\n"
       "                if 'fx' in self.raw_data and 'USDCNY' in self.raw_data['fx'].columns:\n"
       "                    _fx = self.raw_data['fx'].copy(); _fx['date'] = pd.to_datetime(_fx['date'])\n"
       "                    fx_s = _fx.drop_duplicates('date').set_index('date')['USDCNY'].astype(float).sort_index()\n")
out = src.replace(old, new).replace(anchor, pre + anchor).encode('utf-8')
open(sys.argv[2], 'wb').write(out)
print('v2 eval_script sha256', hashlib.sha256(out).hexdigest())
