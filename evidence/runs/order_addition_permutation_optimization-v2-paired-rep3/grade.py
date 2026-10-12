"""Grade saved paired captures (result/out) with this repo's sforge harness, then apply the
task's selection (pass_rate_first) to submission histories. Run from this directory."""
import json
from pathlib import Path
from grade_common import specs, grade, select_best
HERE = Path(__file__).resolve().parent; OUT = HERE / "result/out"
S = specs("order_addition_permutation_optimization", HERE.parent)
subs = ["identity", "search", "badcost", "dup"]
R = {v: {m: grade(S[v], OUT, v, m) for m in subs} for v in ("v1", "v2")}
print("| Submission | Image | Tests passed | pass_rate | valid | raw TOTAL_SCORE | normalized (0-100) | eval exit |")
print("| --- | --- | --- | ---: | --- | ---: | ---: | --- |")
for m in subs:
    for v in ("v1", "v2"):
        r = R[v][m]; st = json.loads((OUT / f"{v}.{m}.status.json").read_text())
        print(f"| {m} | {v} | {r['passed']}/{r['total_tests']} | {r['pass_rate']:.2f} | {r['valid']} | {r['score']} | {r['score_0_100']} | rc={st['rc']} |")
print()
for hist in (["identity", "search"], ["search", "identity"], ["dup", "identity", "search"], ["badcost", "identity", "search"]):
    for v in ("v1", "v2"):
        b = select_best([dict(R[v][m]["entry"], round=m) for m in hist], S[v].judge.score_direction, S[v].judge.selection)
        print(f"history {hist} {v} ({S[v].judge.selection}): best_round={b['best_round']} best_score={b['best_score']} best_pass_rate={b['best_pass_rate']}")
json.dump({v: {m: {k: R[v][m][k] for k in ("valid", "passed", "total_tests", "pass_rate", "score", "score_0_100", "summary")} for m in subs} for v in R},
          open(HERE / "graded.json", "w"), indent=1)
