#!/usr/bin/env python3
"""Pairwise intersection area of the two placed items in each witness (shapely),
plus the exact closed-form area for these integer, rotation-0 witnesses."""
import json, sys
from pathlib import Path
from shapely.geometry import Polygon
from shapely.affinity import translate
EXPECTED = {"valid_adjacent_squares": 0, "coincident_squares": 100, "half_slid_squares": 50,
            "rect_inside_square": 50, "triangle_inside_square": 50, "diamond_inside_square": 50,
            "diag_shift_squares": 25, "tiny_overlap_1e-6": 1e-5}
d = Path(sys.argv[1])
for inst in sorted(d.glob("*.instance.json")):
    name = inst.name[:-len(".instance.json")]
    I = json.loads(inst.read_text()); S = json.loads((d / f"{name}.solution.json").read_text())
    shapes = {it["id"]: Polygon(it["shape"]["data"]) for it in I["items"]}
    P = [translate(shapes[p["item_id"]], *p["transformation"]["translation"]) for p in S["solution"]["layout"]["placed_items"]]
    print(f"{name:26s} shapely={P[0].intersection(P[1]).area:.9g} closed_form={EXPECTED[name]}")
