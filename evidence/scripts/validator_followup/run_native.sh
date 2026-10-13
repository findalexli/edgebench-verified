#!/bin/bash
set -euo pipefail
cd /job
mkdir -p out
D=seededge/edgebench.judge.schemathesis_datagen_pipeline@sha256:16b21364d67906d802e24d0b3b4505c42a6ac0f91cd5b382bb4c9d1d20224d37
F=seededge/edgebench.judge.ffmpeg_swscale_reimplementation@sha256:38b256686afe14f6cec76790a7e884eb46ac70eb918a60351942a9c35c0f879f
for short in datagen ffmpeg; do
 if [ "$short" = datagen ]; then original=$D; else original=$F; fi
 timeout 300 docker pull "$original" >out/pull-$short.log 2>&1
 timeout 90 docker build -t ebv/$short:v2.1 pkg-$short >out/build-$short.log 2>&1
 docker image inspect "$original" ebv/$short:v2.1 --format '{{.Id}} {{.RepoTags}}' >out/images-$short.txt
 if [ "$short" = datagen ]; then
  for variant in stdlib_1900 stdlib_any_year garbage_shape; do
   for revision in original candidate; do
    image=$D; [ "$revision" = original ] || image=ebv/datagen:v2.1
    name=datagen-$variant-$revision; mkdir -p out/$name
    t0=$SECONDS
    set +e
    timeout 180 docker run --rm --memory 4g --cpus 2 --network none -e EBV_DATE_VARIANT="$variant" -v /job:/job:ro -v /job/out/$name:/out "$image" bash -c 'cp /job/headers_overlay.py /app/src/schemathesis/specs/openapi/headers.py; bash /job/datagen-eval.sh > /out/stdout.log 2>&1; rc=$?; cp /logs/verifier/reward.json /out/reward.json 2>/dev/null; exit $rc' >out/$name/container.log 2>&1
    rc=$?; set -e
    echo "$name exit=$rc seconds=$((SECONDS-t0))" | tee -a out/summary.txt
   done
  done
 else
  mkdir -p shim
  docker run --rm --memory 4g --network none -v /job:/job "$F" bash -c 'for arm in good skip bad; do flags=""; [ "$arm" != skip ] || flags=-DSKIP_SECOND; [ "$arm" != bad ] || flags=-DFAIL_ALWAYS; gcc -O2 -shared -fPIC $flags -DBASELINE_PATH="\"/verifier-data/libswscale_baseline.so\"" /job/ref_shim.c -o /job/shim/$arm.so -ldl; done' >out/compile.log 2>&1
  for arm in good skip bad; do
   for revision in original candidate; do
    image=$F; [ "$revision" = original ] || image=ebv/ffmpeg:v2.1
    name=ffmpeg-$arm-$revision; mkdir -p out/$name
    t0=$SECONDS; set +e
    timeout 360 docker run --rm --memory 4g --cpus 2 --network none -e ARM="$arm" -v /job:/job:ro -v /job/out/$name:/out "$image" bash -c 'PYTHONPATH=/opt/tests python3 /opt/tests/compute_reward.py --candidate /job/shim/$ARM.so --baseline /verifier-data/libswscale_baseline.so --output-dir /out > /out/stdout.log 2>&1' >out/$name/container.log 2>&1
    rc=$?;set -e
    echo "$name exit=$rc seconds=$((SECONDS-t0))" | tee -a out/summary.txt
   done
  done
 fi
done
