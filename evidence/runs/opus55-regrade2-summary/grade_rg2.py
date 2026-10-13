"""Grade collected regrade captures offline with EdgeBench's own sforge grade_output + rescale_score.
usage: grade_rg2.py REPO RAWDIR OUTJSON  -> list of derived rows (no output text kept)."""
import json, sys, glob, os, re
from pathlib import Path
REPO = Path(sys.argv[1]); RAW = Path(sys.argv[2]); OUT = Path(sys.argv[3])
sys.path.insert(0, str(REPO))
from sforge.harness.benchmark import load_benchmark
from sforge.harness.task_spec import make_task_spec
from sforge.harness.grading import grade_output
from sforge.harness.score_rescale import rescale_score
bench = load_benchmark(REPO / "tasks")
specs = {}
def spec(t, v):
    if (t, v) not in specs:
        p = REPO / "tasks" / f"{t}.json" if v == "v1" else REPO / "repairs" / f"{t}-v2" / "task.json.in"
        specs[(t, v)] = make_task_spec(p, bench)
    return specs[(t, v)]
rows = []
for st in sorted(RAW.glob("*.status.json")):
    m = re.match(r"(.+)\.([^.]+)\.rep(\d+)\.(v[12])\.status\.json$", st.name)
    t, r, rep, v = m.group(1), m.group(2), int(m.group(3)), m.group(4)
    s = json.loads(st.read_text())
    raw = (RAW / st.name.replace(".status.json", ".raw.txt")).read_text(errors="replace")
    sp = spec(t, v)
    g = grade_output(sp, raw, f"{r}", s["timed_out"], s["wall_s"])
    shaf = RAW / f"{t}.{r}.sha256"
    sub_sha = None
    if shaf.exists():
        for line in shaf.read_text().split("\n"):
            if line.endswith("submission.tar.gz"): sub_sha = line.split()[0]
    ex = RAW / st.name.replace(".status.json", ".extract.txt")
    rows.append({"task": t, "round": r, "rep": rep, "version": v, "valid": g.valid, "passed": g.passed,
                 "total_tests": g.total_tests, "pass_rate": g.pass_rate, "score": g.score,
                 "score_0_100": rescale_score(sp.judge.rescale, g.score), "timed_out": s["timed_out"],
                 "rc": s["rc"], "wall_s": s["wall_s"], "n_allowed_files": s.get("n_allowed"),
                 "extract_ok": ex.exists() and "extract_rc=0" in ex.read_text(),
                 "submission_tar_sha256": sub_sha, "raw_output_sha256": __import__("hashlib").sha256(raw.encode("utf-8", "surrogateescape")).hexdigest(),
                 "summary": (g.summary or "")[:160]})
OUT.write_text(json.dumps(rows, indent=1) + "\n")
print(len(rows), "rows")
