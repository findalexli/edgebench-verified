"""Honest v2 solver: uses ONLY the files shipped in the v2 work directory
(forward_model.py, public_problem_config.json, public_monitoring_data.csv).
Wraps the shipped functions into a row-vectorised predictor (checked equal to the
shipped simulate_from_answer), then runs the same multi-start bounded least squares
(80 starts, seed 1, log1p residuals on detected rows, hinge on censored rows) as the
review's judge_convention_solver_check.py, and writes answer.json.
Usage (inside the v2 work image): python v2_solver.py <work_dir> <out_answer.json>
"""
import json, sys, time
from pathlib import Path
from multiprocessing import Pool
import numpy as np, pandas as pd
from scipy.optimize import least_squares
WD = Path(sys.argv[1]); sys.path.insert(0, str(WD))
import forward_model as fm
cfg = json.load(open(WD / "public_problem_config.json"))
H = cfg["hydrogeological_parameters"]; B = cfg["source_search_bounds_for_agent"]
pub = pd.read_csv(WD / "public_monitoring_data.csv")
X, Y, Z, T = (pub[k].to_numpy(float) for k in ("x", "y", "z", "time_days"))
obs = np.maximum(pub["concentration_observed_mg_L"].to_numpy(float), 0)
det = pub["above_detection_limit"].astype(str).eq("True").to_numpy()
dl = pub["detection_limit_mg_L"].to_numpy(float)
NAMES = ["x_center", "y_center", "z_center", "half_length_x", "half_length_y", "half_length_z", "C0", "t_start", "duration"]
lo = np.array([B[k + "_min"] for k in NAMES]); hi = np.array([B[k + "_max"] for k in NAMES])

def predict(p, x=X, y=Y, z=Z, t=T):
    src = fm.normalize_region_answer(dict(zip(NAMES, map(float, p))), cfg)
    sub = fm._region_subpoints(src, cfg); offs = fm._release_offsets(src["duration"], cfg)
    n = max(len(sub) * len(offs), 1); tot = np.zeros_like(t)
    for sx, sy, sz in sub:
        for off in offs:
            e = t - (src["t_start"] + float(off)); a = e > 0
            if a.any():
                tot[a] += fm._point_response(src["C0"] / n, x[a], y[a], z[a], e[a], sx, sy, sz, H, cfg)
    return np.maximum(np.nan_to_num(tot, nan=0.0, posinf=0.0, neginf=0.0), 0.0)

def check_wrapper():
    wells = pub.drop_duplicates("well_id")[["well_id", "x", "y", "z"]].reset_index(drop=True)
    rng = np.random.default_rng(7); worst = 0.0
    for _ in range(3):
        p = lo + rng.random(9) * (hi - lo)
        ref = fm.simulate_from_answer(dict(zip(NAMES, p)), wells, sorted(pub.time_days.unique()), cfg)
        m = pub.merge(ref, on=["well_id", "time_days"], suffixes=("", "_r"))
        mine = predict(p, *(m[k].to_numpy(float) for k in ("x", "y", "z", "time_days")))
        r = m["concentration_predicted_mg_L"].to_numpy()
        worst = max(worst, float(np.max(np.abs(mine - r) / np.maximum(np.abs(r), 1e-300))))
    return worst

def resid(p):
    pr = predict(p)
    return np.where(det, np.log1p(pr) - np.log1p(obs), np.log1p(np.maximum(pr - dl, 0) / dl) * 0.1)

def fit(p0):
    r = least_squares(resid, p0, bounds=(lo, hi), x_scale=(hi - lo), max_nfev=400)
    return float(r.cost), r.x.tolist()

if __name__ == "__main__":
    t0 = time.time()
    print("wrapper_vs_simulate_from_answer max_rel_diff", check_wrapper(), flush=True)
    rng = np.random.default_rng(1); starts = [lo + rng.random(9) * (hi - lo) for _ in range(80)]
    with Pool(8) as pool: res = pool.map(fit, starts)
    cost, x = min(res, key=lambda r: r[0])
    print("best", dict(zip(NAMES, np.round(x, 4))), "public_RMS", float(np.sqrt(np.mean(resid(np.array(x)) ** 2))),
          "wall_s", round(time.time() - t0), flush=True)
    a = dict(zip(NAMES, x))
    a.update({"source_type": "rectangular_region", "dimension": 3,
              "transport_model": {"equation_type": "advection_dispersion_reaction",
                                  "governing_equation": "R*dC/dt = div(D grad C) - v dot grad C - lambda*C + source",
                                  "velocity_m_per_day": H["velocity_m_per_day"], "alpha_L_m": H["alpha_L_m"],
                                  "alpha_TH_m": H["alpha_TH_m"], "alpha_TV_m": H["alpha_TV_m"], "porosity": H["porosity"],
                                  "retardation_factor": 1.0, "lambda_per_day": 0.0,
                                  "numerical_approach": "shipped forward_model.py (5x5x1 sub-points, 9 pulses); multi-start bounded least squares"},
              "method": "multi-start bounded least squares on censored log residuals of public monitoring data"})
    Path(sys.argv[2]).write_text(json.dumps(a, indent=2))
