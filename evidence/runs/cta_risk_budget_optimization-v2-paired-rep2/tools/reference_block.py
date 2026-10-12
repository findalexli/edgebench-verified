"""Run the INSTALLED CTAEvaluator._evaluate_risk_constraints cross-border block on the task's
shipped standard-answer positions.csv / trades.csv (from scoring/standard_answer_artifacts.tar.gz).
Same stubs as repro_cross_border.py: participation gate -> pass, nav_history omitted (so the
vol/drawdown veto cannot fire), costs_fx score set to 0 and to 2. No evaluator source is modified;
whichever eval_script.py the image installs (v1 or v2) is the code under test."""
import sys, io, contextlib, tarfile, hashlib
import pandas as pd
sys.path.insert(0, '/home/workspace/scoring')
import eval_script as E
print('eval_script sha256', hashlib.sha256(open(E.__file__, 'rb').read()).hexdigest())
tf = tarfile.open('/home/workspace/scoring/standard_answer_artifacts.tar.gz')
pos = pd.read_csv(tf.extractfile('./backtest_results/positions.csv'))
trd = pd.read_csv(tf.extractfile('./backtest_results/trades.csv'))
ev0 = E.CTAEvaluator('/nonexistent', '/home/workspace/input')
with contextlib.redirect_stdout(io.StringIO()):
    ev0._load_raw_data()
raw = ev0.raw_data
for cfx in (0, 2):
    ev = E.CTAEvaluator('/nonexistent', '/home/workspace/input'); ev.raw_data = raw
    frames = {'holdings_detail': pos, 'trade_records': trd, 'nav_history': None}
    ev._load_df = lambda k: None if frames.get(k) is None else frames[k].copy()
    ev._compute_exposure_stats = lambda *a, **k: {'participation_status': 'pass'}
    ev.details['backtest_verification'] = {'costs_fx': {'score': cfx}}
    ev.scores['backtest_verification'] = 10
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        ev._evaluate_risk_constraints()
    lines = [l.strip() for l in buf.getvalue().splitlines() if 'Overseas ratio' in l or 'FX conversion' in l]
    print(f'reference cost_fx={cfx} -> cross_border {ev.details["risk_constraints"]["cross_border"]} {lines}')
