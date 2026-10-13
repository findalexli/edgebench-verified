#!/usr/bin/env python3
"""Paired original/FX-only/NAV-candidate genuine risk-helper controls; no images run."""
import contextlib
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import types
from fractions import Fraction
import pandas as pd

PACKAGE = Path(__file__).resolve().parents[1]
lock = json.loads((PACKAGE / 'source-lock.json').read_text())
original = Path(sys.argv[1]).read_bytes()
assert hashlib.sha256(original).hexdigest() == lock['changed_files'][0]['original_sha256']


def patched(patch):
    with tempfile.TemporaryDirectory() as temp:
        dst = Path(temp) / 'files/eval_script.py'
        dst.parent.mkdir()
        dst.write_bytes(original)
        subprocess.run(['patch', '--batch', '-p1', '-i', str(patch)], cwd=temp, check=True, stdout=subprocess.DEVNULL)
        return dst.read_bytes()


sources = {'original': original, 'fx_only_v2': patched(PACKAGE / 'paired/fx-only-v2.patch'), 'nav_v2_1': patched(PACKAGE / 'repair.patch')}
assert hashlib.sha256(sources['nav_v2_1']).hexdigest() == lock['changed_files'][0]['replacement_sha256']
modules = {}
for label, source in sources.items():
    mod = types.ModuleType('cta_' + label)
    exec(compile(source, label, 'exec'), mod.__dict__)
    modules[label] = mod

date = pd.Timestamp('2021-01-04')
raw = {
    'domestic': pd.DataFrame({'date': [date], 'ticker': ['CU.SHF'], 'close': [1e7]}),
    'overseas': pd.DataFrame({'date': [date], 'ticker': ['GC.CME'], 'close': [1e7]}),
    'specs': pd.DataFrame({'ticker': ['CU.SHF', 'GC.CME'], 'multiplier': [1., 1.], 'currency': ['CNY', 'USD']}),
    'fx': pd.DataFrame({'date': [date], 'USDCNY': [7.]}),
}
# domestic lots, overseas lots, NAV. All defined NAVs use total CNY units.
cases = {
    'leveraged_overseas_breach': (210, 15, 1.5e9),  # gross3150m, overseas1050m => 1/3 gross but70% NAV
    'unleveraged_compliant': (15, 6, 1.5e9),  # 420m / NAV1500m compliant; gross ratio42/57 fails
    'compliant_both': (150, 3, 1.5e9),
    'bad_both': (3, 30, 1.5e9),
    'domestic_only': (150, 0, 1.5e9),
    'at_boundary': (150, 6, 1.05e9),
    'missing_nav': (150, 3, None),
    'missing_same_date': (150, 3, 1.5e9),
    'zero_nav': (150, 3, 0),
    'nonfinite_nav': (150, 3, float('nan')),
}
rows=[]
for name, (domestic, overseas, nav) in cases.items():
    results={}
    for label, mod in modules.items():
        ev=mod.CTAEvaluator('/nonexistent', '/nonexistent')
        ev.raw_data=raw
        frames={'holdings_detail': pd.DataFrame({'date':[date,date],'ticker':['CU.SHF','GC.CME'],'lots':[domestic,overseas]}), 'trade_records':None, 'nav_history':None if nav is None else pd.DataFrame({'date':[date+pd.Timedelta(days=1) if name=='missing_same_date' else date], 'nav':[nav]})}
        ev._load_df=lambda key: None if frames.get(key) is None else frames[key].copy()
        ev._compute_exposure_stats=lambda *a,**kw: {'participation_status':'pass'}
        ev.scores['backtest_verification']=10
        ev.details['backtest_verification']={'costs_fx':{'score':0}}
        with contextlib.redirect_stdout(io.StringIO()), __import__('warnings').catch_warnings():
            __import__('warnings').simplefilter('ignore',RuntimeWarning)
            ev._evaluate_risk_constraints()
        results[label]=ev.details['risk_constraints']['cross_border']
    valid_nav = nav is not None and pd.notna(nav) and nav>0 and name!='missing_same_date'
    ratio=Fraction(overseas*7*10000000, int(nav)) if valid_nav else None
    expected=1 if ratio is not None and ratio<=Fraction(2,5) else 0
    assert results['nav_v2_1']==expected,(name,results,expected)
    rows.append({'control':name,'overseas_cny_over_nav':str(ratio) if ratio is not None else None,'ratio_credit_expected':expected,'cross_border':results})
assert rows[0]['cross_border']=={'original':1,'fx_only_v2':1,'nav_v2_1':0}
assert rows[1]['cross_border']=={'original':1,'fx_only_v2':0,'nav_v2_1':1}
print(json.dumps({'scope':'Actual risk helper; participation stubbed; one-day NAV avoids volatility veto; no end-to-end score claim','source_sha256':{k:hashlib.sha256(v).hexdigest() for k,v in sources.items()},'controls':rows},indent=2))
