"""Check how the ORIGINAL verifier.py treats out-of-range confidences.

Usage: python3 -I check_confidence_mapping.py /path/to/original/verifier.py

Claim tested: for every confidence vector c (any Python floats, including
NaN, +/-inf, negatives, >1), evaluate(c) == evaluate(legal(c)) where
legal(c) is an in-range vector in [0,1] (NaN->0, <0->0, >1->1).  If true,
an out-of-range confidence can never reach a score unreachable by a
contract-conforming submission.
"""
import importlib.util, math, random, sys, itertools, json

spec = importlib.util.spec_from_file_location("orig_verifier", sys.argv[1])
V = importlib.util.module_from_spec(spec); spec.loader.exec_module(V)

def legal(c):
    if math.isnan(c): return 0.0
    return min(1.0, max(0.0, c))

def ev(gt, pr, conf):
    ids = [str(i) for i in range(len(gt))]
    return V.evaluate({k: p for k, p in zip(ids, pr)}, {k: t for k, t in zip(ids, gt)},
                      {k: c for k, c in zip(ids, conf)})

out = {}
# 1. point probes
gt = [0, 1, 2, 0, 1]; pr = [0, 1, 1, 0, 2]   # 3/5 correct
for name, v in [("nan", float("nan")), ("+inf", float("inf")), ("-inf", float("-inf")),
                ("-0.5", -0.5), ("1.7", 1.7), ("0.0", 0.0), ("1.0", 1.0), ("0.6", 0.6)]:
    out[name] = ev(gt, pr, [v] * 5)["ece"]
print("uniform-confidence ECE probes (accuracy 0.6):", json.dumps(out, indent=1))

# 2. randomized equivalence with in-range image
specials = [float("nan"), float("inf"), float("-inf"), -1e9, -0.3, 1.3, 1e9]
random.seed(0)
mism = 0; trials = 20000
for _ in range(trials):
    n = random.randint(1, 30)
    g = [random.randrange(5) for _ in range(n)]
    p = [random.randrange(5) for _ in range(n)]
    c = [random.choice(specials) if random.random() < 0.4 else random.random() for _ in range(n)]
    if ev(g, p, c) != ev(g, p, [legal(x) for x in c]):
        mism += 1
print(f"random trials={trials} mismatches between raw and in-range image: {mism}")

# 3. exhaustive tiny grid: best ECE over out-of-range values vs best over legal grid
grid_legal = [i / 20 for i in range(21)]
grid_bad = [float("nan"), float("inf"), float("-inf"), -0.5, 1.5]
worse = 0; cases = 0
for n in (1, 2, 3):
    for g in itertools.product(range(2), repeat=n):
        for p in itertools.product(range(2), repeat=n):
            best_legal = min(ev(g, p, c)["one_minus_ece"] * -1 for c in itertools.product(grid_legal, repeat=n))
            best_any = min(ev(g, p, c)["one_minus_ece"] * -1 for c in itertools.product(grid_legal + grid_bad, repeat=n))
            cases += 1
            if best_any < best_legal - 1e-15: worse += 1
print(f"exhaustive n<=3 binary cases={cases}: cases where out-of-range beats best legal grid value: {worse}")

# 4. classification metrics independent of confidences
m1 = ev(gt, pr, [0.6] * 5); m2 = ev(gt, pr, [float("nan")] * 5)
print("non-ECE metrics identical:", all(m1[k] == m2[k] for k in ("micro_f1", "macro_f1", "balanced_accuracy")))
