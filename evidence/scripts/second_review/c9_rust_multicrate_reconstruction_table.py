#!/usr/bin/env python3
"""community9 rust_multicrate_reconstruction: real submissions and the reference on the current judge, one change at a time.
old/nff/ex: official 4 CPU; old8/cc8/ccnff8: 8 vCPU with CARGO_BUILD_JOBS=8."""
import json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from c9_table_lib import load, show, arms, mean
J = ["smoke", "a", "b", "cc-a", "cc-b", "cc-c", "cc-d"]
rows = load([f"community9-rust_multicrate_reconstruction-{j}" for j in J])
show(rows)
print("\nnonzero crates (passed/total), first repeat:")
for arm in sorted(rows):
    m = rows[arm][0]["result"].get("metrics") or {}
    print(f"{arm:22s}", m.get("score_status"), {c["crate"][4:]: (c["status"][:5], c["passed"], c["total"]) for c in m.get("crates", []) if c["passed"] or c["crate"] in ("cas-search", "cas-cli")})

R = json.load(open(".internal/upstream-sweep/round3/rust_multicrate_reconstruction.json"))["claims"]
T = "evidence/scripts/second_review/c9_rust_multicrate_reconstruction_table.py"
d = lambda a, b: mean(rows, a) - mean(rows, b)
best = "best real run 17.20, unchanged by the claim's size"
c1 = dict(claim=R[0]["claim"], verdict="CONFIRMED_SMALL", witness="real unchanged: agent-1, auto-8, agent-5; starter as the no-work control",
    arms=arms(rows, [("old-agent1", "real agent-1, current judge"), ("nff-agent1", "real agent-1, --no-fail-fast"), ("old-auto8", "real auto-8, current judge"), ("nff-auto8", "real auto-8, --no-fail-fast"),
                     ("old-agent5", "real agent-5, current judge"), ("nff-agent5", "real agent-5, --no-fail-fast"), ("old-starter", "starter, current judge"), ("nff-starter", "starter, --no-fail-fast"),
                     ("cc8-agent5", "real agent-5, cc files restored"), ("ccnff8-agent5", "real agent-5, cc files restored and --no-fail-fast")]),
    effect_points=round(d("nff-agent1", "old-agent1"), 4),
    fix_tested=f"old vs --no-fail-fast, same files: agent-1 {mean(rows,'old-agent1'):.4f} -> {mean(rows,'nff-agent1'):.4f}, auto-8 {mean(rows,'old-auto8'):.4f} -> {mean(rows,'nff-auto8'):.4f}, agent-5 {mean(rows,'old-agent5'):.4f} -> {mean(rows,'nff-agent5'):.4f}; with cc files restored agent-5 {mean(rows,'cc8-agent5'):.4f} -> {mean(rows,'ccnff8-agent5'):.4f}",
    correct_work_keeps_score="yes: no score falls; every arm rises and is exact across repeats",
    job="evidence/runs/community9-rust_multicrate_reconstruction-a and -b, -cc-d", table_script=T,
    note=f"Real and exactly repeatable but below 1 point on every real file ({best}), even with cc restored (+{d('ccnff8-agent5','cc8-agent5'):.2f}); weakest point: the no-work starter gains as much as agent-1 (+{d('nff-starter','old-starter'):.3f}), so it does not separate work.")
c2 = dict(claim=R[1]["claim"], verdict="CONFIRMED_SMALL", witness="real unchanged: agent-5 (trigger); agent-1 and the starter as controls where the excused test really fails",
    arms=arms(rows, [("old-agent5", "real agent-5, current judge"), ("ex-agent5", "real agent-5, exact FAILED check"), ("old-agent1", "control: real agent-1, current judge"), ("ex-agent1", "control: real agent-1, exact FAILED check"), ("old-starter", "control: starter, current judge"), ("ex-starter", "control: starter, exact FAILED check")]),
    effect_points=round(d("ex-agent5", "old-agent5"), 4),
    fix_tested=f"old vs exact FAILED match: agent-5 {mean(rows,'old-agent5'):.4f} -> {mean(rows,'ex-agent5'):.4f} (cas-pty 10/11 -> 9/11); agent-1 {mean(rows,'old-agent1'):.4f} -> {mean(rows,'ex-agent1'):.4f}; starter {mean(rows,'old-starter'):.4f} -> {mean(rows,'ex-starter'):.4f}",
    correct_work_keeps_score="yes: controls where the excused test fails are unchanged; the fix lowers only the wrongly credited file",
    job="evidence/runs/community9-rust_multicrate_reconstruction-a and -b, -smoke", table_script=T,
    note="Measured on the best real run, exact in 3 of 3 repeats, but worth 0.10 of 100 and capped at 4/40 by construction; weakest point: only agent-5 of the 9 distinct real files was graded as a trigger, and the fix removes credit rather than adding it.")
c3 = dict(claim=R[2]["claim"], verdict="CONFIRMED", witness="real unchanged: agent-5; synthetic: reference (upstream CAS v1.0.0 bodies, hidden tests removed); starter as the no-work control",
    arms=arms(rows, [("old8-agent5", "real agent-5, current judge"), ("cc8-agent5", "real agent-5, cc files restored"), ("old8-reference", "reference, current judge"), ("cc8-reference", "reference, cc files restored"), ("old8-starter", "starter, current judge"), ("cc8-starter", "starter, cc files restored")]),
    effect_points=round(d("cc8-agent5", "old8-agent5"), 4),
    fix_tested=f"old vs build_vendor.py writing the 4 files (checksums match 4 of 4), same files: agent-5 {mean(rows,'old8-agent5'):.4f} -> {mean(rows,'cc8-agent5'):.4f}, reference {mean(rows,'old8-reference'):.4f} -> {mean(rows,'cc8-reference'):.4f}, starter {mean(rows,'old8-starter'):.4f} -> {mean(rows,'cc8-starter'):.4f}",
    correct_work_keeps_score="yes: all rise, agent-5 by 9.97 and the reference by 46.38, while the no-work starter gains only 2.35",
    job="evidence/runs/community9-rust_multicrate_reconstruction-cc-a, -cc-b, -cc-c", table_script=T,
    note="No blind spot here: no real run beats the block (best archived 17.20, NOTES' historical best 27.37, a complete solution 27.61 as shipped); weakest point: upstream already documents this as Known issue 1 and keeps it for comparability, arms ran at 8 vCPU with CARGO_BUILD_JOBS=8 (old-judge scores equal the official 4 CPU ones), and cas-search and cas-cli still fail to compile with the files restored, capping the reference at 73.99.")
json.dump({"task": "rust_multicrate_reconstruction", "claims": [c1, c2, c3]}, open(".internal/upstream-sweep/container/rust_multicrate_reconstruction.json", "w"), indent=1)
