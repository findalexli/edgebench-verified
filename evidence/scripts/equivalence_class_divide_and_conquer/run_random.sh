#!/usr/bin/env bash
# For each random small case: TRUE_COST from instrumented checker; then the original
# checker (W parameterised via env, nothing else changed) at W = oracle predicted count,
# W = predicted-1, and W = true_cost-1. Prints: name true acc@pred acc@pred-1 acc@true-1 (0=accept)
set -uo pipefail
I=seededge/edgebench.judge.equivalence_class_divide_and_conquer@sha256:f793d805d7e2adcec68355343230db3ea15b1010a98678850d2fe89e9ba767e6
HERE=$(cd "$(dirname "$0")" && pwd)
timeout 1200 docker run --rm --network none --memory 2g --cpus 2 -v "$HERE:/audit:ro" $I bash -c '
P=/opt/p2_judge/prob; T=$P/P2/T3_P8204/data
g++ -std=c++17 -Ofast -pipe -I $P -I $T /audit/checker_true_cost.cpp -o /tmp/chk_true
g++ -std=c++17 -Ofast -pipe -I $P -I $T "-DAUDIT_W=atoll(getenv(\"AUDIT_W\"))" /audit/checker_original_paramW.cpp -o /tmp/chk_w
python3 - <<PY
import json, subprocess, re
o = json.load(open("/audit/random_cases/oracle.json"))
for name, v in sorted(o.items()):
    f = "/audit/random_cases/" + name
    args = [f + ".in", f + ".out", f + ".ans"]
    r = subprocess.run(["/tmp/chk_true"] + args, capture_output=True, text=True)
    tc = re.search(r"TRUE_COST (-?\d+)", r.stderr).group(1)
    def acc(W):
        return str(subprocess.run(["/tmp/chk_w"] + args, capture_output=True, env={"AUDIT_W": str(W)}).returncode)
    p = v["predicted_original_count"]
    print(name, tc, acc(p), acc(p - 1), acc(v["true_cost"] - 1))
PY'
