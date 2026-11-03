#!/usr/bin/env python3
"""Repeat gradings of one file on the current Wesnoth judge. Reads report.json and judge_output.txt."""
import glob, json, os, re, statistics as st, sys
JOB = sys.argv[1] if len(sys.argv) > 1 else "evidence/runs/community9-wesnoth_tactical_ai"
rows = {}
for f in sorted(glob.glob(JOB + "/result/out/sf/runs/*/wesnoth_tactical_ai/submissions/manual-1/report.json")):
    label = f.split("/runs/")[-1].split("/")[0]
    m = re.match(r"(\w+)-(\d+)-(old|new)", label)
    d = json.load(open(f))
    out = open(os.path.dirname(f) + "/judge_output.txt").read()
    games = re.findall(r"^CASE \d+ (OK|WA) score=\d  # (\S+) seed=(\d+) repeat=(\d) turns=(\d+)( timeout=1)?", out, re.M)
    rows.setdefault(m.group(1), []).append((int(m.group(2)), d["score_0_100"], d["valid"], d["runtime_seconds"], games, d["timed_out"], re.search(r"TIMEOUT_COUNT (\d+)", out).group(1) if "TIMEOUT_COUNT" in out else None))
for w, v in sorted(rows.items()):
    v.sort()
    s = [x[1] for x in v]
    print(f"{w} n={len(s)} normalized {s}")
    print(f"  mean={st.mean(s):.2f} min={min(s)} max={max(s)} spread={max(s)-min(s)} sd={st.stdev(s) if len(s)>1 else 0:.2f} all_valid={all(x[2] for x in v)} judge_timed_out={sum(bool(x[5]) for x in v)} game_timeouts={[x[6] for x in v]} runtime_s={[round(x[3]) for x in v]}")
    print(f"  wins per grading={[sum(g[0]=='OK' for g in x[4]) for x in v]} games per grading={[len(x[4]) for x in v]}")
    pairs = tot = 0
    for x in v:
        by = {(g[1], g[2], g[3]): (g[0], g[4]) for g in x[4]}
        for (mp, sd, r), val in by.items():
            if r == "0":
                tot += 1
                pairs += by.get((mp, sd, "1")) == val
    print(f"  repeat pairs (same map, seed) with equal outcome and turns: {pairs}/{tot}")
    if len(v) > 1:
        base = {(g[1], g[2], g[3]): (g[0], g[4]) for g in v[0][4]}
        agree = [sum(({(g[1], g[2], g[3]): (g[0], g[4]) for g in x[4]}.get(k) == val) for k, val in base.items()) for x in v[1:]]
        print(f"  games identical to the first grading (of {len(base)}): {agree}")
