#!/usr/bin/env python3
"""Grade native evaluator logs with the repository harness (grading -> rescale -> selection).
Usage (from repo root on PYTHONPATH): grade.py <task.json> <log>..."""
import sys, json, types
from sforge.harness.grading import grade_output
from sforge.harness.score_rescale import parse_rescale_spec, rescale_score
from sforge.harness.selection import select_best
task = json.load(open(sys.argv[1]))
j = task['judge']
spec = types.SimpleNamespace(task_id=task['task_id'],
                             judge=types.SimpleNamespace(parser=j['parser']))
rs = parse_rescale_spec(j['rescale'])
for log in sys.argv[2:]:
    raw = open(log).read()
    r = grade_output(spec, raw, log)
    norm = rescale_score(rs, r.score)
    sel = select_best([{"type": "submission", "status": "completed", "score": r.score,
                        "pass_rate": r.pass_rate, "valid": r.valid, "timed_out": r.timed_out,
                        "round": "r1"}], j['score_direction'], j['selection'])
    print(f"{log.split('/')[-1]:24s} valid={r.valid} raw={r.score} pass_rate={r.pass_rate:.2f} "
          f"normalized={None if norm is None else round(norm, 4)} selected_best={sel['best_score']} "
          f"best_valid={sel['best_valid']} reason={r.metrics.get('grading_error')}")
# piecewise_min reference points
for raw in (2 * 50, 554.75, 1575, 4490, 94092, 7744909, 9025986):
    print('rescale', raw, round(rescale_score(rs, raw), 4))
# two-round selection: a valid round followed by a round with one honest failed case
reps = [grade_output(spec, open(l).read(), l) for l in sys.argv[2:]]
ents = [{"type": "submission", "status": "completed", "score": r.score, "pass_rate": r.pass_rate,
         "valid": r.valid, "timed_out": r.timed_out, "round": l.split('/')[-1]}
        for r, l in zip(reps, sys.argv[2:])]
print('select_best over all logs as rounds:', select_best(ents, j['score_direction'], j['selection']))
