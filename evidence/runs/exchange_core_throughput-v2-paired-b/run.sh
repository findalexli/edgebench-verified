#!/bin/bash
# Paired v1/v2 evaluation for exchange_core_throughput-v2 (E2B worker, root, /job).
# Every arm runs the task's ORIGINAL eval_cmd in a fresh container with --network none (task internet:false).
#  v1  = pinned original image + the surefire provider overlay mounted at /root/.m2 (image's own ~/.m2 plus the
#        same 30 Maven Central files that v2 bakes in; copied from /job/pkg, no network). Without it v1 cannot run
#        offline at all (arm v1raw shows this).
#  v2  = image built from /job/pkg/Dockerfile (FROM original digest + COPY), no mount.
set -uo pipefail
V1=seededge/edgebench.judge.exchange_core_throughput@sha256:6b1617315cd2bdc7248ed057b449042c215b90c7571e302378d3c8b3202bbb8d
V2=ebv/exchange_core_throughput:v2
O=/job/out; mkdir -p $O/logs
EVAL='cd /home/workspace/exchange-core && python3 /tmp/eval_exchange_core.py'
{ nproc; free -m; df -h /; docker version --format '{{.Server.Version}}'; date -u; } > $O/env.txt 2>&1
docker pull -q $V1 > $O/pull.log 2>&1 || { echo pull-failed | tee -a $O/summary.txt; exit 2; }
docker image inspect $V1 --format '{{.Id}}' >> $O/pull.log
docker build -t $V2 /job/pkg > $O/build.log 2>&1 || { echo build-failed | tee -a $O/summary.txt; exit 3; }
docker image inspect $V2 --format '{{.Id}}' > $O/v2_image_id.txt
for img in $V1 $V2; do docker run --rm --network none $img bash -c 'sha256sum /tmp/eval_exchange_core.py; ls /root/.m2/repository/org/apache/maven/surefire/ | tr "\n" " "; echo'; done > $O/image_files.txt 2>&1
mkdir -p /job/m2v1
docker run --rm --network none -v /job/m2v1:/m2 $V1 bash -c 'cp -a /root/.m2/. /m2/' > $O/m2v1_copy.txt 2>&1
cp -a /job/pkg/files/m2/repository/. /job/m2v1/repository/
run_arm() { # $1 arm(variant) $2 label $3 image $4 extra docker args
  local arm=$1 lab=$2 img=$3 extra=$4 log=$O/logs/$1-$2.log t0=$(date +%s)
  timeout 2500 docker run --rm --network none --cpus 8 --memory 6g -v /job/inputs:/in:ro $extra $img \
    bash -c "python3 /in/mutate.py $arm && $EVAL" > $log 2>&1
  local rc=$?
  echo "$arm $lab exit=$rc wall=$(( $(date +%s) - t0 ))s $(grep -E '^(GATE OK|CASE 0000)' $log | tr '\n' ' ') $(grep -E '^(TOTAL_SCORE|CASES_OK)' $log | tr '\n' ' ')" | tee -a $O/summary.txt
}
run_arm control v1raw $V1 ""
for arm in control feeswap dropevents topo21 feeleak compileerr control; do
  run_arm $arm v1 $V1 "-v /job/m2v1:/root/.m2"
  run_arm $arm v2 $V2 ""
done
date -u >> $O/env.txt
docker image rm $V2 >/dev/null 2>&1; echo done >> $O/summary.txt
