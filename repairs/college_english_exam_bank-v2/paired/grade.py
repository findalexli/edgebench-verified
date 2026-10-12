"""Grade the saved paired captures (result/out) with this repo's sforge harness.
Usage: python3 grade.py  (run from this directory)"""
import json, re
from pathlib import Path
from grade_common import specs, grade, select_best
HERE = Path(__file__).resolve().parent; OUT = HERE / "result/out"
S = specs("college_english_exam_bank", HERE.parent)
cases = [l.split()[0] for l in (HERE / "cases.txt").read_text().splitlines() if l.strip()]
def structured(v, n):
    t = (OUT / f"{v}.{n}.raw.txt").read_text(encoding="utf-8")
    return t.split(">>>>> Start Structured Result")[-1].split(">>>>> End Structured Result")[0].strip()
rows = {}
print("| Fixed response | v1 valid | v1 score | v2 valid | v2 score | v2 model calls | v1==v2 structured output |")
print("| --- | --- | ---: | --- | ---: | ---: | --- |")
for n in cases:
    r = {v: grade(S[v], OUT, v, n) for v in ("v1", "v2")}
    calls = (OUT / f"v2.{n}.calls.txt").read_text().strip()
    same = structured("v1", n) == structured("v2", n)
    rows[n] = r
    f = lambda x: "-" if x is None else f"{x:g}"
    print(f"| {n} | {r['v1']['valid']} | {f(r['v1']['score'])} | {r['v2']['valid']} | {f(r['v2']['score'])} | {calls} | {same} |")
print()
for hist in (["A_complete_one_deduction_each", "C_empty_scores"], ["A_complete_one_deduction_each", "D_A_minus_R009"],
             ["B_complete_all_zero", "I_B_R009_score0_zero_checkpoints"]):
    for v in ("v1", "v2"):
        b = select_best([dict(rows[n][v]["entry"], round=n) for n in hist], S[v].judge.score_direction, S[v].judge.selection)
        print(f"history {hist} {v} ({S[v].judge.selection}): best_round={b['best_round']} best_score={b['best_score']} best_valid={b['best_valid']}")
json.dump({n: {v: {k: x[k] for k in ('valid', 'score', 'score_0_100', 'pass_rate', 'summary')} for v, x in r.items()} for n, r in rows.items()},
          open(HERE / "graded.json", "w"), indent=1, ensure_ascii=False)
