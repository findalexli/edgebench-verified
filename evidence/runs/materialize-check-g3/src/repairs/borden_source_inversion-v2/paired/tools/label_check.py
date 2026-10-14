"""Run in the (unchanged) judge image: does the SHIPPED forward_model.py reproduce the
hidden clean labels from the hidden true source? Also diff its outputs against the
judge's own hidden_forward_model on the same inputs.
Usage: python label_check.py <shipped forward_model dir> <judge case dir> <judge scoring dir>"""
import json, sys, importlib.util
import numpy as np, pandas as pd
def load(name, path):
    s = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
ship = load("ship", sys.argv[1] + "/forward_model.py"); judge = load("judge", sys.argv[3] + "/hidden_forward_model.py")
case, sc = sys.argv[2], sys.argv[3]
cfg = json.load(open(case + "/public_problem_config.json")); truth = json.load(open(sc + "/hidden_true_region_source.json"))
hid = pd.read_csv(sc + "/hidden_monitoring_data.csv"); pubc = pd.read_csv(case + "/scoring/public_monitoring_data_with_clean.csv")
lab = pd.concat([hid, pubc], ignore_index=True)
worst = {"ship_vs_label": 0.0, "ship_vs_judge": 0.0}; n = 0
for wid, g in lab.groupby("well_id"):
    w = g.iloc[:1][["well_id", "x", "y", "z"]]
    ts = g.time_days.to_numpy(float)
    a = ship.simulate_from_answer(truth, w, ts, cfg)["concentration_predicted_mg_L"].to_numpy()
    b = judge.simulate_from_answer(truth, w, ts, cfg)["concentration_predicted_mg_L"].to_numpy()
    c = g.concentration_clean_mg_L.to_numpy(float); n += len(c)
    sel = c > 1e-12
    worst["ship_vs_label"] = max(worst["ship_vs_label"], float(np.max(np.abs(a[sel] - c[sel]) / c[sel])) if sel.any() else 0.0)
    worst["ship_vs_judge"] = max(worst["ship_vs_judge"], float(np.max(np.abs(a - b))))
print(json.dumps({"rows": n, **worst}))
