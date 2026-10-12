#!/usr/bin/env python3
"""Write small hand-made instance/solution pairs (stdlib only).

Each witness is <name>.instance.json + <name>.solution.json in the output dir.
Coordinates are small integers, rotation 0: no floating-point tolerance is involved.
"""
import json, sys
from pathlib import Path

out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
SQ = [[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]]
RECT_HALF = [[0, 0], [10, 0], [10, 5], [0, 5], [0, 0]]
TRI = [[0, 0], [10, 0], [5, 10], [0, 0]]
DIAMOND = [[5, 0], [10, 5], [5, 10], [0, 5], [5, 0]]

def item(i, poly, demand=1):
    return {"id": i, "demand": demand, "allowed_orientations": [0.0],
            "shape": {"type": "simple_polygon", "data": poly}}

def pl(i, x, y, r=0.0):
    return {"item_id": i, "transformation": {"rotation": r, "translation": [x, y]}}

W = {
  # name: (items, placements, expectation-under-contract)
  "valid_adjacent_squares": ([item(0, SQ, 2)], [pl(0, 0, 0), pl(0, 10, 0)], "legal edge contact"),
  "coincident_squares": ([item(0, SQ, 2)], [pl(0, 0, 0), pl(0, 0, 0)], "full overlap"),
  "half_slid_squares": ([item(0, SQ, 2)], [pl(0, 0, 0), pl(0, 5, 0)], "50% overlap, shared horizontal edges"),
  "rect_inside_square": ([item(0, SQ), item(1, RECT_HALF)], [pl(0, 0, 0), pl(1, 0, 0)], "containment, area 50"),
  "triangle_inside_square": ([item(0, SQ), item(1, TRI)], [pl(0, 0, 0), pl(1, 0, 0)], "containment, area 50"),
  "diamond_inside_square": ([item(0, SQ), item(1, DIAMOND)], [pl(0, 0, 0), pl(1, 0, 0)], "containment, area 50, no shared edge"),
  "diag_shift_squares": ([item(0, SQ, 2)], [pl(0, 0, 0), pl(0, 5, 5)], "proper crossing, area 25 (control: must reject)"),
  "tiny_overlap_1e-6": ([item(0, SQ, 2)], [pl(0, 0, 0), pl(0, 10 - 1e-6, 0)], "1e-5 area, tolerance scale"),
}
for name, (items, placed, note) in W.items():
    inst = {"name": name, "items": items, "strip_height": 20.0}
    width = max(x + 10 for x in [p["transformation"]["translation"][0] for p in placed])
    sol = {"solution": {"strip_width": width, "layout": {"placed_items": placed}}, "note": note}
    (out / f"{name}.instance.json").write_text(json.dumps(inst))
    (out / f"{name}.solution.json").write_text(json.dumps(sol))
print("wrote", len(W), "witnesses to", out)
