"""Differential check of GraphNodeValidation.lean against the REAL v1/v2 verifier.evaluate.
Usage (image Python 3.11, no network):  python3 -I diff_check.py <v1 verifier.py sha 044cd50e...> <v2 verifier.py sha 32caddb1...>
The verifier files are image-derived and not stored in Git (materialize.sh regenerates them).
For random prediction dicts over the value classes of the model it checks
  V1: v2 evaluate succeeds  <=>  every gt node has a value the model's `strict` accepts;
  V2: if v2 succeeds and every string value satisfies StrOK, v1 returns identical metrics;
and counts the StrOK exceptions (strings padded with U+001C..U+001F) separately."""
import importlib.util, math, random, sys
from decimal import Decimal
from fractions import Fraction

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m); return m
v1, v2 = load("v1", sys.argv[1]), load("v2", sys.argv[2])

def py_int(f, x):
    try: return f(x)
    except Exception: return None

def model_tag(v):                      # PyVal constructor of the Lean model
    if isinstance(v, bool): return "bool"
    if isinstance(v, float):
        if v != v: return "nan"
        if math.isinf(v): return "inf"
        return "fint" if v.is_integer() else "fnon"
    if isinstance(v, int): return "int"
    if isinstance(v, str): return ("str", py_int(int, v), py_int(lambda s: int(s.strip()), v))
    if hasattr(type(v), "__index__"): return "idx"
    if hasattr(type(v), "__int__"): return "intOnly"
    return "other"

def strict_ok(tag):                    # Lean `strict v).isSome`
    return tag in ("int", "fint", "idx") or (isinstance(tag, tuple) and tag[2] is not None)

def str_ok(tag):
    return not isinstance(tag, tuple) or tag[1] == tag[2]

POOL = [0, 1, 2, 3, 4, -1, 7, True, False, 2.0, 3.0, 2.5, -0.5, float("nan"), float("inf"),
        "1", " 2 ", "+3", "1_0", "x", "", "2.0", "\u0663", "\x1c1", "1\x1f", "\u20031", None, [1],
        Decimal(3), Fraction(2, 1), 4.0]
rng = random.Random(20261012)
n_acc = n_rej = n_same = n_strbad = 0
for trial in range(20000):
    k = rng.randint(1, 6)
    gt = {str(i): rng.randint(0, 4) for i in range(k)}
    pred = {}
    for nid in gt:
        r = rng.random()
        if r < 0.08: continue                                   # missing node
        pred[nid] = rng.randint(0, 4) if r < 0.6 else rng.choice(POOL)
    if rng.random() < 0.1: pred["extra"] = 1
    conf = {nid: rng.choice([0.1, 0.5, 0.9, 1.0]) for nid in gt if rng.random() < 0.7}
    tags = {nid: model_tag(v) for nid, v in pred.items()}
    expect = all(nid in pred and strict_ok(tags[nid]) for nid in gt)
    try: r2 = v2.evaluate(predictions=pred, ground_truth=gt, confidences=conf); ok = True
    except ValueError: ok = False
    assert ok == expect, (gt, pred)
    if not ok: n_rej += 1; continue
    n_acc += 1
    if not all(str_ok(tags[nid]) for nid in gt): n_strbad += 1; continue
    r1 = v1.evaluate(predictions=pred, ground_truth=gt, confidences=conf)
    assert r1 == r2, (gt, pred, r1, r2)
    n_same += 1
print(f"python {sys.version.split()[0]}: 20000 trials, v2 accepted {n_acc}, rejected {n_rej}; "
      f"claim V1 (acceptance = model) held on all; claim V2 identical metrics on {n_same}/{n_acc - n_strbad} StrOK-accepted; "
      f"{n_strbad} accepted with a U+001C..U+001F-padded string (outside V2)")
pred = {"0": "\x1c0", "1": 1}; gt = {"0": 0, "1": 1}
print("separator example: v1", v1.evaluate(pred, gt, {}), "\n                   v2", v2.evaluate(pred, gt, {}))
