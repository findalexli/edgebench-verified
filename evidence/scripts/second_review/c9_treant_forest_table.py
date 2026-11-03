#!/usr/bin/env python3
"""community9 treant_forest: real runs on the current judge, with the linear rescale, and with the tester's 2*N*N stop removed.
Also: all archived real submissions against the cap."""
import glob, hashlib, json, os, re, sys
sys.path.insert(0, os.path.dirname(__file__))
from c9_table_lib import load, show, fmt
rows = load(["community9-treant_forest-smoke", "community9-treant_forest-a"])
show(rows)
print("\nper-case: how many of 50 cases sit at 2N^2 on the capped judge, and exceed it when the stop is removed")
caps = None
for arm in sorted(rows):
    for r in rows[arm]:
        cs = re.findall(r"CASE (\d+) (\w+) score=(\d+)", r["log"])
        ok = sum(1 for c in cs if c[1] == "OK")
        print(f"  {r['label']:24s} raw={r['raw']} cases={len(cs)} OK={ok} nonOK={[c[:2] for c in cs if c[1]!='OK'][:5]} top={max((int(c[2]) for c in cs), default=0)}")
def caseof(lb):
    for arm in rows:
        for r in rows[arm]:
            if r["label"] == lb:
                return {c[0]: int(c[2]) for c in re.findall(r"CASE (\d+) (\w+) score=(\d+)", r["log"])}
for n in ["agent10", "agent40", "agent33", "agent1", "greedy"]:
    a = caseof(f"old-{n}-p1"); b = caseof(f"nocap-{n}-p1")
    if a and b:
        print(f"  {n}: cases where nocap > capped: {sum(1 for k in a if b.get(k,0) > a[k])}/50; capped sum {sum(a.values())}, nocap sum {sum(b.values())}")
print("\nreal archive (all 87 reports): raw and normalized")
T = "treant_forest"; U = {}
for rp in glob.glob(f"evidence/runs/claude-opus-{T}*/result/out/sforge-logs/runs/*/{T}/submissions/*/report.json"):
    d = json.load(open(rp)); sha = hashlib.sha256(open(rp.replace("report.json", "submission.tar.gz"), "rb").read()).hexdigest()[:12]
    U.setdefault(sha, []).append((d["score"], d["score_0_100"]))
vals = [x for v in U.values() for x in v]
print(f"  reports {len(vals)} unique files {len(U)} raw min {min(x[0] for x in vals)} max {max(x[0] for x in vals)} normalized min {min(x[1] for x in vals):.3f} max {max(x[1] for x in vals):.3f}")
print(f"  reports at exactly 92304: {sum(1 for x in vals if x[0]==92304)}; files with a report at 92304: {sum(1 for v in U.values() if any(x[0]==92304 for x in v))}")

from c9_table_lib import arms, mean
claim = json.load(open(".internal/upstream-sweep/round3/treant_forest.json"))["claims"][0]["claim"]
eff_rescale = mean(rows, "new-agent10") - mean(rows, "old-agent10")
eff_nocap = mean(rows, "nocap-agent10") - mean(rows, "old-agent10")
print(f"\neffect agent10: linear rescale +{eff_rescale:.2f}, stop removed on the same anchors +{eff_nocap:.2f}")
print(f"order flip: agent1 capped {mean(rows,'old-agent1'):.3f} < agent10 capped {mean(rows,'old-agent10'):.3f}; stop removed agent1 {mean(rows,'nocap-agent1'):.3f} > agent10 {mean(rows,'nocap-agent10'):.3f}")
out = {"task": "treant_forest", "claims": [{
    "claim": claim, "verdict": "CONFIRMED", "witness": "real unchanged (agent-10, agent-40, agent-33, agent-1 of the Opus run); synthetic controls: grid-only greedy, invalid",
    "arms": arms(rows, [("old-starter", "starter, current judge"), ("old-greedy", "good control: grid-only greedy, current judge"), ("old-invalid", "bad control: invalid, current judge"),
                        ("old-agent10", "real agent-10, current judge"), ("old-agent40", "real agent-40, current judge"), ("old-agent33", "real agent-33, current judge"), ("old-agent1", "real agent-1, current judge"),
                        ("new-agent10", "real agent-10, linear 3418..92304"), ("new-agent33", "real agent-33, linear 3418..92304"), ("new-greedy", "greedy, linear 3418..92304"), ("new-starter", "starter, linear"), ("new-invalid", "invalid, linear"),
                        ("nocap-agent10", "real agent-10, tester stop removed, same anchors"), ("nocap-agent40", "real agent-40, stop removed"), ("nocap-agent33", "real agent-33, stop removed"), ("nocap-agent1", "real agent-1, stop removed"), ("nocap-greedy", "greedy, stop removed"), ("nocap-starter", "starter, stop removed")]),
    "effect_points": round(eff_nocap, 2),
    "fix_tested": f"two: linear 3418..92304 moves agent-10 by +{eff_rescale:.2f} and keeps order; removing the tester's undocumented 2*N*N stop on the same anchors moves it by +{eff_nocap:.2f} and reorders real runs (agent-1 below agent-10 under the cap, 91007 vs about 92040 raw; above its best run without it, 164473 vs 158357)",
    "correct_work_keeps_score": "no, every scale change moves scores up; invalid stays 0, starter stays 0, and greedy keeps 3.04 with the stop removed (it never reaches the cap)",
    "job": "evidence/runs/community9-treant_forest-a", "table_script": "evidence/scripts/second_review/c9_treant_forest_table.py",
    "note": "Real runs do reach the ceiling: all 87 archived reports (53 files) sit at 20.46-21.02 and the stop binds 47-50 of 50 cases, so the cap hides real differences; weakest point: the four measured runs read the destination list from stdin (a text match finds it in all 53 files) although the README says solutions read only the grid (a grid-only greedy never reaches the cap, 3.04), replay of the longest uncapped case hits the tester's 60 s limit in some repeats, and the choice of fix is discretionary."}]}
json.dump(out, open(".internal/upstream-sweep/container/treant_forest.json", "w"), indent=1)
