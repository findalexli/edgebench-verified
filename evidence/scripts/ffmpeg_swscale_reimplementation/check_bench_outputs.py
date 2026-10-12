#!/usr/bin/env python3
"""Apply the ORIGINAL correctness check (compute_reward.check_correctness, PSNR thresholds)
to the 10 timed benchmark workloads, which the original scorer times but never validates.
Run inside the judge image: python3 check_bench_outputs.py <candidate.so>"""
import random, sys, json
sys.path.insert(0, "/opt/tests")
import compute_reward as cr
cand = cr.load_swscale_library(sys.argv[1])
base = cr.load_swscale_library("/verifier-data/libswscale_baseline.so")
rng = random.Random(0xDEADBEEF_CAFEBABE)
cr.sample_correctness_workloads(rng)          # advance the RNG exactly as _run_scoring does
bench = cr.sample_benchmark_workloads(rng)
ok, results = cr.check_correctness(cand, base, bench)
for r in results:
    print(json.dumps(r, ensure_ascii=False))
print("all_benchmark_workloads_pass:", ok)
