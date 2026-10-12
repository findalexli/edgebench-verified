#!/usr/bin/env python3
"""Maximum attainable hidden score with and without the unwinnable SAT cases.
usage: score_impact.py expected_answers.json selection_manifest.json scan_z3.jsonl"""
import json, sys
from fractions import Fraction as F
exp = json.load(open(sys.argv[1]))
man = {x["selected_path"]: x["difficulty"] for x in json.load(open(sys.argv[2]))}
unwinnable = set()
for line in open(sys.argv[3]):
    r = json.loads(line)
    if r.get("z3", {}).get("checker") == "unsat" and r["z3"].get("true") == "sat":
        unwinnable.add(r["file"])
W = {"easy": F(1, 10), "medium": F(2, 10), "hard": F(7, 10)}
def best(excl):
    tot = F(0)
    for d, w in W.items():
        cases = [k for k, v in man.items() if v == d]
        credit = sum((F(0) if k in excl else F(1)) if exp[k] == "sat" else F(1, 5) for k in cases)
        tot += w * credit / len(cases)
    return 100 * tot
for d in W:
    cases = [k for k, v in man.items() if v == d]
    print(d, "cases", len(cases), "sat", sum(exp[k] == "sat" for k in cases),
          "unwinnable", sum(k in unwinnable for k in cases))
a, b = best(set()), best(unwinnable)
print("unwinnable total", len(unwinnable))
print(f"max attainable (documented rules): {float(a):.3f}")
print(f"max attainable (original checker):  {float(b):.3f}")
print(f"points lost for a perfect solver:   {float(a-b):.3f}")
