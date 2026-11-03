#!/usr/bin/env python3
"""Replay archived Opus integer_compression_codec reports under the stored anchors and under starter-measured
compression anchors (sizes are deterministic; archived throughput kept). Counts ordering flips among real submissions,
keeping only pairs whose order flips by more than the larger same-file spread seen in the archive."""
import glob, hashlib, json, os, itertools, sys
T = "integer_compression_codec"
ROOT = "evidence/runs/"
B = json.load(open(sys.argv[1]))  # baseline_results.json of upstream
base = {d["name"]: d for d in B["per_dataset"]}
rows = {}
for a in sorted(glob.glob(ROOT + f"claude-opus-{T}*/result/out/sforge-logs/runs/*/{T}/submissions/*/submission.tar.gz")):
    rp = a.replace("submission.tar.gz", "report.json")
    if not os.path.exists(rp): continue
    d = json.load(open(rp))
    m = d.get("metrics") or {}
    if m.get("status") != "ok": continue
    sha = hashlib.sha256(open(a, "rb").read()).hexdigest()[:10]
    r = rows.setdefault(sha, {"sub": a.split("/")[-2], "run": a.split("/")[2], "reps": []})
    r["reps"].append(m["per_dataset"])
starter = None
for sha, r in rows.items():
    if abs(r["reps"][0][1]["encoded_bytes"] * 8 / r["reps"][0][1]["n"] - 40.0) < 1e-6: starter = r["reps"][0]
anch = {x["name"]: x["encoded_bytes"] * 8 / x["n"] for x in starter}
print("starter measured bpi vs stored:", {k: (round(v, 3), base[k]["bpi"]) for k, v in anch.items()})
def score(pd, a):
    tw = sum(x["weight"] for x in pd); s = 0
    for x in pd:
        if not x.get("roundtrip_ok") or x.get("error"): continue
        bpi = x["encoded_bytes"] * 8 / max(x["n"], 1)
        s += x["weight"] * min(a[x["name"]] / max(bpi, 1e-9), 8) * min(x["decode_gbps"] / base[x["name"]]["decode_gbps"], 40)
    return s / tw
old = {k: v["bpi"] for k, v in base.items()}
res = []
for sha, r in rows.items():
    so = [score(p, old) for p in r["reps"]]; sn = [score(p, anch) for p in r["reps"]]
    res.append(dict(sha=sha, sub=r["sub"], run=r["run"], n=len(so), old=sum(so)/len(so), new=sum(sn)/len(sn), so=so, sn=sn, nw=(sum(sn)/len(sn)-1)/319*100))
res.sort(key=lambda x: -x["old"])
for x in res: print(x["sha"], x["run"].replace("claude-opus-integer_compression_codec", "orig"), x["sub"], "n", x["n"], "old %.3f" % x["old"], "newraw %.3f" % x["new"], "new_1_320 %.3f" % x["nw"])
spread = max((max(x["so"]) - min(x["so"]) for x in res), default=0)
flips = 0; robust = []
for a, b in itertools.combinations(res, 2):
    if (a["old"] - b["old"]) * (a["new"] - b["new"]) < 0:
        flips += 1
        # keep flips where in BOTH scales every repeat of one beats every repeat of the other
        if min(a["so"]) > max(b["so"]) and max(a["sn"]) < min(b["sn"]): robust.append((a["sha"], a["run"].replace("claude-opus-integer_compression_codec", "orig"), a["sub"], a["n"], b["sha"], b["run"].replace("claude-opus-integer_compression_codec", "orig"), b["sub"], b["n"], round(a["old"]-b["old"], 3), round(a["new"]-b["new"], 3)))
print("pairs", len(res)*(len(res)-1)//2, "flips", flips, "robust(all repeats separated in both scales)", len(robust))
for x in sorted(robust, key=lambda r: -abs(r[8]))[:15]: print(x)
strict = [x for x in robust if x[3] >= 2 and x[7] >= 2]
print("flips where both files have n>=2 repeats and all repeats separate in both scales:", len(strict), strict[:5])
