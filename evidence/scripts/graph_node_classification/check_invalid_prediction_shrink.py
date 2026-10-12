"""Side observation (not the NaN-confidence claim): non-integer prediction values are
silently dropped by _to_int_labels, then y_true is truncated to the shorter length.
Usage: python3 -I check_invalid_prediction_shrink.py /path/to/original/verifier.py"""
import importlib.util, sys
spec = importlib.util.spec_from_file_location("v", sys.argv[1]); V = importlib.util.module_from_spec(spec); spec.loader.exec_module(V)
gt = {str(i): i % 5 for i in range(1000)}            # 1000 test nodes, 5 classes
# honest all-wrong-ish baseline: predict class 0 everywhere
honest = {k: 0 for k in gt}
print("honest constant-0:", V.evaluate(honest, gt, {k: 0.2 for k in gt}))
# shrink: correct label for the first node, 'x' (non-int) for all others -> only node '0' scored
shrink = {k: ("x" if k != "0" else gt["0"]) for k in gt}
print("first correct, rest non-int:", V.evaluate(shrink, gt, {k: 1.0 for k in gt}))
print("prediction count seen by runner coverage check:", len(shrink), "of", len(gt))
