"""Shared offline grading of saved paired-run captures with this repo's sforge harness.
grade(task_id, pkg_dir, version, name) -> dict (grade_output + rescale_score, as judge_submission does)."""
import json, sys
from pathlib import Path
REPO = Path(__file__).resolve().parents[4] if False else Path("/home/alex/edgebench-verified")
sys.path.insert(0, str(REPO))
from sforge.harness.benchmark import load_benchmark
from sforge.harness.task_spec import make_task_spec
from sforge.harness.grading import grade_output
from sforge.harness.score_rescale import rescale_score
from sforge.harness.selection import select_best

def specs(task_id, pkg):
    bench = load_benchmark(REPO / "tasks")
    return {"v1": make_task_spec(REPO / "tasks" / f"{task_id}.json", bench),
            "v2": make_task_spec(pkg / "task.json.in", bench)}

def grade(spec, out_dir, version, name):
    raw = (out_dir / f"{version}.{name}.raw.txt").read_text(encoding="utf-8", errors="replace")
    st_path = out_dir / f"{version}.{name}.status.json"
    st = json.loads(st_path.read_text()) if st_path.exists() else {"timed_out": False, "wall_s": 0.0}
    r = grade_output(spec, raw, name, st.get("timed_out", False), st.get("wall_s", 0.0))
    r.score_0_100 = rescale_score(spec.judge.rescale, r.score)
    return {"submission": name, "version": version, "valid": r.valid, "passed": r.passed,
            "total_tests": r.total_tests, "pass_rate": r.pass_rate, "score": r.score,
            "score_0_100": r.score_0_100, "summary": (r.summary or "")[:300],
            "metrics": r.metrics, "timed_out": st.get("timed_out"), "wall_s": st.get("wall_s"),
            "entry": {"type": "submission", "status": "completed", "round": name, "valid": r.valid,
                      "pass_rate": r.pass_rate, "score": r.score, "timed_out": r.timed_out}}
