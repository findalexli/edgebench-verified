"""Gap responses for the revised fixed grader (after make_responses.py; argv[1] = response dir).
Each starts from B (all rules floored to 0) and changes one row so that the row reports a
deduction (score 0) that the earlier fixed grader's raw-row pre-check exempted, while
reconciliation (which reads the normalised row) gave the rule full marks:
  GA  R001 (has veto_conditions): veto stated only in veto_reason, rule_veto_triggered=false
  GB  R009: nine detail checkpoints 0, a tenth checkpoint beyond the rubric carries the deduction
  GC  R009 (no veto_conditions): rule_veto_triggered=true
  GD  R009: the floor wording appears after character 200 of reason (truncated by normalisation)
  M   control: R001 score 0, a negative checkpoint and a veto marker in reason; the original
      reconciles it as a veto (0); the earlier fixed grader rejected it."""
import json, os, sys
out = sys.argv[1]
t = open(os.path.join(out, "B_complete_all_zero.txt"), encoding="utf-8").read()
B = json.loads(t.split("```json\n", 1)[1].rsplit("\n```", 1)[0])["scores"]
def zero(row):
    return [dict(cp, score=0) for cp in row["checkpoint_scores"]]
def dump(name, rid, change):
    rows = []
    for r in B:
        r = json.loads(json.dumps(r))
        if r["rule_id"] == rid:
            r["checkpoint_scores"] = zero(r); r["reason"] = "poor"
            change(r)
        rows.append(r)
    with open(os.path.join(out, name + ".txt"), "w", encoding="utf-8") as f:
        f.write("```json\n" + json.dumps({"scores": rows, "summary": "bad"}, ensure_ascii=False) + "\n```\n")
dump("GA_R001_veto_reason_only", "R001", lambda r: r.update(rule_veto_triggered=False, veto_reason="veto: condition met"))
dump("GB_R009_extra_checkpoint", "R009", lambda r: r["checkpoint_scores"].append(
    {"description": "extra", "score": 4, "max_score": 4, "evidence": "e"}))
dump("GC_R009_flag_without_veto_conditions", "R009", lambda r: r.update(rule_veto_triggered=True, veto_reason="x"))
dump("GD_R009_floor_after_200_chars", "R009", lambda r: r.update(reason="p" * 205 + "扣分超过上限，本规则得0"))
def neg(r):
    r["checkpoint_scores"][0]["score"] = -1; r["reason"] = "poor veto"
dump("M_R001_negative_checkpoint_veto_marker", "R001", neg)
