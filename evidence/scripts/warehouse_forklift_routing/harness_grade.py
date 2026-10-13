#!/usr/bin/env python3
"""Feed saved native evaluator stdout through EdgeBench's harness in sforge/ (grade_output ->
score_first selection -> rescale). Usage: harness_grade.py <stdout files...>"""
import sys
from pathlib import Path
REPO = __import__('os').environ.get('EBV_REPO') or str(__import__('pathlib').Path(__file__).resolve().parents[3])
sys.path.insert(0, REPO)
from sforge.harness.benchmark import load_benchmark
from sforge.harness.task_spec import make_task_spec
from sforge.harness.grading import grade_output
from sforge.harness.selection import select_best
from sforge.harness.score_rescale import parse_rescale_spec, rescale_score
import json
tasks = Path(REPO) / 'tasks'
spec = make_task_spec(tasks / 'warehouse_forklift_routing.json', load_benchmark(tasks))
resc = parse_rescale_spec(json.load(open(tasks / 'warehouse_forklift_routing.json'))['judge']['rescale'])
entries = []
rnd = lambda x: None if x is None else round(x, 4)  # rescale_score gives None for a missing or non-finite (inf) score
for i, f in enumerate(sys.argv[1:]):
    rep = grade_output(spec, open(f).read(), submission_id=Path(f).stem)
    e = {"type": "submission", "status": "completed", "valid": rep.valid, "timed_out": rep.timed_out,
         "pass_rate": rep.pass_rate, "score": rep.score, "round": Path(f).stem, "error": None}
    entries.append(e)
    print("%-14s valid=%s pass_rate=%.3f score=%s normalized=%s summary=%s" % (
        Path(f).stem, rep.valid, rep.pass_rate, rep.score,
        rnd(rescale_score(resc, rep.score)), rep.summary[:90]))
best = select_best(entries, spec.judge.score_direction, spec.judge.selection)
print("score_first selection over all of the above:", best,
      "normalized:", rnd(rescale_score(resc, best["best_score"])))
