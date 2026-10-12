import sys, json
from pathlib import Path
src = Path(sys.argv[1]).read_text()
pre, post = src.split("rng = np.random.default_rng(1); best = None")
sys.argv = [sys.argv[1], sys.argv[2], sys.argv[3]]
ns = {"__file__": sys.argv[0]}
exec(pre, ns)
np = ns["np"]; truth = json.load(open(Path(sys.argv[1]).parent / "x.json")) if False else json.load(open(Path(ns["root"]) / "opt/borden_scoring/hidden_true_region_source.json"))
p0 = np.array([truth[k] for k in ns["NAMES"]])
print("truth public RMS", float(np.sqrt(np.mean(ns["resid"](p0)**2))))
ns["best"] = ns["least_squares"](ns["resid"], p0, bounds=(ns["lo"], ns["hi"]), x_scale=(ns["hi"]-ns["lo"]), max_nfev=400)
post = post.split("print(\"judge-convention fit:\"", 1)[1]
exec("print(\"judge-convention fit:\"" + post.replace("judge_conv_fit", "judge_conv_truthstart").replace('"judge_conv_fit_params.json"', '"truthstart_params.json"'), ns)
