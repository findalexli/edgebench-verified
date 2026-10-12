"""Do the textbook solver's OWN predictions match the hidden labels?
(separates 'wrong physics/ill-posed' from 'right predictions, wrong parameter convention')
Usage: python3 textbook_own_prediction.py <judge_root> <textbook_out_dir>"""
import json, sys, runpy
from pathlib import Path
import numpy as np, pandas as pd
root = Path(sys.argv[1]); od = Path(sys.argv[2])
sys.argv = [sys.argv[0], str(root), str(od / "_scratch")]
src = Path(__file__).with_name("textbook_solver_check.py").read_text()
ns = {}
exec(src.split("rng = np.random.default_rng(0)")[0], ns)   # defs + data only
textbook = ns["textbook"]; NAMES = ns["NAMES"]
fit = json.load(open(od / "summary.json"))["fit"]; p = np.array([fit[k] for k in NAMES])
truth = json.load(open(root / "opt/borden_scoring/hidden_true_region_source.json")); pt = np.array([truth[k] for k in NAMES])
h = pd.read_csv(root / "opt/borden_scoring/hidden_monitoring_data.csv")
c = h["concentration_clean_mg_L"].to_numpy(float)
for name, pp in [("textbook_fit", p), ("textbook_at_truth", pt)]:
    pr = textbook(pp, *(h[k].to_numpy(float) for k in ("x", "y", "z", "time_days")))
    for g in sorted(h.eval_split.unique()):
        m = (h.eval_split == g).to_numpy()
        rr = np.sqrt(np.mean((pr[m] - c[m]) ** 2)) / np.mean(np.abs(c[m]))
        lr = np.sqrt(np.mean((np.log1p(pr[m]) - np.log1p(c[m])) ** 2))
        print(f"{name:18s} {g:14s} n={m.sum():3d} rRMSE={rr:.3f} log_rmse={lr:.4f} mean_label={c[m].mean():.4f} mean_pred={pr[m].mean():.4f}")
