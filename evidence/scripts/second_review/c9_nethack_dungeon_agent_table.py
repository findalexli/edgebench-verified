#!/usr/bin/env python3
"""Repeat gradings of one file on the current NetHack judge (old) and on the judge with core seeding (new). Reads report.json and judge_output.txt."""
import glob, json, os, re, statistics as st, sys
JOB = sys.argv[1] if len(sys.argv) > 1 else "evidence/runs/community9-nethack_dungeon_agent"
rows = {}
for f in sorted(glob.glob(JOB + "/result/out/sf/runs/*/nethack_dungeon_agent/submissions/manual-1/report.json")):
    label = f.split("/runs/")[-1].split("/")[0]
    m = re.match(r"(\w+)-(\d+)-(old|new)", label)
    d = json.load(open(f))
    cases = [int(x) for x in re.findall(r"^CASE \S+ \S+ score=(\d+)", open(os.path.dirname(f) + "/judge_output.txt").read(), re.M)]
    rows.setdefault((m.group(1), m.group(3)), []).append((int(m.group(2)), d["score"], d["score_0_100"], d["valid"], d["runtime_seconds"], cases, d.get("timed_out")))
for (w, sd), v in sorted(rows.items()):
    v.sort()
    s = [x[2] for x in v]
    print(f"{w} {sd} n={len(s)} normalized {[round(x,3) for x in s]}")
    print(f"  mean={st.mean(s):.3f} min={min(s):.3f} max={max(s):.3f} spread={max(s)-min(s):.3f} sd={st.pstdev(s) if len(s)<2 else st.stdev(s):.3f} all_valid={all(x[3] for x in v)} timed_out={sum(bool(x[6]) for x in v)} runtime_max={max(x[4] for x in v):.0f}s")
    same_rep = sum(c[i] == c[i + 1] for x in v for c in [x[5]] for i in range(0, len(c) - 1, 2))
    tot = sum(len(x[5]) // 2 for x in v)
    print(f"  repeat pairs (same seed, repeat 0 vs 1) with equal score: {same_rep}/{tot}")
    if len(v) > 1:
        ident = sum(v[0][5] == x[5] for x in v[1:])
        print(f"  gradings whose 20 game scores equal the first grading's: {ident}/{len(v)-1}")
fp = JOB + "/result/out/d/fix-seed0-starter.txt"
if os.path.exists(fp):
    print("fix judge, --run-seed 0 three times, starter:", open(fp).read().strip().replace("\n", " | "))
