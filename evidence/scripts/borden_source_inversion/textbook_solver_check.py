"""Honest-solver experiment for borden_source_inversion.

Usage: python3 textbook_solver_check.py <judge_root> <out_dir>
  judge_root contains opt/borden_scoring (evaluate.py, hidden labels) and
  home/workspace/borden_inverse (public task files).

1. Own textbook ADE forward model, built only from the public docs:
   continuous injection of fluid at concentration C0 [mg/L] and rate q [m3/d]
   (mass rate C0*q*1000 mg/d) into a uniform box, dissolved in pore water
   (divide by porosity), Gaussian/erf kernels, mg/m3 -> mg/L (/1000).
2. Fit all 9 source parameters (inside the public bounds) to the public noisy,
   censored observations only.
3. Score the fitted answer with the ORIGINAL evaluate.py (subprocess, temp copy
   of the public dir).  Also score counterfactuals that isolate each convention
   difference.
"""
import json, math, shutil, subprocess, sys, tempfile
from pathlib import Path
import numpy as np, pandas as pd
from scipy.optimize import least_squares
from scipy.special import erf

root = Path(sys.argv[1]); out = Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
SC = root / "opt/borden_scoring"; WS = root / "home/workspace/borden_inverse"
cfg = json.load(open(WS / "public_problem_config.json"))
H = cfg["hydrogeological_parameters"]; B = cfg["source_search_bounds_for_agent"]
v, n, q = H["velocity_m_per_day"], H["porosity"], H["q_source_m3_per_day"]
DL, DT, DV = H["alpha_L_m"] * v, H["alpha_TH_m"] * v, H["alpha_TV_m"] * v
pub = pd.read_csv(WS / "public_monitoring_data.csv")
X, Y, Z, T = (pub[k].to_numpy(float) for k in ("x", "y", "z", "time_days"))
obs = np.maximum(pub["concentration_observed_mg_L"].to_numpy(float), 0)
det = pub["above_detection_limit"].astype(str).eq("True").to_numpy()
dl = pub["detection_limit_mg_L"].to_numpy(float)
NAMES = ["x_center", "y_center", "z_center", "half_length_x", "half_length_y", "half_length_z", "C0", "t_start", "duration"]
lo = np.array([B[k + "_min"] for k in NAMES]); hi = np.array([B[k + "_max"] for k in NAMES])

def boxk(u, c, h, D, tt):
    s = np.sqrt(4 * D * tt)
    return 0.5 * (erf((u - c + h) / s) - erf((u - c - h) / s)) / (2 * h)

def textbook(p, x, y, z, t, nst=200):
    xc, yc, zc, hx, hy, hz, C0, ts, dur = p
    rate = C0 * q * 1000.0           # mg/day
    dt = dur / nst
    tau = ts + (np.arange(nst) + 0.5) * dt
    tt = t[:, None] - tau[None, :]
    act = tt > 0; tt = np.where(act, tt, 1.0)
    g = (boxk(x[:, None] - v * tt, xc, hx, DL, tt) * boxk(y[:, None], yc, hy, DT, tt)
         * boxk(z[:, None], zc, hz, DV, tt))
    cm3 = (rate * dt / n * g * act).sum(1)   # mg/m3
    return cm3 / 1000.0                      # mg/L

def resid(p):
    pr = np.maximum(textbook(p, X, Y, Z, T), 0)
    r = np.where(det, np.log1p(pr) - np.log1p(obs), np.log1p(np.maximum(pr - dl, 0) / dl) * 0.1)
    return r

rng = np.random.default_rng(0)
best = None
for k in range(60):
    p0 = lo + rng.random(9) * (hi - lo)
    try:
        r = least_squares(resid, p0, bounds=(lo, hi), x_scale=(hi - lo), max_nfev=400)
    except Exception:
        continue
    if best is None or r.cost < best.cost:
        best = r
pfit = best.x
pubrmse = math.sqrt(np.mean(resid(pfit) ** 2))
truth = json.load(open(SC / "hidden_true_region_source.json"))
ptrue = np.array([truth[k] for k in NAMES])

def answer_of(p, note):
    a = {k: float(val) for k, val in zip(NAMES, p)}
    a.update({"source_type": "rectangular_region", "dimension": 3,
              "transport_model": {"equation_type": "advection_dispersion_reaction",
                                  "governing_equation": "R*dC/dt = div(D grad C) - v dot grad C - lambda*C + source",
                                  "velocity_m_per_day": v, "alpha_L_m": H["alpha_L_m"], "alpha_TH_m": H["alpha_TH_m"],
                                  "alpha_TV_m": H["alpha_TV_m"], "porosity": n, "retardation_factor": 1.0,
                                  "lambda_per_day": 0.0,
                                  "numerical_approach": "analytical erf box-source, continuous release, superposition in time; least squares"},
              "method": "multi-start bounded least squares on censored log residuals of public monitoring data: " + note})
    return a

def score(ans, tag):
    d = Path(tempfile.mkdtemp(prefix="bsi_"))
    for f in WS.iterdir():
        if f.is_file():
            shutil.copy(f, d / f.name)
    (d / "answer.json").write_text(json.dumps(ans, indent=2))
    r = subprocess.run([sys.executable, str(SC / "evaluate.py"), "--submission_dir", str(d), "--case_dir", str(d),
                        "--scoring_dir", str(SC), "--output", str(d / "score.json")], capture_output=True, text=True, timeout=600)
    s = json.load(open(d / "score.json"))
    (out / f"answer_{tag}.json").write_text(json.dumps(ans, indent=2))
    (out / f"score_{tag}.json").write_text(json.dumps(s, indent=2, default=str))
    shutil.rmtree(d)
    m = s.get("metrics", {})
    return dict(tag=tag, total=s["total_score"], raw=s["raw_total_before_cap"], cap=s["cap_reason"],
                hidden_rRMSE=m.get("hidden_well", {}).get("rRMSE"), future_rRMSE=m.get("future_public", {}).get("rRMSE"))

rows = []
print("textbook fit params:", dict(zip(NAMES, np.round(pfit, 4))))
print("truth params      :", dict(zip(NAMES, ptrue)))
print("textbook public censored-log RMS residual: %.4f (cost %.4g)" % (pubrmse, best.cost))
# amplitude factor between textbook and judge at the truth, on public rows with clean>1e-2
cl = pd.read_csv(SC / "public_monitoring_data_with_clean.csv")
m = cl["concentration_clean_mg_L"].to_numpy(float) > 1e-2
ratio = textbook(ptrue, *(cl[k].to_numpy(float)[m] for k in ("x", "y", "z", "time_days"))) / cl["concentration_clean_mg_L"].to_numpy(float)[m]
print("textbook(truth)/judge-label ratio on public rows clean>1e-2: n=%d min=%.3g median=%.3g max=%.3g; predicted factor dur/(1000 n)=%.3g"
      % (m.sum(), ratio.min(), np.median(ratio), ratio.max(), truth["duration"] / (1000 * n)))
rows.append(score(answer_of(ptrue, "truth"), "truth"))
rows.append(score(answer_of(pfit, "textbook fit"), "textbook_fit"))
p2 = pfit.copy(); p2[6] = min(pfit[6] * pfit[8] / (1000 * n), hi[6]); p2[6] = max(p2[6], lo[6])
rows.append(score(answer_of(p2, "textbook fit, C0 rescaled by dur/(1000n)"), "textbook_fit_C0rescaled"))
p3 = p2.copy(); p3[2] = min(pfit[2] + pfit[5], hi[2])  # move judge's source plane (zc-hz) to textbook box center
rows.append(score(answer_of(p3, "C0 rescaled + z shift"), "textbook_fit_C0rescaled_zshift"))
mid = 0.5 * (lo + hi)
rows.append(score(answer_of(mid, "baseline mid-bounds"), "baseline_mid"))
for r in rows:
    print(r)
json.dump({"fit": dict(zip(NAMES, pfit.tolist())), "public_rms": pubrmse, "rows": rows}, open(out / "summary.json", "w"), indent=2)
