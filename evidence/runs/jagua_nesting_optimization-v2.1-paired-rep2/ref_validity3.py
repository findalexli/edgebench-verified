"""v2.1 revision: run the frozen reference lbf on the 16 scored instances (scorer seeds) and validate
three forms of each output with v1 (in-image), v2 (superseded) and v2.1 validate_solution:
  ref     the reference output as written;
  f32deg  every angle replaced by its f32 radians converted to degrees in f64 (90 -> 90.0000025);
  wrong   every angle + 0.01 deg (10 x the v2.1 tolerance).
Saves the reference solutions to /o."""
import sys, time, json, math, struct, tempfile, os
sys.path.insert(0, "/home/workspace/jagua_task_scorer")
import importlib.util
from pathlib import Path
import evaluate as V1
def load(p, n):
    s = importlib.util.spec_from_file_location(n, p); m = importlib.util.module_from_spec(s); sys.modules[n] = m; s.loader.exec_module(m); return m
EV = {"v1": V1,
      "v2": load("/job/v2ctx/files/home/workspace/jagua_task_scorer/evaluate.py", "V2"),
      "v2.1": load("/job/v21ctx/files/home/workspace/jagua_task_scorer/evaluate.py", "V21")}
def f32(x): return struct.unpack("f", struct.pack("f", x))[0]
RAD32 = f32(f32(math.pi) / f32(180.0))                       # Rust f32::to_radians constant
FORMS = {"ref": lambda r: r,
         "f32deg": lambda r: math.degrees(f32(f32(r) * RAD32)),
         "wrong": lambda r: r + 0.01}
work = Path("/tmp/w"); work.mkdir(exist_ok=True)
for n in sys.argv[1].split(","):
    inst = work / f"{n}.json"; inst.write_text(Path(f"/home/workspace/jagua-rs-ref/assets/{n}.json").read_text())
    cfg = work / f"{n}_config.json"; V1.write_config(cfg, seed=10_000 + V1.HIDDEN_CASE_FILES.index(n + ".json") * 17, n_samples=900)
    ok, reason, sol, rt = V1.run_lbf(Path("/home/workspace/jagua-rs-ref"), inst, cfg, work / f"ref_{n}", 20)
    if not ok: print(n, "lbf failed", reason); continue
    Path(f"/o/{n}.sol.json").write_text(sol.read_text())
    base = json.loads(sol.read_text())
    for form, fn in FORMS.items():
        s = json.loads(json.dumps(base))
        for p in s["solution"]["layout"]["placed_items"]:
            p["transformation"]["rotation"] = fn(float(p["transformation"]["rotation"]))
        tp = work / f"{n}.{form}.json"; tp.write_text(json.dumps(s))
        dev = max(abs((float(p["transformation"]["rotation"]) - float(q["transformation"]["rotation"]) + 180) % 360 - 180)
                  for p, q in zip(s["solution"]["layout"]["placed_items"], base["solution"]["layout"]["placed_items"]))
        out = []
        for k, E in EV.items():
            t = time.time(); r = E.validate_solution(inst, tp); out.append(f"{k}={r[0]}/{r[1]}/{r[2]} ({time.time() - t:.2f}s)")
        print(n, form, f"max_angle_change={dev:.3e}", *out, flush=True)
