#!/usr/bin/env python3
"""Compare native eval_ahc.sh per-case results with the exact oracle, then push each
eval stdout through EdgeBench's harness in sforge/ (score_sum parser, TOTAL_SCORE extraction,
score_first selection, piecewise_max rescale).
Usage: compare.py CASES_DIR RESULTS_DIR REPO_ROOT"""
import json, re, sys, os
cases, res, repo = sys.argv[1:4]
sys.path.insert(0, repo)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from oracle import read_input, judge
from sforge.harness.log_parsers.score_sum import parse_score_sum
from sforge.harness.grading import extract_score
from sforge.harness.selection import select_best
from sforge.harness import score_rescale
spec_path = os.path.join(repo, "tasks/ad_placement_optimization.json")
summary = {}
for ctl in sorted(os.listdir(res)):
    d = os.path.join(res, ctl)
    log = open(os.path.join(d, "eval_stdout.log")).read()
    native = {m.group(1): (m.group(2), int(m.group(3)))
              for m in re.finditer(r"^CASE (\S+) (\S+) score=(\d+)$", log, re.M)}
    exits = dict(l.split() for l in open(os.path.join(d, "outs/exit_codes")))
    mism, exp_total = [], 0
    for f in sorted(os.listdir(cases)):
        cid = f[:-4]
        n, pts = read_input(os.path.join(cases, f))
        if ctl == "mixed" and n % 10 in (0, 1):
            exp = ("TLE", 0) if n % 10 == 0 else ("RE", 0)
        else:
            o = judge(n, pts, open(os.path.join(d, "outs", cid + ".txt"), encoding="utf-8").read())
            exp = (o["status"], o.get("score", 0))
            if not o.get("f64_matches_exact", True): mism.append((cid, "f64!=exact"))
        if exp[0] == "OK": exp_total += exp[1]
        if native.get(cid) != exp: mism.append((cid, native.get(cid), exp))
    recs = parse_score_sum(log)
    total = extract_score(log)
    entry = {"type": "submission", "status": "completed", "valid": True, "timed_out": False,
             "score": total, "pass_rate": sum(r["status"] == "passed" for r in recs) / len(recs)}
    sel = select_best([entry], "maximize", "score_first")
    summary[ctl] = {"cases": len(native), "native_total": total, "oracle_total": exp_total,
                    "per_case_mismatches": mism, "parser_records": len(recs),
                    "selected": sel["best_score"],
                    "normalized": score_rescale.rescale_score(score_rescale.parse_rescale_spec(json.load(open(spec_path))["judge"]["rescale"]), sel["best_score"])}
spec = json.load(open(spec_path))["judge"]["rescale"]
print(json.dumps(summary, indent=1))
print("rescale spec", spec)
