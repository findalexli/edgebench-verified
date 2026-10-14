#!/usr/bin/env python3
"""Summarize smt_solver v2 paired results: per arm/version verdict counts split by file class."""
import json, os
from collections import Counter
O = "/job/out" if os.path.isdir("/job/out") else os.path.join(os.path.dirname(__file__), "result", "out")
J = os.path.dirname(os.path.abspath(__file__))
cls = dict(l.split() for l in open(os.path.join(J, "file_classes.txt")))
def load(name):
    p = os.path.join(O, "json", name, "res.json")
    if not os.path.exists(p):
        return None
    d = json.load(open(p))
    return d, {r["benchmark"]: r for l in d["results"].values() for r in l}
per = {}
for arm in ["ground", "textual", "textual_true", "ground_wrong"]:
    for v in ["v1", "v2"]:
        x = load(f"{arm}-{v}")
        if not x:
            print(arm, v, "NO RESULT"); continue
        d, rs = x
        per[(arm, v)] = {b: r["verdict"] for b, r in rs.items()}
        for c in ["multi_context_27", "single_context_42"]:
            cnt = Counter(r["verdict"] for b, r in rs.items() if cls.get(b) == c)
            print(f"{arm:13s} {v} {c:18s} {dict(sorted(cnt.items()))}")
        print(f"{arm:13s} {v} final_score {d.get('final_score')}")
for arm in ["ground", "textual", "textual_true", "ground_wrong"]:
    a, b = per.get((arm, "v1")), per.get((arm, "v2"))
    if a and b:
        flips = Counter((a[k], b.get(k)) for k in a if a[k] != b.get(k))
        print(f"flips {arm}: {dict(flips)}")
for v in ["v1", "v2"]:
    x = load(f"mini-{v}")
    if not x:
        print("mini", v, "NO RESULT"); continue
    d, rs = x
    for b in sorted(rs):
        print(f"mini {v} {b:40s} {rs[b]['verdict']:14s} {(rs[b].get('model_error') or '')[:80]}")
    print(f"mini {v} final_score {d.get('final_score')}")
p = os.path.join(O, "oracle.jsonl")
if os.path.exists(p):
    rows = [json.loads(l) for l in open(p)]
    print("oracle C verdicts", dict(Counter(r.get("oracle_C") for r in rows)),
          "Cw built", sum(1 for r in rows if r.get("oracle_Cw") == "unsat"), "of", len(rows))
