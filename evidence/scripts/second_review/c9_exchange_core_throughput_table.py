#!/usr/bin/env python3
"""Exchange core: real agent-12 and its variants on the old and fixed judge. Reads sforge reports from the job results."""
import glob, json, re, sys
rows = {}
for job in sys.argv[1:] or ["community9-exchange_core_throughput-smoke", "community9-exchange_core_throughput-a2", "community9-exchange_core_throughput-b", "community9-exchange_core_throughput-c"]:
    for f in sorted(glob.glob(f"evidence/runs/{job}/result/out/sf/runs/*/*/submissions/*/report.json")):
        d = json.load(open(f))
        run = f.split("/")[-5]
        m = re.match(r"(\w+)-[ps]\d+-(old|new)", run)
        out = open(f.replace("report.json", "judge_output.txt")).read()
        case = (re.findall(r"^CASE 0000 (\w+)", out, re.M) or ["?"])[0]
        rows.setdefault((job.split("-")[-1], m.group(1), m.group(2)), []).append((d["score"], round(d["score_0_100"] or 0, 2), case, "GATE OK" in out))
print("| job | arm | judge | n | raw | score 0-100 | case | gate ok |")
print("|---|---|---|---|---|---|---|---|")
for k, v in sorted(rows.items()):
    print(f"| {k[0]} | {k[1]} | {k[2]} | {len(v)} | {[x[0] for x in v]} | {[x[1] for x in v]} | {sorted(set(x[2] for x in v))} | {sum(x[3] for x in v)} |")
