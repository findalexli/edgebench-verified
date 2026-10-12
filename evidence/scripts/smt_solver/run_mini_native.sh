#!/bin/sh
# Runs the original judge-image evaluator (official flags) on the mini audit cases.
D=$(cd "$(dirname "$0")" && pwd)
IMG=seededge/edgebench.judge.smt_solver@sha256:2bf3482a5b2952eeadecf16e33041c13c284b7ce5d93f3491b7cfd5088d91fc6
timeout 300 docker run --rm --network none --memory 2g --cpus 2 -v "$D/mini:/mini:ro" "$IMG" bash -c '
cp -r /mini/bench /tmp/hb && cp -r /mini/sub /tmp/sub && cd /tmp/sub && ./build.sh &&
python3 /home/workspace/smt_judge/scripts/evaluate.py --solver ./solve --benchmarks /tmp/hb --expected /tmp/hb/expected_answers.json --manifest /tmp/hb/selection_manifest.json --timeout 60 --parallel 2 --perturb --perturb-salt hidden-sebench --submission-root /tmp/sub --output /tmp/out.json >/dev/null &&
python3 -c "
import json; d=json.load(open(\"/tmp/out.json\"))
for r in d[\"results\"][\"QF_UF\"]: print(r[\"benchmark\"], r[\"verdict\"], r[\"model_error\"])
print(\"final_score\", d[\"final_score\"])"'
