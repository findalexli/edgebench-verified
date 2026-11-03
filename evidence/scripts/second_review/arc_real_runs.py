#!/usr/bin/env python3
"""Best in-run score per real Opus arc_compiler_runtime run, from each submission's report.json and run_history.json."""
import glob, json
for v in ("v1", "v2"):
    base = f"evidence/runs/claude-opus-arc_compiler_runtime-{v}/result/out/sforge-logs/runs/*/arc_compiler_runtime"
    rep = []
    for f in glob.glob(base + "/submissions/*/report.json"):
        d = json.load(open(f))
        if d.get("score") is not None and d.get("valid"):
            rep.append((d["score"], f.split("/")[-2]))
    h = json.load(open(glob.glob(base + "/run_history.json")[0]))
    ent = [(e.get("score"), e.get("round")) for e in h.get("entries", []) if e.get("score") is not None]
    print(v, "reports", len(rep), "max", max(rep), "| history", {k: h.get(k) for k in ("best_score", "best_round")}, "max entry", max(ent) if ent else None)
    a = [x for x in rep if x[1] in ("agent-36", "agent-16", "agent-85")]
    print("  named", sorted(a), [e for e in ent if e[1] in ("agent-36", "agent-16", "agent-85")])
