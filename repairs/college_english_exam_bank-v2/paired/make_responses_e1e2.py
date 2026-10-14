"""Responses for the v2.2 revision (after make_responses.py and make_responses_multiblock.py;
argv[1] = response dir). Review edge cases e1 (rule score as a string or bool) and e2 (which JSON
block of one output is scored).
  e1, built from A (77) or I:
  QA  A with R009's rule score as the numeric string of its own value ("11")
  QB  A with every rule score as a padded decimal string (e.g. " 11.0 ")
  QC  A with R009's rule score true (bool; must stay rejected)
  QD  A with R009's rule score "twelve" (not a number; must stay rejected)
  QE  I with R009's score "0" (string) and all-zero checkpoints (inconsistent; must stay rejected)
  QF  F with R009's score "0" and no checkpoints (incomplete; must stay rejected)
  e2, one model output with two fenced blocks unless stated:
  NZ  a full-marks block (every rule at max, consistent) followed by D's block (incomplete)
  NU  A's JSON then D's JSON, both unfenced (the raw_decode path)"""
import json, os, sys
out = sys.argv[1]
rd = lambda n: open(os.path.join(out, n + ".txt"), encoding="utf-8").read()
obj = lambda n: json.loads(rd(n).split("```json\n", 1)[1].rsplit("\n```", 1)[0])
fence = lambda o: "```json\n" + json.dumps(o, ensure_ascii=False) + "\n```\n"
def dump(name, body):
    with open(os.path.join(out, name + ".txt"), "w", encoding="utf-8") as f:
        f.write(body)
def change(base, rid, fn):
    o = obj(base)
    for r in o["scores"]:
        if rid is None or r["rule_id"] == rid:
            fn(r)
    return o
def fmt(x):
    return str(int(x)) if float(x).is_integer() else str(x)
dump("QA_A_R009_score_numeric_string", fence(change("A_complete_one_deduction_each", "R009", lambda r: r.update(score=fmt(r["score"])))))
dump("QB_A_all_scores_padded_decimal_strings", fence(change("A_complete_one_deduction_each", None, lambda r: r.update(score=" %.1f " % float(r["score"])))))
dump("QC_A_R009_score_bool", fence(change("A_complete_one_deduction_each", "R009", lambda r: r.update(score=True))))
dump("QD_A_R009_score_word", fence(change("A_complete_one_deduction_each", "R009", lambda r: r.update(score="twelve"))))
dump("QE_I_R009_score_string0_zero_checkpoints", fence(change("I_B_R009_score0_zero_checkpoints", "R009", lambda r: r.update(score="0"))))
dump("QF_F_R009_score_string0_no_checkpoints", fence(change("F_B_R009_rule_score_only", "R009", lambda r: r.update(score="0"))))
def full(r):
    r["score"] = r["max_score"]; r["reason"] = "no fault found"
    for cp in r["checkpoint_scores"]:
        cp["score"] = 0
Z = change("A_complete_one_deduction_each", None, full)
D = obj("D_A_minus_R009")
dump("NZ_full_marks_block_then_D_block_one_output", "Draft assessment:\n" + fence(Z) + "\nRevised assessment:\n" + rd("D_A_minus_R009"))
dump("NU_A_then_D_unfenced_one_output", "Draft assessment: " + json.dumps(obj("A_complete_one_deduction_each"), ensure_ascii=False)
     + "\nRevised assessment: " + json.dumps(D, ensure_ascii=False) + "\n")
