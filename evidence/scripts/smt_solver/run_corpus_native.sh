#!/bin/sh
# Hidden cases are extracted at run time from the image's own SMT-hidden_benchmarks.zip.
# Original judge-image evaluator, official flags, on two real hidden cases with z3-derived witnesses.
D=$(cd "$(dirname "$0")" && pwd)
IMG=seededge/edgebench.judge.smt_solver@sha256:2bf3482a5b2952eeadecf16e33041c13c284b7ce5d93f3491b7cfd5088d91fc6
for TAG in A B C; do
timeout 600 docker run --rm --network none --memory 2g --cpus 2 -e WITNESS_TAG=$TAG -v "$D/native_corpus:/nc:ro" "$IMG" bash -c '
cp -r /nc/bench /tmp/hb && python3 -c "import zipfile,json; z=zipfile.ZipFile(\"/home/workspace/smt_judge/SMT-hidden_benchmarks.zip\"); [z.extract(k,\"/tmp/hb\") for k in json.load(open(\"/tmp/hb/expected_answers.json\"))]" && cp -r /nc/sub /tmp/sub && cd /tmp/sub &&
python3 /home/workspace/smt_judge/scripts/evaluate.py --solver ./solve --benchmarks /tmp/hb --expected /tmp/hb/expected_answers.json --manifest /tmp/hb/selection_manifest.json --timeout 60 --parallel 2 --perturb --perturb-salt hidden-sebench --submission-root /tmp/sub --output /tmp/out.json >/dev/null &&
python3 -c "
import json,os; d=json.load(open(\"/tmp/out.json\"))
for l in d[\"results\"].values():
  for r in l: print(os.environ[\"WITNESS_TAG\"], r[\"benchmark\"], r[\"answer\"], r[\"verdict\"], (r.get(\"model_error\") or \"\")[:90])"'
done
