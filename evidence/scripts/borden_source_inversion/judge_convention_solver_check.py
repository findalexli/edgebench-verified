"""Counterpart to textbook_solver_check.py: a solver that implements the JUDGE's
convention (own vectorised re-implementation: 5x5x1 sub-points, 9 pulses on
linspace(0,dur,9), pulse mass C0*q*1000/225, no porosity, result read as mg/L)
and fits it to the public noisy/censored data only.  Shows what score an honest
solver who guesses the convention can reach (is >100 reachable?).
Usage: python3 judge_convention_solver_check.py <judge_root> <out_dir>
"""
import json, sys, shutil, subprocess, tempfile
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
root = Path(sys.argv[1]); out = Path(sys.argv[2])
import pandas as pd
WS = root / "home/workspace/borden_inverse"
cfg = json.load(open(WS / "public_problem_config.json"))
H = cfg["hydrogeological_parameters"]; B = cfg["source_search_bounds_for_agent"]
v, q = H["velocity_m_per_day"], H["q_source_m3_per_day"]
DL, DT, DV = H["alpha_L_m"] * v, H["alpha_TH_m"] * v, H["alpha_TV_m"] * v
pub = pd.read_csv(WS / "public_monitoring_data.csv")
X, Y, Z, T = (pub[k].to_numpy(float) for k in ("x", "y", "z", "time_days"))
obs = np.maximum(pub["concentration_observed_mg_L"].to_numpy(float), 0)
det = pub["above_detection_limit"].astype(str).eq("True").to_numpy()
dl = pub["detection_limit_mg_L"].to_numpy(float)
NAMES = ["x_center", "y_center", "z_center", "half_length_x", "half_length_y", "half_length_z", "C0", "t_start", "duration"]
lo = np.array([B[k + "_min"] for k in NAMES]); hi = np.array([B[k + "_max"] for k in NAMES])

def judge_conv(p, x, y, z, t):
    xc, yc, zc, hx, hy, hz, C0, ts, dur = p
    xs = np.linspace(xc - hx, xc + hx, 5); ys = np.linspace(yc - hy, yc + hy, 5); zs = np.array([zc - hz])
    offs = np.linspace(0, max(dur, 1.0), 9)
    m = C0 / 225 * q * 1000
    tot = np.zeros_like(t)
    for off in offs:
        tt = t - (ts + off); act = tt > 0; tt = np.maximum(np.where(act, tt, 1.0), 1e-6)
        den = (4 * np.pi * tt) ** 1.5 * np.sqrt(DL * DT * DV)
        gx = np.exp(-(x[:, None] - xs[None, :] - (v * tt)[:, None]) ** 2 / (4 * DL * tt[:, None])).sum(1)
        gy = np.exp(-(y[:, None] - ys[None, :]) ** 2 / (4 * DT * tt[:, None])).sum(1)
        gz = np.exp(-(z - zs[0]) ** 2 / (4 * DV * tt))
        tot += np.where(act, m / den * gx * gy * gz, 0.0)
    return tot

def resid(p):
    pr = np.maximum(judge_conv(p, X, Y, Z, T), 0)
    return np.where(det, np.log1p(pr) - np.log1p(obs), np.log1p(np.maximum(pr - dl, 0) / dl) * 0.1)

rng = np.random.default_rng(1); best = None
for k in range(80):
    p0 = lo + rng.random(9) * (hi - lo)
    r = least_squares(resid, p0, bounds=(lo, hi), x_scale=(hi - lo), max_nfev=400)
    if best is None or r.cost < best.cost: best = r
print("judge-convention fit:", dict(zip(NAMES, np.round(best.x, 4))), "public RMS", float(np.sqrt(np.mean(resid(best.x)**2))))
json.dump(dict(zip(NAMES, best.x.tolist())), open(out / "judge_conv_fit_params.json", "w"), indent=2)
SC = root / "opt/borden_scoring"
a = {k: float(x) for k, x in zip(NAMES, best.x)}
a.update({"source_type": "rectangular_region", "dimension": 3,
          "transport_model": {"equation_type": "advection_dispersion_reaction",
                              "governing_equation": "R*dC/dt = div(D grad C) - v dot grad C - lambda*C + source",
                              "velocity_m_per_day": v, "alpha_L_m": H["alpha_L_m"], "alpha_TH_m": H["alpha_TH_m"],
                              "alpha_TV_m": H["alpha_TV_m"], "porosity": H["porosity"], "retardation_factor": 1.0,
                              "lambda_per_day": 0.0, "numerical_approach": "superposed point-source ADE pulses over 5x5 sub-points and 9 release times; least squares"},
          "method": "multi-start bounded least squares on censored log residuals of public monitoring data"})
d = Path(tempfile.mkdtemp(prefix="bsj_"))
for f in WS.iterdir():
    if f.is_file(): shutil.copy(f, d / f.name)
(d / "answer.json").write_text(json.dumps(a, indent=2))
subprocess.run([sys.executable, str(SC / "evaluate.py"), "--submission_dir", str(d), "--case_dir", str(d),
                "--scoring_dir", str(SC), "--output", str(d / "score.json")], capture_output=True, text=True, timeout=600)
s = json.load(open(d / "score.json")); shutil.rmtree(d)
(out / "answer_judge_conv_fit.json").write_text(json.dumps(a, indent=2))
(out / "score_judge_conv_fit.json").write_text(json.dumps(s, indent=2, default=str))
m = s.get("metrics", {})
print(dict(tag="judge_conv_fit", total=s["total_score"], raw=s["raw_total_before_cap"], cap=s["cap_reason"],
           hidden_rRMSE=m.get("hidden_well", {}).get("rRMSE"), future_rRMSE=m.get("future_public", {}).get("rRMSE")))
