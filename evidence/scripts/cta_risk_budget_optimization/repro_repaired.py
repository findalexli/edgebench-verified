"""Apply repair.patch's change textually to the installed source, load it as a module, rerun repro cases."""
import sys, types, runpy
src = open('/home/workspace/scoring/eval_script.py').read()
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
src = src.replace(old, new).replace(anchor, pre + anchor)
mod = types.ModuleType('eval_script'); mod.__file__ = 'patched'
exec(compile(src, 'eval_script_patched.py', 'exec'), mod.__dict__)
sys.modules['eval_script'] = mod
runpy.run_path('/s/repro_cross_border.py', run_name='__main__')
