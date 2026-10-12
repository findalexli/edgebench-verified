"""Grade the saved paired captures with this repo's sforge harness.
Usage: python3 grade.py [OUT_DIR]   (run from this directory; default OUT_DIR = result/out)
Arms: v1 (original), v2 (fixed) and, when its captures exist, v2prev (earlier fixed grader,
superseded 2026-10-12). graded.json goes to this directory, or to OUT_DIR/../.. when given."""
import json, re, sys
from pathlib import Path
from grade_common import specs, grade, select_best
HERE = Path(__file__).resolve().parent
OUT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else HERE / "result/out"
S = specs("college_english_exam_bank", HERE.parent)
S["v2prev"] = S["v2"]  # same task JSON; only the image differs
cases = [l.split()[0] for l in (HERE / "cases.txt").read_text().splitlines() if l.strip()]
cases = [n for n in cases if (OUT / f"v1.{n}.raw.txt").exists()]  # older runs lack the later cases
arms = ["v1"] + (["v2prev"] if (OUT / f"v2prev.{cases[0]}.raw.txt").exists() else []) + ["v2"]
def structured(v, n):
    t = (OUT / f"{v}.{n}.raw.txt").read_text(encoding="utf-8")
    return t.split(">>>>> Start Structured Result")[-1].split(">>>>> End Structured Result")[0].strip()
rows = {}
hdr = "| Fixed response | " + " | ".join(f"{v} valid | {v} score" for v in arms) + " | v2 model calls | v1==v2 structured output |"
print(hdr); print("| --- |" + " --- | ---: |" * len(arms) + " ---: | --- |")
for n in cases:
    r = {v: grade(S[v], OUT, v, n) for v in arms}
    calls = (OUT / f"v2.{n}.calls.txt").read_text().strip()
    same = structured("v1", n) == structured("v2", n)
    rows[n] = r
    f = lambda x: "-" if x is None else f"{x:g}"
    print(f"| {n} | " + " | ".join(f"{r[v]['valid']} | {f(r[v]['score'])}" for v in arms) + f" | {calls} | {same} |")
print()
for hist in (["A_complete_one_deduction_each", "C_empty_scores"], ["A_complete_one_deduction_each", "D_A_minus_R009"],
             ["B_complete_all_zero", "I_B_R009_score0_zero_checkpoints"], ["B_complete_all_zero", "GA_R001_veto_reason_only"]):
    if not all(n in rows for n in hist):
        continue
    for v in arms:
        b = select_best([dict(rows[n][v]["entry"], round=n) for n in hist], S[v].judge.score_direction, S[v].judge.selection)
        print(f"history {hist} {v} ({S[v].judge.selection}): best_round={b['best_round']} best_score={b['best_score']} best_valid={b['best_valid']}")
json.dump({n: {v: {k: x[k] for k in ('valid', 'score', 'score_0_100', 'pass_rate', 'summary')} for v, x in r.items()} for n, r in rows.items()},
          open(OUT.parent.parent / "graded.json" if len(sys.argv) > 1 else HERE / "graded.json", "w"), indent=1, ensure_ascii=False)
