#!/usr/bin/env python3
"""Repeat gradings of one file on the current DCSS judge (old) and on the same judge with _dismiss_loop sending no keys (new). Reads report.json and judge_output.txt."""
import glob, json, os, re, statistics as st
for job, arm in (("evidence/runs/community9-dcss_dungeon_ai-old", "old, keys injected"), ("evidence/runs/community9-dcss_dungeon_ai-nokeys", "new, no injected keys")):
    rows = {}
    for f in sorted(glob.glob(job + "/result/out/sf/runs/*/dcss_dungeon_ai/submissions/manual-1/report.json")):
        label = f.split("/runs/")[-1].split("/")[0]
        m = re.match(r"(\w+)-(\d+)-(old|new)", label)
        d = json.load(open(f))
        out = open(os.path.dirname(f) + "/judge_output.txt", errors="replace").read()
        games = [int(x) for x in re.findall(r"^CASE \d+ \S+ score=(\d+)", out, re.M)]
        rows.setdefault(m.group(1), []).append((int(m.group(2)), d["score"], d["score_0_100"], d["valid"], round(d["runtime_seconds"]), games, d["timed_out"]))
    print("==", arm, job)
    for w, v in sorted(rows.items()):
        v.sort()
        s = [x[2] for x in v]
        print(f"{w} n={len(s)} normalized {[round(x,3) for x in s]} raw {[x[1] for x in v]} spread={max(s)-min(s):.3f} mean={st.mean(s):.3f} all_valid={all(x[3] for x in v)} timed_out={sum(bool(x[6]) for x in v)}")
        for x in v:
            print(f"   run {x[0]} games={x[5]} runtime={x[4]}s")
        print(f"   gradings with all 5 games equal to the first: {sum(v[0][5] == x[5] for x in v[1:])}/{len(v)-1}")
