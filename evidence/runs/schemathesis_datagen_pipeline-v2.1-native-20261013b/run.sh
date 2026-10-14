#!/bin/bash
# Datagen v2.1 clean rerun (issue #47): six arms (3 header-overlay variants x original/v2.1).
# The v2.1 judge image is built in the worker from the committed package: materialize.sh (pull the
# pinned image, extract, apply repair.patch, verify sha256) and docker build. Each arm runs the task's
# original judge.eval_cmd (datagen-eval.sh, sha256 4764bae1...) as in run_native.sh lines 12-23.
set -uo pipefail
cd /job; mkdir -p out
D=seededge/edgebench.judge.schemathesis_datagen_pipeline@sha256:16b21364d67906d802e24d0b3b4505c42a6ac0f91cd5b382bb4c9d1d20224d37
{ nproc; free -m; df -h /; docker version --format '{{.Server.Version}}'; date -u; } > out/env.txt 2>&1
sha256sum datagen-eval.sh headers_overlay.py pkg-datagen/* > out/input-sha256.txt
timeout 300 docker pull "$D" >out/pull-datagen.log 2>&1 || { echo pull-failed | tee -a out/summary.txt; exit 2; }
command -v patch >/dev/null || { (apt-get update -qq && apt-get install -y -qq patch) > out/apt.log 2>&1; }
( cd pkg-datagen && bash materialize.sh ) > out/materialize-datagen.log 2>&1 || { echo materialize-failed | tee -a out/summary.txt; exit 4; }
sha256sum pkg-datagen/files/tests/test_01_header_strategies.py > out/v2.1-test-sha256.txt
timeout 300 docker build -t ebv/datagen:v2.1 pkg-datagen >out/build-datagen.log 2>&1 || { echo build-failed | tee -a out/summary.txt; exit 3; }
docker image inspect "$D" ebv/datagen:v2.1 --format '{{.Id}} {{.RepoTags}}' >out/images.txt
docker run --rm --network none --entrypoint sha256sum ebv/datagen:v2.1 /tests/test_01_header_strategies.py >> out/v2.1-test-sha256.txt 2>&1
fail=0
for variant in stdlib_1900 stdlib_any_year garbage_shape; do
 for revision in original candidate; do
  image=$D; [ "$revision" = original ] || image=ebv/datagen:v2.1
  name=datagen-$variant-$revision; mkdir -p out/$name
  t0=$SECONDS
  timeout 180 docker run --rm --memory 4g --cpus 2 --network none -e EBV_DATE_VARIANT="$variant" -v /job:/job:ro -v /job/out/$name:/out "$image" bash -c 'cp /job/headers_overlay.py /app/src/schemathesis/specs/openapi/headers.py; bash /job/datagen-eval.sh > /out/stdout.log 2>&1; rc=$?; cp /logs/verifier/reward.json /out/reward.json 2>/dev/null; exit $rc' >out/$name/container.log 2>&1
  rc=$?; [ $rc = 0 ] && [ -s out/$name/reward.json ] || fail=1
  echo "$name exit=$rc seconds=$((SECONDS-t0)) reward=$(python3 -c "import json;print(json.load(open('out/$name/reward.json'))['reward'])" 2>/dev/null)" | tee -a out/summary.txt
 done
done
docker image rm ebv/datagen:v2.1 >/dev/null 2>&1; rm -rf pkg-datagen/files
echo "done fail=$fail" >> out/summary.txt
exit $fail
