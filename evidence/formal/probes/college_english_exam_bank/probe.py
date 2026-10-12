"""Runs the REAL v1/v2 _validate_result + reconcile_result_with_rubrics of grade_with_codex.py
on hand-built score lists (the gaps found by the Lean model CollegeEnglishGrader.lean).
Usage: python3 -I probe.py <v1 grade_with_codex.py sha b8b2824c...> <v2 grade_with_codex.py sha 1d941b58...> <rubrics.json sha d05f344e...>
The grader files are image-derived and are not stored in Git (materialize.sh regenerates them).
Prints total score out of 100 or REJECT:<reason> (v2 grading failure)."""
import importlib.util, json, sys
def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
o = load("orig", sys.argv[1]); f = load("fixed", sys.argv[2])
rules = json.load(open(sys.argv[3]))["rules"]
def row(r, score, cps, **kw):
    d = {"rule_id": r["rule_id"], "scoring_mode": "deductive", "score": score, "max_score": r["max_score"], "reason": "x"}
    if cps is not None: d["checkpoint_scores"] = cps
    d.update(kw); return d
def zero(r): return [{"score": 0, "max_score": d["points"]} for d in r["scoring_details"]]
def total(mod, obj, fixed):
    try:
        res = mod._validate_result(obj, rules) if fixed else mod._validate_result(obj)
    except ValueError as e: return "REJECT:" + str(e)
    res = mod.reconcile_result_with_rubrics(res, rules)
    return round(res["raw_total"] / res["max_total"] * 100, 6)
B = [row(r, 0, zero(r), reason="扣分超过上限，本规则得0") for r in rules]
r1 = rules[0]  # R001 has veto_conditions
cases = {
 "B": B,
 "veto_reason_only": [x for x in B if x["rule_id"] != "R001"] + [row(r1, 0, zero(r1), reason="poor", veto_reason="veto: condition met")],
 "neg_cp_veto_marker": [x for x in B if x["rule_id"] != "R001"] + [row(r1, 0, [{"score": -1}] + zero(r1)[1:], reason="poor veto")],
 "score_str_complete_zero_cps": [x for x in B if x["rule_id"] != "R009"] + [row(rules[8], "0", zero(rules[8]), reason="poor")],
}
for k, v in cases.items():
    print(k, "orig:", total(o, {"scores": v}, False), "fixed:", total(f, {"scores": v}, True))
r9 = rules[8]
more = {
 "extra_cp_after_details": [x for x in B if x["rule_id"] != "R009"] + [row(r9, 0, zero(r9) + [{"score": 4, "max_score": 4}], reason="poor")],
 "rvt_on_rule_without_veto": [x for x in B if x["rule_id"] != "R009"] + [row(r9, 0, zero(r9), reason="poor", rule_veto_triggered=True, veto_reason="x")],
 "floor_text_after_200_chars": [x for x in B if x["rule_id"] != "R009"] + [row(r9, 0, zero(r9), reason="p" * 205 + "扣分超过上限，本规则得0")],
 "flag_true_rule_with_veto": [x for x in B if x["rule_id"] != "R001"] + [row(r1, 0, zero(r1), reason="poor", rule_veto_triggered=True, veto_reason="veto: c")],
}
for k, v in more.items():
    print(k, "orig:", total(o, {"scores": v}, False), "fixed:", total(f, {"scores": v}, True))
