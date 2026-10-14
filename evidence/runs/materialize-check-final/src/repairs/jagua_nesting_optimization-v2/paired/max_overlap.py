"""Largest pairwise relative overlap (area / smaller item area) in a solution, using v2 overlap_area.
Usage: python3 max_overlap.py <v2 evaluate.py> <instance.json> <solution.json>"""
import importlib.util, json, sys
s = importlib.util.spec_from_file_location("V2", sys.argv[1]); V2 = importlib.util.module_from_spec(s); sys.modules["V2"] = V2; s.loader.exec_module(V2)
inst, sol = json.load(open(sys.argv[2])), json.load(open(sys.argv[3]))
shp = {int(i["id"]): V2.normalize_shape(i["shape"]) for i in inst["items"]}
P = []
for p in sol["solution"]["layout"]["placed_items"]:
    t = p["transformation"]; P.append(V2.rotate_translate(shp[int(p["item_id"])], float(t["rotation"]), [float(v) for v in t["translation"]]))
B = [V2.polygon_bbox(p) for p in P]; worst = 0.0; pairs = 0
for i in range(len(P)):
    for j in range(i + 1, len(P)):
        if V2.bboxes_may_overlap(B[i], B[j]):
            pairs += 1
            r = V2.overlap_area(P[i], P[j]) / min(abs(V2.polygon_area(P[i])), abs(V2.polygon_area(P[j])))
            worst = max(worst, r)
print(f"items={len(P)} bbox_pairs={pairs} max_relative_overlap={worst:.3g} (v2 tolerance {V2.OVERLAP_AREA_REL_TOL})")
