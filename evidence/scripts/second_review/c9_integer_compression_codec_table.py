#!/usr/bin/env python3
"""community9 integer_compression_codec: stored bpi anchors vs the starter's exact bpi plus the 1..320 scale; per-dataset effects from each graded run."""
import json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from c9_table_lib import load, show, arms, mean
rows = load(["community9-integer_compression_codec-smoke", "community9-integer_compression_codec-a"])
show(rows)
print("\nper dataset, starter on each judge (documented S_i = 1.0 everywhere):")
for arm in ["old-starter", "new-starter"]:
    pd = rows[arm][0]["result"]["metrics"]["per_dataset"]
    print(arm, {x["name"]: round(x["score"], 3) for x in pd}, "max/min", round(max(x["score"] for x in pd) / min(x["score"] for x in pd), 2))
print("\nbpi identical across repeats and judges:")
for sub in ["top", "starter", "flipA", "flipB"]:
    s = {tuple(x["encoded_bytes"] for x in r["result"]["metrics"]["per_dataset"]) for a in (f"old-{sub}", f"new-{sub}") for r in rows[a]}
    print(sub, "distinct size vectors", len(s), "repeats", len(rows[f"old-{sub}"]) + len(rows[f"new-{sub}"]))
A, B = "flipA", "flipB"
print("\norder of the pair on each judge, raw:")
for side in ("old", "new"):
    a = [r["raw"] for r in rows[f"{side}-{A}"]]; b = [r["raw"] for r in rows[f"{side}-{B}"]]
    print(side, "A", [round(x, 3) for x in a], "B", [round(x, 3) for x in b], "mean diff A-B", round(sum(a)/len(a) - sum(b)/len(b), 3), "A always above" if min(a) > max(b) else "B always above" if min(b) > max(a) else "overlap")
    print("  normalized means", round(mean(rows, f"{side}-{A}"), 3), round(mean(rows, f"{side}-{B}"), 3))

R = json.load(open(".internal/upstream-sweep/round3/integer_compression_codec.json"))["claims"]
c = [x for x in R if x["verdict"] in ("HOLDS", "NEEDS_CONTAINER")]
assert len(c) == 1
top_old = mean(rows, "old-top"); top_new = mean(rows, "new-top"); top_raw = mean(rows, "new-top", "raw")
st_old = mean(rows, "old-starter", "raw"); st_new = mean(rows, "new-starter", "raw")
clip = min(top_raw, 100.0)
print(f"\ntop real: current {top_old:.2f}; corrected bpi raw {top_raw:.2f}, which the task's 0..100 scale clips to {clip:.0f}; on 1..320 {top_new:.2f}")
print(f"starter raw: current {st_old:.4f}; corrected bpi {st_new:.4f}; documented 1.0")
out = {"task": "integer_compression_codec", "claims": [dict(
    claim=c[0]["claim"], verdict="CONFIRMED", witness="real unchanged: auto-1 (byte-identical to the public starter), r2 agent-15, auto-3, r2 auto-5; bad control: auto-1 with one corrupted value",
    arms=arms(rows, [("old-starter", "real starter, current judge"), ("new-starter", "real starter, corrected bpi, 1..320"), ("old-top", "real agent-15, current judge"), ("new-top", "real agent-15, corrected bpi, 1..320"),
                     ("old-flipA", "real auto-3, current judge"), ("new-flipA", "real auto-3, corrected bpi, 1..320"), ("old-flipB", "real r2 auto-5, current judge"), ("new-flipB", "real r2 auto-5, corrected bpi, 1..320"),
                     ("old-bad", "bad control: corrupted starter, current judge"), ("new-bad", "bad control, corrected bpi, 1..320")]),
    effect_points=round(top_new - top_old, 2),
    fix_tested=f"old vs new on the same files, interleaved, n>=3: starter raw {st_old:.3f} -> {st_new:.3f} (documented 1.0; the remainder is the stored throughput anchors, not changed); agent-15 {top_old:.2f} -> {top_new:.2f} on 1..320, raw {top_raw:.1f}, which the unchanged 0..100 scale would clip to 100; corrupted codec 0 on both",
    correct_work_keeps_score=f"no: agent-15 {top_old:.2f} -> {top_new:.2f} on 1..320, or 100 on the unchanged scale; order of the tested pair does not flip beyond throughput noise",
    job="evidence/runs/community9-integer_compression_codec-a", table_script="evidence/scripts/second_review/c9_integer_compression_codec_table.py",
    note="Measured: the starter gets 0.25 raw against the documented 1.0 and per-dataset S_i of 0.08-0.63 against 1.0, on every run; blind spot: this is not a ceiling, a real run reaches 73.78, and the 3 flips the archive suggested did not repeat for the pair tested (auto-3 vs r2 auto-5 overlap on both judges) with no flip among repeated files, so the weighting change has no shown ranking effect and the size of the score move depends on the scale chosen.")]}
json.dump(out, open(".internal/upstream-sweep/container/integer_compression_codec.json", "w"), indent=1)
