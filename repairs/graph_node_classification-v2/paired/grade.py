"""Grade saved paired captures (result/out) with EdgeBench's sforge harness (this repo's sforge/, 6e4e5f4). Run from this directory.
Arms v1, v2 and, when its captures exist, v2prev (the earlier fixed verifier); submissions that have no capture are skipped."""
import json
from pathlib import Path
from grade_common import specs, grade
HERE = Path(__file__).resolve().parent; OUT = HERE / "result/out"
PKG = next(p for p in (HERE.parent, HERE / "pkg") if (p / "task.json.in").exists())  # package dir, or a job's copy
S = specs("graph_node_classification", PKG)
S["v2prev"] = S["v2"]  # same task JSON; only the image differs
subs = [m for m in ["baseline", "neighbor", "neighbor_intkeys", "dupkeys_after_str", "nanconf", "shrink", "missing_half"]
        if (OUT / f"v1.{m}.raw.txt").exists()]
arms = ["v1"] + (["v2prev"] if (OUT / f"v2prev.{subs[0]}.raw.txt").exists() else []) + ["v2"]
def metrics(v, m):
    t = (OUT / f"{v}.{m}.raw.txt").read_text(errors="replace")
    s = t.split(">>>>> Start Structured Result")[-1].split(">>>>> End Structured Result")[0]
    try:
        return json.loads(s)
    except Exception:
        return {}
print("| Submission | Image | harness valid | score (final) | normalized 0-100 | overall (quality) | macro_f1 | micro_f1 | bal_acc | one_minus_ece | checks / reason |")
print("| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |")
out = {}
for m in subs:
    for v in arms:
        r = grade(S[v], OUT, v, m); j = metrics(v, m); mm = j.get("metrics", {})
        f = lambda k: f"{mm[k]:.6f}" if isinstance(mm.get(k), (int, float)) else "-"
        sc = "-" if r["score"] is None else f"{r['score']:.6f}"; n = "-" if r["score_0_100"] is None else f"{r['score_0_100']:.4f}"
        why = (j.get("summary") or "")[:110].replace("|", "/")
        print(f"| {m} | {v} | {r['valid']} | {sc} | {n} | {f('overall_score')} | {f('macro_f1')} | {f('micro_f1')} | {f('balanced_accuracy')} | {f('one_minus_ece')} | {why} |")
        out[f"{v}.{m}"] = {"harness": {k: r[k] for k in ("valid", "score", "score_0_100", "summary")}, "evaluator": j}
json.dump(out, open(HERE / "graded.json", "w"), indent=1)
