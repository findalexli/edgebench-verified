"""Grade saved judge logs with a given sforge harness copy and apply the task's
selection policy + rescale. Usage: python grade_and_select.py HARNESS_ROOT TASKS_DIR LOGDIR"""
import sys, itertools
from pathlib import Path
harness, tasks, logdir = map(Path, sys.argv[1:4])
sys.path.insert(0, str(harness))
from sforge.harness.benchmark import load_benchmark
from sforge.harness.task_spec import make_task_spec
from sforge.harness.grading import grade_output
from sforge.harness.score_rescale import rescale_score
from sforge.harness.selection import select_best
spec = make_task_spec(tasks / "wireless_electricity_layout.json", load_benchmark(tasks))
print("harness:", harness, "| selection:", spec.judge.selection, spec.judge.score_direction)
ents = {}
for name in ("baseline", "ce", "re_some"):
    r = grade_output(spec, (logdir / f"{name}.log").read_text(), name)
    ents[name] = {"type": "submission", "status": "completed", "round": name,
                  "pass_rate": r.pass_rate, "score": r.score, "valid": r.valid}
    print(f"  {name:9s} valid={r.valid} pass_rate={r.pass_rate:.2f} raw={r.score} "
          f"norm={rescale_score(spec.judge.rescale, r.score)} summary={(r.summary or '')[:70]!r}")
for order in (["baseline", "ce"], ["ce", "baseline"], ["re_some", "ce"], ["baseline", "re_some", "ce"]):
    b = select_best([ents[m] for m in order], spec.judge.score_direction, spec.judge.selection)
    print(f"  history {order}: selected={b['best_round']} raw={b['best_score']} "
          f"norm={rescale_score(spec.judge.rescale, b['best_score'])}")
