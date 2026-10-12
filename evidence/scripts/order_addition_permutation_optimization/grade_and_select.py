"""Feed saved judge logs through the repo's sforge grading + selection code.
Usage: python grade_and_select.py HARNESS_ROOT TASKS_DIR LOGDIR
(HARNESS_ROOT = this repo for the maintained harness, or a copy of upstream sforge)"""
import json, sys
from pathlib import Path
harness, tasks, logdir = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
sys.path.insert(0, str(harness))
from sforge.harness.benchmark import load_benchmark
from sforge.harness.task_spec import make_task_spec
from sforge.harness.grading import grade_output
from sforge.harness.score_rescale import rescale_score
from sforge.harness.selection import select_best
from sforge.harness.constants import START_TEST_OUTPUT, END_TEST_OUTPUT
spec = make_task_spec(tasks / "order_addition_permutation_optimization.json", load_benchmark(tasks))
def grade(name):
    raw = f"{START_TEST_OUTPUT}\n" + (logdir / name).read_text() + f"\n{END_TEST_OUTPUT}\n"
    r = grade_output(spec, raw, name)
    return {"type": "submission", "status": "completed", "submission_id": name, "round": name,
            "pass_rate": r.pass_rate, "score": r.score, "valid": r.valid,
            "score_0_100": rescale_score(spec.judge.rescale, r.score)}
print("harness =", harness, "selection =", spec.judge.selection, "direction =", spec.judge.score_direction)
for variant in ("original", "repaired"):
    print(f"\n### {variant} judge")
    ents = {m: grade(f"{m}.{variant}.log") for m in ("identity", "search", "badcost", "dup")}
    for m, e in ents.items():
        print(f"  {m:9s} pass_rate={e['pass_rate']:.2f} score={e['score']} score_0_100={e['score_0_100']}")
    for order in (["identity", "search"], ["search", "identity"], ["dup", "identity", "search"]):
        b = select_best([ents[m] for m in order], spec.judge.score_direction, spec.judge.selection)
        print(f"  submissions in order {order}: selected round={b['best_round']} best_score={b['best_score']}")
