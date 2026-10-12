"""Run the ORIGINAL judge helper (/tmp/openrct2_original_eval.py) unchanged on chosen scenarios
and budgets, recording the monitor's date fields and whether a DONE line was seen.
Only observation is added: engine stdout lines are teed to a list. Scoring code is untouched.
Usage: python3 driver.py PLUGIN BUDGET_SECONDS SCENARIO [SCENARIO...]"""
import importlib.util, json, re, sys, time
spec = importlib.util.spec_from_file_location("orig", "/tmp/openrct2_original_eval.py")
orig = importlib.util.module_from_spec(spec); spec.loader.exec_module(orig)

seen = []
_Popen = orig.subprocess.Popen
class Tee:
    def __init__(self, f): self.f = f
    def fileno(self): return self.f.fileno()
    def readline(self):
        l = self.f.readline()
        if "__SEBENCH_MONITOR__" in l: seen.append((time.time(), l.strip()))
        return l
    def __getattr__(self, k): return getattr(self.f, k)
def Popen(*a, **k):
    p = _Popen(*a, **k); p.stdout = Tee(p.stdout); return p
orig.subprocess.Popen = Popen

DAYS = [31, 30, 31, 30, 31, 31, 30, 31]  # OpenRCT2 months March..October
def ordinal(y, m, d): return (y - 1) * 245 + sum(DAYS[:m]) + (d - 1)

plugin, budget, scen = sys.argv[1], int(sys.argv[2]), sys.argv[3:]
print("validate_plugin violations:", orig.validate_plugin(plugin))
norms = []
for s in scen:
    seen.clear(); t0 = time.time()
    metrics = orig.run_scenario("/home/workspace/openrct2/scenarios/" + s, plugin, budget)
    wall = time.time() - t0
    norm, reason = orig.score_scenario(s, metrics); norms.append(norm)
    kinds = [re.search(r":(SCORE|DONE):", l).group(1) for _, l in seen]
    dates = [tuple(int(x) for x in re.search(r":date=(\d+),(\d+),(\d+)", l).groups()) for _, l in seen]
    vals = [int(re.search(r":value=(-?\d+)", l).group(1)) for _, l in seen]
    o = {"scenario": s, "budget_s": budget, "wall_s": round(wall, 1), "samples": len(seen),
         "done_seen": "DONE" in kinds, "first_date": dates[0] if dates else None,
         "last_date": dates[-1] if dates else None,
         "game_days_elapsed": (ordinal(*dates[-1]) - ordinal(*dates[0])) if dates else None,
         "first_value": vals[0] if vals else None, "last_value": vals[-1] if vals else None,
         "min_value": min(vals) if vals else None, "max_value": max(vals) if vals else None,
         "metrics": metrics, "norm": norm, "reason": reason}
    if dates and len(seen) > 1:
        span = seen[-1][0] - seen[0][0]
        o["game_days_per_wall_s"] = round(o["game_days_elapsed"] / span, 3) if span > 0 else None
    # value trajectory every ~10 samples
    o["trajectory"] = [(round(seen[i][0] - t0, 1), dates[i], vals[i]) for i in range(0, len(seen), max(1, len(seen)//12))]
    print(json.dumps(o))
print("average_normalized:", sum(norms) / len(norms))
