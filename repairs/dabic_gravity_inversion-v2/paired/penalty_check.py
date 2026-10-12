"""Derived check, run inside each image with that image's evaluator: apply
structural_penalty_v34 to an arm's own native breakdown with only the C score replaced.
Usage: python penalty_check.py <eval_result.json> <label>"""
import json, sys
sys.path.insert(0, "/opt/evaluator")
import eval_dabic_v2 as E
r = json.load(open(sys.argv[1], encoding="utf-8"))
bd = r["breakdown"]; c0 = float(bd["C_hidden_scenarios"].get("score", 0.0))
for c in (20.0, 26.0, 30.0):
    b = json.loads(json.dumps(bd)); b["C_hidden_scenarios"]["score"] = c
    pen, det = E.structural_penalty_v34(b)
    raw = r["raw_total"] - c0 + c
    print(f"{sys.argv[2]} C={c:g} penalty={pen} reason={det['reason']} total={raw*pen:.2f}")
