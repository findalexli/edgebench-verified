"""Grade saved paired captures (result/out) with EdgeBench's sforge harness (this repo's sforge/, 6e4e5f4). Run from this directory."""
import json, re
from pathlib import Path
from grade_common import specs, grade
HERE = Path(__file__).resolve().parent; OUT = HERE / "result/out"
S = specs("jagua_nesting_optimization", HERE.parent)
subs = ["baseline", "seed_shift", "drop_last_item"]
print("| Submission | Image | valid | raw TOTAL_SCORE | normalized | cases OK / WA / RE / other | case lines identical v1 vs v2 (ignoring timings) |")
print("| --- | --- | --- | ---: | ---: | --- | --- |")
def cases(v, m):
    t = (OUT / f"{v}.{m}.raw.txt").read_text(errors="replace")
    return [l for l in t.splitlines() if l.startswith("CASE ")]
def strip_time(l):
    return re.sub(r"rt=[0-9.]+,time=[0-9.]+s,ref_time=[0-9.]+s", "", l)
out = {}
for m in subs:
    same = [strip_time(a) for a in cases("v1", m)] == [strip_time(b) for b in cases("v2", m)]
    for v in ("v1", "v2"):
        r = grade(S[v], OUT, v, m); cs = cases(v, m)
        cnt = {k: sum(1 for l in cs if l.split()[2] == k) for k in ("OK", "WA", "RE")}
        other = len(cs) - sum(cnt.values())
        print(f"| {m} | {v} | {r['valid']} | {r['score']} | {r['score_0_100']} | {cnt['OK']} / {cnt['WA']} / {cnt['RE']} / {other} | {same} |")
        out[f"{v}.{m}"] = {"harness": {k: r[k] for k in ("valid", "score", "score_0_100")}, "cases": cs}
json.dump(out, open(HERE / "graded.json", "w"), indent=1)
