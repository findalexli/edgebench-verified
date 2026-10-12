#!/usr/bin/env python3
"""Compare the shipped score (stored baseline constants) with the documented score
(baseline = the shipped Varint starter measured on the same host).
usage: rescore_documented.py starter_stdout candidate_stdout baseline_results.json"""
import json, sys
def load(p):
    t = open(p).read()
    s = t[t.index(">>>>> Start Structured Result") + 29:t.index(">>>>> End")]
    return {x["name"]: x for x in json.loads(s)["metrics"]["per_dataset"]}
st, ca = load(sys.argv[1]), load(sys.argv[2])
stored = {x["name"]: x for x in json.load(open(sys.argv[3]))["per_dataset"]}
W = {"docids": 2, "ts_sec": 1.5, "ts_ns": 1.5, "temp": 1, "grid": 1, "zipf": 1, "rand": 1, "sparse": 1}
bpi = lambda x: x["encoded_bytes"] * 8 / x["n"]
def score(c, base_bpi, base_gbps):
    tot = 0
    for k, w in W.items():
        x = c[k]
        if not x["roundtrip_ok"]:
            continue
        tot += w * min(base_bpi[k] / bpi(x), 8) * min(x["decode_gbps"] / base_gbps[k], 40)
    return tot / sum(W.values())
doc_bpi = {k: bpi(st[k]) for k in W}; doc_gbps = {k: st[k]["decode_gbps"] for k in W}
sto_bpi = {k: stored[k]["bpi"] for k in W}; sto_gbps = {k: stored[k]["decode_gbps"] for k in W}
print("dataset  true-varint-bpi stored-bpi  k_bpi=stored/true   true-gbps stored-gbps")
for k in W:
    print(f"{k:8s} {doc_bpi[k]:8.2f} {sto_bpi[k]:10.2f} {sto_bpi[k]/doc_bpi[k]:10.3f} {doc_gbps[k]:12.3f} {sto_gbps[k]:8.2f}")
print("starter   shipped score %.4f   documented score %.4f" % (score(st, sto_bpi, sto_gbps), score(st, doc_bpi, doc_gbps)))
print("candidate shipped score %.4f   documented score %.4f" % (score(ca, sto_bpi, sto_gbps), score(ca, doc_bpi, doc_gbps)))
