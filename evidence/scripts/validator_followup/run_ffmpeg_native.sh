#!/bin/bash
set -euo pipefail
cd /job
mkdir -p out shim
trap 'docker rm -f ebv-layout-check >/dev/null 2>&1 || true' EXIT
F=seededge/edgebench.judge.ffmpeg_swscale_reimplementation@sha256:38b256686afe14f6cec76790a7e884eb46ac70eb918a60351942a9c35c0f879f
C=ebv/ffmpeg:v2.2
timeout --kill-after=10 300 docker pull "$F" >out/pull.log 2>&1
timeout --kill-after=10 90 docker build -t "$C" pkg-ffmpeg >out/build.log 2>&1
docker image inspect "$F" "$C" --format '{{.Id}} {{.RepoTags}}' >out/images.txt
# This original-helper correspondence gate must pass before candidate grading.
timeout --kill-after=10 60 docker run --rm --name ebv-layout-check --memory 4g --cpus 2 --network none -v /job:/job:ro -e PYTHONPATH=/opt/tests "$F" python3 /job/ffmpeg_buffers.py /job/pkg-ffmpeg/files/compute_reward.py >out/layouts.json 2>out/layouts.stderr

docker run --rm --memory 4g --network none -v /job:/job "$F" bash -c 'for arm in good skip bad; do flags=""; [ "$arm" != skip ] || flags=-DSKIP_SECOND; [ "$arm" != bad ] || flags=-DFAIL_ALWAYS; gcc -O2 -shared -fPIC $flags -DBASELINE_PATH="\"/verifier-data/libswscale_baseline.so\"" /job/ref_shim.c -o /job/shim/$arm.so -ldl; done' >out/compile.log 2>&1
for arm in good skip bad; do
 for revision in original candidate; do
  image=$F; [ "$revision" = original ] || image=$C
  name=ffmpeg-$arm-$revision; owned=ebv-$name; mkdir -p out/$name
  t0=$SECONDS; set +e
  timeout --kill-after=10 360 docker run --rm --name "$owned" --memory 4g --cpus 2 --network none -e ARM="$arm" -v /job:/job:ro -v /job/out/$name:/out "$image" bash -c 'export PYTHONPATH=/opt/tests; exec python3 /opt/tests/compute_reward.py --candidate /job/shim/$ARM.so --baseline /verifier-data/libswscale_baseline.so --output-dir /out > /out/stdout.log 2>&1' >out/$name/container.log 2>&1
  rc=$?
  docker rm -f "$owned" >/dev/null 2>&1
  set -e
  echo "$name exit=$rc seconds=$((SECONDS-t0))" | tee -a out/summary.txt
 done
done
# Collect every arm first, then fail the job on incomplete or incorrect evidence.
python3 /job/check_native_results.py /job/out >out/validation.json
