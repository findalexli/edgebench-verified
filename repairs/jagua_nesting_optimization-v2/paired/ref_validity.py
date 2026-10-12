"""Run the frozen reference lbf on hidden instances (scorer seeds) and validate each output with v1 and v2 validate_solution; saves solutions to /o."""
import sys, time, json
sys.path.insert(0, "/home/workspace/jagua_task_scorer")
import importlib.util
from pathlib import Path
import evaluate as V1
s = importlib.util.spec_from_file_location("V2", "/job/v2ctx/files/home/workspace/jagua_task_scorer/evaluate.py"); V2 = importlib.util.module_from_spec(s); sys.modules["V2"] = V2; s.loader.exec_module(V2)
work = Path("/tmp/w"); work.mkdir(exist_ok=True)
names = sys.argv[1].split(",")
for idx, n in enumerate(names):
    inst = work / f"{n}.json"; inst.write_text(Path(f"/home/workspace/jagua-rs-ref/assets/{n}.json").read_text())
    cfg = work / f"{n}_config.json"; V1.write_config(cfg, seed=10_000 + V1.HIDDEN_CASE_FILES.index(n + ".json") * 17, n_samples=900)
    ok, reason, sol, rt = V1.run_lbf(Path("/home/workspace/jagua-rs-ref"), inst, cfg, work / f"ref_{n}", 20)
    if not ok: print(n, "lbf failed", reason); continue
    Path(f"/o/{n}.sol.json").write_text(sol.read_text())
    t = time.time(); r1 = V1.validate_solution(inst, sol); t1 = time.time() - t
    t = time.time(); r2 = V2.validate_solution(inst, sol); t2 = time.time() - t
    rots = sorted({round(p["transformation"]["rotation"], 9) for p in json.loads(sol.read_text())["solution"]["layout"]["placed_items"]})
    print(n, f"lbf={rt:.1f}s", "v1", r1, f"{t1:.2f}s", "v2", r2, f"{t2:.2f}s", "rots", rots, flush=True)
