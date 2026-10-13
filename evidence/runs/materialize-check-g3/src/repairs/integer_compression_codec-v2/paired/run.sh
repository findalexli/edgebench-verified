#!/bin/bash
# Paired v1/v2 evaluation for integer_compression_codec-v2 (E2B worker, root, /job).
# Every arm runs the task's ORIGINAL eval_cmd inside the judge image, --network none;
# only the image differs (v1 = pinned original, v2 = built from /job/pkg/Dockerfile).
set -uo pipefail
V1=seededge/edgebench.judge.integer_compression_codec@sha256:15dffad066b4bd1e4844b3d3798a605c80df8e83db547998b560c28e28e989ac
WORK=seededge/edgebench.work.integer_compression_codec@sha256:b6a58b1aaf1030221caf85700f6c91a9e73c1bdd0673e12df8b357ed9bae1785
V2=ebv/integer_compression_codec:v2
O=/job/out; mkdir -p $O/logs
EVAL='cd /home/workspace/integer-compression-codec && python3 runner_judge.py'
D=/home/workspace/integer-compression-codec
(nproc; free -m; lscpu | grep -E "Model name"; docker version --format '{{.Server.Version}}') > $O/env.txt 2>&1
docker pull $V1 > $O/pull.log 2>&1 || { echo pull-failed > $O/summary.txt; exit 2; }
docker image inspect $V1 --format '{{.Id}}' >> $O/pull.log
docker build -t $V2 /job/pkg > $O/build.log 2>&1 || { echo build-failed > $O/summary.txt; exit 3; }
docker image inspect $V2 --format '{{.Id}}' > $O/v2_image_id.txt
for img in $V1 $V2; do echo "== $img"; docker run --rm --network none $img bash -c "cd $D && sha256sum runner_judge.py src/codec.cpp include/intcompress.h Makefile internal/baseline/baseline_results.json; ls internal/baseline/starter 2>/dev/null && sha256sum internal/baseline/starter/*"; done > $O/file_sha.txt 2>&1
sha256sum /job/variants/*/codec.cpp > $O/variants_sha.txt
run_arm() { # $1 variant  $2 version  $3 image  $4 tag
  local t0=$(date +%s)
  timeout 900 docker run --rm --network none --cpus 4 --memory 6g -v /job/variants/$1:/v:ro $3 \
    bash -c "cp /v/codec.cpp $D/src/codec.cpp && $EVAL" > $O/logs/$4-$1-$2.stdout 2> $O/logs/$4-$1-$2.stderr
  local rc=$?
  echo "$4 $1 $2 exit=$rc wall=$(( $(date +%s) - t0 ))s $(python3 /job/tools/summarize.py $O/logs/$4-$1-$2.stdout)" | tee -a $O/summary.txt
}
n=0
for v in s0_starter s1_roundtrip_bug s2_delta_zigzag_varint; do
  n=$((n+1)); run_arm $v v1 $V1 r$n; run_arm $v v2 $V2 r$n
done
# Run-to-run noise in v2 (same host): starter and honest codec once more.
n=$((n+1)); run_arm s0_starter v2 $V2 r$n
n=$((n+1)); run_arm s2_delta_zigzag_varint v2 $V2 r$n
echo arms-done >> $O/summary.txt
# Optional: confirm the solver-visible starter in the work image equals the v2 baseline copy.
docker image rm $V1 > /dev/null 2>&1
if timeout 900 docker pull $WORK > $O/work_pull.log 2>&1; then
  docker run --rm --network none $WORK bash -c "cd $D && sha256sum src/codec.cpp include/intcompress.h Makefile" > $O/work_sha.txt 2>&1
else echo "work image pull failed or timed out" > $O/work_sha.txt; fi
docker image rm $V2 >/dev/null 2>&1; echo done >> $O/summary.txt
