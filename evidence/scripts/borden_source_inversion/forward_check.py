"""Independent forward-model check for borden_source_inversion (pure Python, no numpy).

Usage: python3 -I forward_check.py <dir containing opt/borden_scoring and home/workspace/borden_inverse>

Own implementation (not the scorer's helper) of:
 (A) the judge's documented superposition convention (5x5x1 sub-points, 9 pulses,
     instantaneous 3D Gaussian, mass C0*q*1000/n_norm per pulse) -> checks whether the
     shipped clean labels are exactly that model evaluated at the hidden true source;
 (B) a physically standard continuous finite-duration release from a uniform box
     (erf in y,z per release time, mass rate = C0*q*1000 / porosity, integrated over
     duration) -> reports how far 'textbook' physics departs from the labels.
"""
import csv, json, math, sys
from pathlib import Path

root = Path(sys.argv[1])
sc = root / "opt/borden_scoring"
ws = root / "home/workspace/borden_inverse"
cfg = json.load(open(ws / "public_problem_config.json"))
true = json.load(open(sc / "hidden_true_region_source.json"))
H = cfg["hydrogeological_parameters"]
v = H["velocity_m_per_day"]
n = H["porosity"]
q = H["q_source_m3_per_day"]
scale = H["fallback_source_scale_factor"]
DL, DT, DV = H["alpha_L_m"] * v, H["alpha_TH_m"] * v, H["alpha_TV_m"] * v
print("v check: K*i/n =", 10.0 * (1.0 / 1200.0) / 0.3, "config v =", v)


def lin(a, b, k):
    return [a] if k == 1 else [a + (b - a) * i / (k - 1) for i in range(k)]


def judge_convention(s, x, y, z, t):
    xs = lin(s["x_center"] - s["half_length_x"], s["x_center"] + s["half_length_x"], 5)
    ys = lin(s["y_center"] - s["half_length_y"], s["y_center"] + s["half_length_y"], 5)
    zs = lin(s["z_center"] - s["half_length_z"], s["z_center"] + s["half_length_z"], 1)
    offs = lin(0.0, max(s["duration"], 1.0), 9)
    m = s["C0"] / (25 * 9) * q * scale
    tot = 0.0
    for off in offs:
        tt = t - (s["t_start"] + off)
        if tt <= 0:
            continue
        tt = max(tt, 1e-6)
        den = (4 * math.pi * tt) ** 1.5 * math.sqrt(DL * DT * DV)
        for sx in xs:
            for sy in ys:
                for sz in zs:
                    e = ((x - sx - v * tt) ** 2 / (4 * DL * tt) + (y - sy) ** 2 / (4 * DT * tt)
                         + (z - sz) ** 2 / (4 * DV * tt))
                    tot += m / den * math.exp(-e)
    return tot


def box(u, h, c, D, tt):
    s = math.sqrt(4 * D * tt)
    return 0.5 * (math.erf((u - c + h) / s) - math.erf((u - c - h) / s)) / (2 * h)


def physical_continuous(s, x, y, z, t, nsteps=400):
    # continuous injection at rate C0*q*1000 (mg/day) spread uniformly over the box volume,
    # dissolved mass in pore water -> divide by porosity. Midpoint rule in release time.
    T = s["duration"]
    dt = T / nsteps
    rate = s["C0"] * q * scale / n
    tot = 0.0
    for k in range(nsteps):
        tau = s["t_start"] + (k + 0.5) * dt
        tt = t - tau
        if tt <= 0:
            continue
        gx = box(x - v * tt, s["half_length_x"], s["x_center"], DL, tt)
        gy = box(y, s["half_length_y"], s["y_center"], DT, tt)
        gz = box(z, s["half_length_z"], s["z_center"], DV, tt)
        tot += rate * dt * gx * gy * gz
    return tot


def rows(p):
    return list(csv.DictReader(open(p)))


labels = rows(sc / "public_monitoring_data_with_clean.csv") + rows(sc / "hidden_monitoring_data.csv")
maxrel = 0.0; maxabs = 0.0; nz_ = 0
ratios = []
for r in labels:
    x, y, z, t = (float(r[k]) for k in ("x", "y", "z", "time_days"))
    c = float(r["concentration_clean_mg_L"])
    a = judge_convention(true, x, y, z, t)
    maxabs = max(maxabs, abs(a - c))
    if c > 1e-3:
        nz_ += 1
        maxrel = max(maxrel, abs(a - c) / c)
        if r["eval_split"] != "x":
            pass
for r in labels[::12]:
    x, y, z, t = (float(r[k]) for k in ("x", "y", "z", "time_days"))
    c = float(r["concentration_clean_mg_L"])
    if c > 1e-2:
        ratios.append(physical_continuous(true, x, y, z, t) / c)
print("labels:", len(labels), "max |judge_conv - clean| =", maxabs, "max rel (clean>1e-3, n=%d) =" % nz_, maxrel)
ratios.sort()
if ratios:
    print("physical-continuous / clean ratio: n=%d min=%.3g median=%.3g max=%.3g" % (
        len(ratios), ratios[0], ratios[len(ratios) // 2], ratios[-1]))
# Mass bookkeeping
M_judge = true["C0"] * q * scale
M_phys = true["C0"] * q * scale * true["duration"] / n
print("judge total injected mass (independent of duration) =", M_judge, "; continuous-release mass/porosity =", M_phys,
      "; ratio =", M_phys / M_judge)
# duration-invariance of total mass: compare with duration doubled, late time far downstream
pub = rows(ws / "public_monitoring_data.csv")
cl = {(r["well_id"], r["time_days"]): r for r in rows(sc / "public_monitoring_data_with_clean.csv")}
same = sum(1 for r in pub if (r["well_id"], r["time_days"]) in cl and
           abs(float(cl[(r["well_id"], r["time_days"])]["concentration_observed_mg_L"]) - float(r["concentration_observed_mg_L"])) < 1e-12)
print("public observed rows:", len(pub), "matching private observed column:", same)
cens = sum(1 for r in pub if r["above_detection_limit"] == "False")
print("public censored rows:", cens, "| hidden splits:",
      {k: sum(1 for r in rows(sc / 'hidden_monitoring_data.csv') if r['eval_split'] == k) for k in
       set(r['eval_split'] for r in rows(sc / 'hidden_monitoring_data.csv'))})
print("public columns:", list(pub[0].keys()))

# ---- Score ceiling check (own re-implementation of evaluate.py arithmetic, true source submitted) ----
res = []
for r in pub:
    x, y, z, t = (float(r[k]) for k in ("x", "y", "z", "time_days"))
    p = max(judge_convention(true, x, y, z, t), 0.0)
    yv = max(float(r["concentration_observed_mg_L"]), 0.0)
    det = float(r["detection_limit_mg_L"])
    if r["above_detection_limit"] == "True":
        res.append(math.log1p(p) - math.log1p(yv))
    else:
        res.append(math.log1p(max(p - det, 0.0) / max(det, 1e-8)))
clr = math.sqrt(sum(e * e for e in res) / len(res))
pub_pts = 10.0 if clr <= 0.035 else (0.0 if clr >= 0.55 else 10.0 * (0.55 - clr) / (0.55 - 0.035))
metric = 5 + 5 + 2 + 2 + 33 + 25 + 10 + 10  # all hidden errors exactly 0
total = 1 + 1 + min(pub_pts, 2.0) + 1 + 2 + metric + 10
print("truth: public censored_log_rmse=%.4f -> public_sanity=%.3f (cap 2); attainable total with truth = %.3f (no clamp to 100)" % (clr, pub_pts, total))
