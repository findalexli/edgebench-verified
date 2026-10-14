#!/usr/bin/env python3
"""One-line summary of a runner_judge.py stdout: raw score, normalized (linear 0..100), status,
roundtrip pass rate, per-dataset S_i."""
import json, sys
try:
    t = open(sys.argv[1]).read()
    s = json.loads(t[t.index(">>>>> Start Structured Result") + 29:t.index(">>>>> End")])
    m = s["metrics"]; raw = float(s["score"])
    norm = max(0.0, min(100.0, 100.0 * (raw - 0.0) / (100.0 - 0.0)))
    pd = m.get("per_dataset", [])
    ok = sum(1 for x in pd if x.get("roundtrip_ok") and not x.get("error"))
    per = " ".join(f"{x['name']}={x['score']:.3f}" for x in pd)
    print(f"raw={raw:.4f} norm={norm:.4f} status={m.get('status')} valid={s.get('valid')} pass={ok}/{len(pd) or m.get('num_cases')} [{per}] base={m.get('baseline_source','stored baseline_results.json')}")
except Exception as e:  # noqa: BLE001
    print(f"unparsed ({type(e).__name__}: {e})")
