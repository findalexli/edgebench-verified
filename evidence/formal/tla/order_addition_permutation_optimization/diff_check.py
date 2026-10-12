"""Differential check: the claims of OrderSelection.tla, re-checked against the REAL
sforge/harness/selection.py select_best on every run of up to 3 submissions over the
same abstract alphabet (64 submission kinds), plus a replay of the recorded paired
reports in repairs/order_addition_permutation_optimization-v2/paired/graded.json.
Run from the repository root:  python3 evidence/formal/tla/order_addition_permutation_optimization/diff_check.py"""
import itertools, json, sys
sys.path.insert(0, ".")
from sforge.harness.selection import select_best

TESTS = ("T1", "T3", "T4", "T5")
KINDS = [(frozenset(c), sc) for r in range(5) for c in itertools.combinations(TESTS, r) for sc in (1, 2, 3)]
VAL = {1: 0.001, 2: 0.002, 3: 0.003}          # abstract score -> TOTAL_SCORE value

def entry(kind, fixed, i):
    p, sc = kind
    if "T1" not in p and "T5" in p:            # two TOTAL_SCORE lines -> grading error
        return {"type": "submission", "round": i, "error": "Multiple TOTAL_SCORE records"}
    score = VAL[sc] if "T5" in p else (0.0 if "T1" not in p else None)
    return {"type": "submission", "round": i, "status": "completed", "valid": True,
            "pass_rate": (len(p) + fixed) / 5, "score": score}

n = 0
for L in range(1, 4):
    for seq in itertools.product(KINDS, repeat=L):
        n += 1
        b1 = select_best([entry(k, 0, i + 1) for i, k in enumerate(seq)], "maximize", "pass_rate_first")
        b2 = select_best([entry(k, 1, i + 1) for i, k in enumerate(seq)], "maximize", "pass_rate_first")
        s1 = select_best([entry(k, 0, i + 1) for i, k in enumerate(seq)], "maximize", "score_first")
        s2 = select_best([entry(k, 1, i + 1) for i, k in enumerate(seq)], "maximize", "score_first")
        valid = [i + 1 for i, k in enumerate(seq) if k[0] == frozenset(TESTS)]
        if valid:
            best = max(seq[i - 1][1] for i in valid)
            assert b1["best_round"] == valid[0], seq                                     # C1
            assert b2["best_score"] == VAL[best] and b2["best_pass_rate"] == 1.0, seq    # C2
            assert b2["best_round"] == min(i for i in valid if seq[i - 1][1] == best), seq
        assert s1 == {**s2, "best_pass_rate": s1["best_pass_rate"]}, seq                 # C4
        scored = [i + 1 for i, k in enumerate(seq) if not ("T1" not in k[0] and "T5" in k[0])
                  and ("T5" in k[0] or "T1" not in k[0])]
        if valid and scored == valid:
            assert b2["best_score"] == s2["best_score"], seq                             # C5
print(f"claims C1 C2 C4 C5 hold on real select_best for {n} runs (length 1-3)")

g = json.load(open("repairs/order_addition_permutation_optimization-v2/paired/graded.json"))
for order in (["identity", "search"], ["search", "identity"], ["dup", "identity", "search"],
              ["badcost", "identity", "search"]):
    for v in ("v1", "v2"):
        es = [{"type": "submission", "round": s, "status": "completed", **{k: g[v][s][k] for k in
              ("valid", "pass_rate", "score")}} for s in order]
        b = select_best(es, "maximize", "pass_rate_first")
        # model prediction: v1 -> first valid (identity/search); v2 -> highest-scoring valid (search)
        expect = next(s for s in order if s in ("identity", "search")) if v == "v1" else "search"
        assert b["best_round"] == expect, (order, v, b)
        print(order, v, "->", b["best_round"], b["best_score"])
for v in ("v1", "v2"):   # K3 on recorded reports: a run of only score-less submissions
    b = select_best([{"type": "submission", "round": "badcost", "status": "completed",
                      **{k: g[v]["badcost"][k] for k in ("valid", "pass_rate", "score")}}])
    print("only badcost", v, "->", b)
