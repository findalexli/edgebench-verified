"""Extra fixed responses for the v2 paired run (after make_responses.py).
L: case A with every rule-level "score" field removed (complete checkpoint vectors only)."""
import json, os, sys
out = sys.argv[1]
t = open(os.path.join(out, "A_complete_one_deduction_each.txt"), encoding="utf-8").read()
obj = json.loads(t.split("```json\n", 1)[1].rsplit("\n```", 1)[0])
for r in obj["scores"]:
    r.pop("score")
with open(os.path.join(out, "L_A_without_rule_scores.txt"), "w", encoding="utf-8") as f:
    f.write("```json\n" + json.dumps(obj, ensure_ascii=False) + "\n```\n")
