"""Build fixed grading-model responses from the original rubrics.json (path argv[1]) into argv[2]."""
import json, sys, os
rules = json.load(open(sys.argv[1], encoding="utf-8"))["rules"]
out = sys.argv[2]; os.makedirs(out, exist_ok=True)

def row(r, score, cps=None, reason="x"):
    d = {"rule_id": r["rule_id"], "rule_name": r["title"], "scoring_mode": "deductive",
         "score": score, "max_score": r["max_score"], "reason": reason}
    if cps is not None:
        d["checkpoint_scores"] = cps
    return d

def full_cps(r, hit_idx=None):
    # deduction checkpoints: 0 = not triggered, points = triggered
    return [{"description": d["description"], "score": (d["points"] if i == hit_idx else 0),
             "max_score": d["points"], "evidence": "e"} for i, d in enumerate(r["scoring_details"])]

def dump(name, obj):
    with open(os.path.join(out, name + ".txt"), "w", encoding="utf-8") as f:
        f.write("```json\n" + json.dumps(obj, ensure_ascii=False) + "\n```\n")

# A: complete, honest, every rule assessed, first deduction triggered in every rule
A = [row(r, r["max_score"] - r["scoring_details"][0]["points"], full_cps(r, 0)) for r in rules]
dump("A_complete_one_deduction_each", {"scores": A, "summary": "ok"})
# B: complete, all rules zero (known-bad control); expressed as rule score 0 + floor reason
B = [row(r, 0, full_cps(r), reason="扣分超过上限，本规则得0") for r in rules]
dump("B_complete_all_zero", {"scores": B, "summary": "bad"})
# C: empty assessment list
dump("C_empty_scores", {"scores": [], "summary": "none"})
# D: same as A but R009 (15 pts, the largest rule) omitted
dump("D_A_minus_R009", {"scores": [x for x in A if x["rule_id"] != "R009"], "summary": "ok"})
# E: same as B but R009 omitted
dump("E_B_minus_R009", {"scores": [x for x in B if x["rule_id"] != "R009"], "summary": "bad"})
# F: R009 present with only a rule-level score of 0 and no checkpoints
F = [x for x in B if x["rule_id"] != "R009"] + [row(next(r for r in rules if r["rule_id"]=="R009"), 0, None, reason="poor")]
dump("F_B_R009_rule_score_only", {"scores": F, "summary": "bad"})
# G: R009 present but neither score nor checkpoints (malformed row)
G = [x for x in B if x["rule_id"] != "R009"] + [{"rule_id": "R009", "reason": "?"}]
dump("G_B_R009_no_score_no_checkpoints", {"scores": G, "summary": "bad"})
# H: non-JSON response (control: parse failure)
with open(os.path.join(out, "H_no_json.txt"), "w") as f: f.write("I could not grade this.\n")
# I: R009 present, rule-level score 0, but a complete all-zero checkpoint vector (inconsistent row)
I = [x for x in B if x["rule_id"] != "R009"]
r9 = next(r for r in rules if r["rule_id"] == "R009")
I.append(row(r9, 0, full_cps(r9), reason="poor"))
dump("I_B_R009_score0_zero_checkpoints", {"scores": I, "summary": "bad"})
