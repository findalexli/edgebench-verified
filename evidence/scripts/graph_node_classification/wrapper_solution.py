"""Wrapper submission: the image's own baseline (solution_template.py) with its
confidences post-processed according to env CONF_MODE:
  orig  - unchanged baseline confidences (in [0,1])
  nan   - every confidence replaced by float('nan')
  zero  - every confidence replaced by 0.0 (legal value)
  big   - every confidence replaced by 7.5 (out of range, >1)
  one   - every confidence replaced by 1.0 (legal value)
  neg   - every confidence replaced by -3.0 (out of range, <0)
  inf   - every confidence replaced by float('inf')
  calib - every confidence replaced by env CONF_CONST (legal constant)
  shrink - SIDE CHECK: keep the baseline prediction only for the first test node; every other
           prediction value becomes the non-integer string "x" (contract violation); conf 1.0/0.0
"""
import importlib.util, os
from pathlib import Path

_p = Path(__file__).resolve().parent / "solution_template.py"
_spec = importlib.util.spec_from_file_location("_baseline_template", _p)
_m = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_m)

_MAP = {"nan": float("nan"), "zero": 0.0, "big": 7.5, "one": 1.0, "neg": -3.0, "inf": float("inf")}

class Solution:
    def __init__(self):
        self._inner = _m.Solution()

    def solve(self, input_data):
        out = self._inner.solve(input_data)
        mode = os.environ.get("CONF_MODE", "orig")
        if mode == "orig":
            return out
        if mode == "shrink":
            first = str(input_data["test_nodes"][0])
            preds = {k: (v if k == first else "x") for k, v in out["predictions"].items()}
            return {"predictions": preds, "confidences": {k: 1.0 for k in preds}}
        v = float(os.environ.get("CONF_CONST", "0.5")) if mode == "calib" else _MAP[mode]
        out["confidences"] = {k: v for k in out["predictions"]}
        return out
