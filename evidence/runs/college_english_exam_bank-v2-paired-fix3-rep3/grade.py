"""Grade the saved paired captures with EdgeBench's sforge harness (this repo's sforge/, 6e4e5f4).
Usage: python3 grade.py [OUT_DIR]   (run from this directory; default OUT_DIR = result/out)
Arms: v1 (original), v2 (fixed) and, when its captures exist, v2prev (earlier fixed grader,
superseded 2026-10-12). graded.json goes to this directory, or to OUT_DIR/../.. when given."""
import json, re, sys
from pathlib import Path
from grade_common import specs, grade, select_best
HERE = Path(__file__).resolve().parent
OUT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else HERE / "result/out"
PKG = next(p for p in (HERE.parent, HERE / "pkg") if (p / "task.json.in").exists())  # package dir, or a job's copy
S = specs("college_english_exam_bank", PKG)
S["v2prev"] = S["v2"]  # same task JSON; only the image differs
cases = [l.split()[0] for l in (HERE / "cases.txt").read_text().splitlines() if l.strip()]
cases = [n for n in cases if (OUT / f"v1.{n}.raw.txt").exists()]  # older runs lack the later cases
arms = ["v1"] + (["v2prev"] if (OUT / f"v2prev.{cases[0]}.raw.txt").exists() else []) + ["v2"]
def structured(v, n):
    t = (OUT / f"{v}.{n}.raw.txt").read_text(encoding="utf-8")
    return t.split(">>>>> Start Structured Result")[-1].split(">>>>> End Structured Result")[0].strip()
rows = {}
callarms = [v for v in arms if v != "v1"]
hdr = "| Fixed response | " + " | ".join(f"{v} valid | {v} score" for v in arms) + "".join(f" | {v} model calls" for v in callarms) + " | v1==v2 structured output |"
print(hdr); print("| --- |" + " --- | ---: |" * len(arms) + " ---: |" * len(callarms) + " --- |")
for n in cases:
    r = {v: grade(S[v], OUT, v, n) for v in arms}
    calls = " | ".join((OUT / f"{v}.{n}.calls.txt").read_text().strip() for v in callarms)
    same = structured("v1", n) == structured("v2", n)
    rows[n] = r
    f = lambda x: "-" if x is None else f"{x:g}"
    print(f"| {n} | " + " | ".join(f"{r[v]['valid']} | {f(r[v]['score'])}" for v in arms) + f" | {calls} | {same} |")
print()
for hist in (["A_complete_one_deduction_each", "C_empty_scores"], ["A_complete_one_deduction_each", "D_A_minus_R009"],
             ["B_complete_all_zero", "I_B_R009_score0_zero_checkpoints"], ["B_complete_all_zero", "GA_R001_veto_reason_only"],
             ["A_complete_one_deduction_each", "NZ_full_marks_block_then_D_block_one_output"]):
    if not all(n in rows for n in hist):
        continue
    for v in arms:
        b = select_best([dict(rows[n][v]["entry"], round=n) for n in hist], S[v].judge.score_direction, S[v].judge.selection)
        print(f"history {hist} {v} ({S[v].judge.selection}): best_round={b['best_round']} best_score={b['best_score']} best_valid={b['best_valid']}")
json.dump({n: {v: {k: x[k] for k in ('valid', 'score', 'score_0_100', 'pass_rate', 'summary')} for v, x in r.items()} for n, r in rows.items()},
          open(OUT.parent.parent / "graded.json" if len(sys.argv) > 1 else HERE / "graded.json", "w"), indent=1, ensure_ascii=False)
