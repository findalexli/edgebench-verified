"""Run inside the judge image (cwd = task dir). Writes final_result.txt.
mode: identity | search | badcost | dup
Uses ONLY the public black-box function (root .so), counting calls."""
import random, sys, time
sys.path.insert(0, ".")
from cost_complex_cy import cost_complex_with_builtin_data as f
mode = sys.argv[1]; M = 1000; n = 0
def c(p):
    global n; n += 1; return f(p, m=M, seed=1)
p = list(range(1, M + 1))
best = c(p)
if mode == "search":
    random.seed(0); t0 = time.time(); budget = float(sys.argv[2]) if len(sys.argv) > 2 else 20
    while time.time() - t0 < budget:
        i, j = random.sample(range(M), 2)
        p[i], p[j] = p[j], p[i]
        v = c(p)
        if v < best: best = v
        else: p[i], p[j] = p[j], p[i]
cost = best
if mode == "badcost": cost = best * 0.5
if mode == "dup": p = p[:]; p[1] = p[0]
open("final_result.txt", "w").write(
    "final_pai=" + ",".join(map(str, p)) + f"\nfinal_cost={cost!r}\nfinal_num={n}\n")
print("mode", mode, "cost", cost, "num", n)
