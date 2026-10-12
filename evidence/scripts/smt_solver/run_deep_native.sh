#!/bin/sh
# Deepest hidden SAT case (paren depth 2621): original evaluator accepts an offline-computed witness.
D=$(cd "$(dirname "$0")" && pwd)
IMG=seededge/edgebench.judge.smt_solver@sha256:2bf3482a5b2952eeadecf16e33041c13c284b7ce5d93f3491b7cfd5088d91fc6
timeout 600 docker run --rm --network none --memory 2g --cpus 2 -v "$D/native_deep:/nc:ro" "$IMG" bash -c '
cp -r /nc/bench /tmp/hb && python3 -c "import zipfile,json; z=zipfile.ZipFile(\"/home/workspace/smt_judge/SMT-hidden_benchmarks.zip\"); [z.extract(k,\"/tmp/hb\") for k in json.load(open(\"/tmp/hb/expected_answers.json\"))]" && cp -r /nc/sub /tmp/sub && cd /tmp/sub &&
python3 /home/workspace/smt_judge/scripts/evaluate.py --solver ./solve --benchmarks /tmp/hb --expected /tmp/hb/expected_answers.json --manifest /tmp/hb/selection_manifest.json --timeout 60 --parallel 2 --perturb --perturb-salt hidden-sebench --submission-root /tmp/sub --output /tmp/out.json >/dev/null;
python3 -c "
import json; d=json.load(open(\"/tmp/out.json\"))
for l in d[\"results\"].values():
  for r in l: print(r[\"benchmark\"], r[\"answer\"], r[\"verdict\"], (r.get(\"model_error\") or \"\")[:120])"'
