import sys, json, time, shutil, os
sys.path.insert(0, '/opt/evaluator')
import eval_dabic_v2 as E
from pathlib import Path
case = sys.argv[1] if len(sys.argv) > 1 else 'smoke'
for form in ('data', 'model'):
    d = Path(f'/tmp/sub_{form}'); d.mkdir(exist_ok=True)
    shutil.copy(f'/in/dabic_directive_{form}.py', d / 'dabic_directive.py')
    for norm in ('L0', 'L1'):
        t = time.time()
        r = E._balanced_hidden_case_worker(str(d), case, norm, 123, False)
        snap = r.get('behavior_snapshot', {})
        print(form, case, norm, 'ok', r.get('ok'), r.get('error'), 'chi2', r.get('chi2_per_N'), 'iou', r.get('iou_vs_true'),
              'betas', [f'{b:.3g}' for b in r.get('beta_history', [])], 'dims', sorted(set(map(tuple, snap.get('matrix_dims', [])))),
              'eigh', snap.get('eigh_calls'), 'maxenditer', round(max(snap.get('enditer_seconds', [0]) or [0]), 2), 'n_data', r.get('n_data'), 'n_cells', r.get('n_cells'), f'{time.time()-t:.1f}s', flush=True)
