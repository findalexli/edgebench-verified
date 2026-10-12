"""Normalize paired raw scores under v1 (tasks/treant_forest.json) and v2 (task.json.in) anchors
with the repo's sforge/harness/score_rescale.py. Also recomputes the exact score cap from cases.
Usage: python3 normalize.py <cases_dir> <result_out_dir>"""
import glob, json, os, re, sys
from fractions import Fraction as F
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), *[".."] * 4))
sys.path.insert(0, ROOT)
from sforge.harness.score_rescale import parse_rescale_spec, rescale_score
v1 = parse_rescale_spec(json.load(open(f"{ROOT}/tasks/treant_forest.json"))["judge"]["rescale"])
v2 = parse_rescale_spec(json.load(open(os.path.join(os.path.dirname(__file__), "..", "task.json.in")))["judge"]["rescale"])
cases = sorted(glob.glob(os.path.join(sys.argv[1], "*.txt")))
cap = sum(2 * int(open(c).readline().split()[0]) ** 2 for c in cases)
print(json.dumps({"cases": len(cases), "cap_sum_2N2": cap, "v1_spec": v1.__dict__, "v2_spec": v2.__dict__}))
rows = []
for img in ("v1", "v2"):
    for s in ("baseline", "honest_greedy", "invalid_revealed"):
        t = open(os.path.join(sys.argv[2], f"eval_{img}_{s}.txt")).read()
        st = open(os.path.join(sys.argv[2], f"status_{img}_{s}.txt")).read().strip()
        raw = int(re.search(r"^TOTAL_SCORE (\d+)", t, re.M).group(1))
        ok = re.search(r"^CASES_OK (\d+)", t, re.M).group(1)
        statuses = sorted(set(re.findall(r"^CASE \d+ (\w+)", t, re.M)))
        rows.append(dict(image=img, sub=s, raw=raw, cases_ok=f"{ok}/50", case_statuses=statuses,
                         status=st, v1_norm=rescale_score(v1, raw), v2_norm=rescale_score(v2, raw)))
for r in rows: print(json.dumps(r))
# anchor-endpoint checks
for x in (0, 3418, 5369, cap, 330195):
    print(json.dumps({"raw": x, "v1": rescale_score(v1, x), "v2": rescale_score(v2, x),
                      "v2_exact": str(max(F(0), min(F(100), F(100) * (x - 3418) / (cap - 3418))))}))
