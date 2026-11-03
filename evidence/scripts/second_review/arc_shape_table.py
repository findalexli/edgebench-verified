#!/usr/bin/env python3
"""Scores from evidence/runs/community8-arc_shape: real Opus agent-36 on the current judge, as submitted and as an array."""
import glob, json, os, re
for f in sorted(glob.glob("evidence/runs/community8-arc_shape/result/out/g/*.json")):
    d = json.load(open(f))
    print(os.path.basename(f), d["raw_score"], d["valid"], d["summary"], re.findall(r"round2-type-system\s+\d+ /\s+\d+", str(d.get("log_tail")))[-1:])
