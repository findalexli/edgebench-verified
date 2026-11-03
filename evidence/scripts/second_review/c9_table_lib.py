"""Shared loader for the c9_*_table.py scripts: one row per graded arm of a job, from result/out/g/*.json."""
import glob, json, os, re, statistics as st
ROOT = "evidence/runs/"
def load(jobs):
    rows = {}
    for job in jobs:
        w = ROOT + job + "/result/worker.json"
        status = json.load(open(w)).get("status") if os.path.exists(w) else "not finished"
        for f in sorted(glob.glob(ROOT + job + "/result/out/g/*.json")):
            d = json.load(open(f)); lb = os.path.basename(f)[:-5]
            arm = re.sub(r"-p\d+$", "", lb); arm = re.sub(r"^s-", "", arm)
            rows.setdefault(arm, []).append(dict(job=job, label=lb, raw=d.get("raw_score"), s=d.get("score_0_100"), valid=d.get("valid"),
                                                 rt=d.get("runtime_s"), summary=d.get("summary"), result=d.get("result") or {}, log=d.get("log") or ""))
        print("job", job, "status", status)
    return rows
def fmt(v, n=4):
    return "None" if v is None else f"{v:.{n}f}"
def show(rows, key="s"):
    for arm, rs in sorted(rows.items()):
        print(f"{arm:32s} n={len(rs)} {key}=[{', '.join(fmt(r[key]) for r in rs)}] raw=[{', '.join(fmt(r['raw'],6) for r in rs)}] valid={[r['valid'] for r in rs]} rt={[r['rt'] for r in rs]}")

def arms(rows, spec, key="s"):
    """spec: [(arm name, label)] -> JSON arms with scores taken from the results (key: s normalized, raw judge raw)."""
    out = []
    for arm, label in spec:
        rs = rows.get(arm, [])
        out.append({"label": label, "scores": [r[key] for r in rs], "n": len(rs)})
    return out
def mean(rows, arm, key="s"):
    v = [r[key] for r in rows[arm]]
    return sum(v) / len(v)
