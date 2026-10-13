#!/bin/bash
# Side-by-side arm for the v2 grader's second change (`if status != "OK": score = 0`).
# Same layout as repairs/exchange_core_throughput-v2/paired/run.sh (E2B worker, root, /job), except
# the v2 build context is materialized here from the package (pkg/: Dockerfile, materialize.sh,
# repair.patch, source-lock.json copied unchanged from repairs/exchange_core_throughput-v2/).
#  v1 = pinned original image + the surefire provider overlay mounted at /root/.m2 (as in the paired run)
#  v2 = image built from pkg/Dockerfile after materialize.sh (sha256 of every output checked against the lock)
# Arms (inputs/mutate.py = the package's mutate.py plus two arms):
#  control      unmodified engine
#  shutdownbusy all 50 rounds pass, then ExchangeCore.shutdown() throws, only for BUSY_SPIN (throughput config)
#  shutdownall  same, in every configuration (the gate's integration tests also shut down)
set -uo pipefail
V1=seededge/edgebench.judge.exchange_core_throughput@sha256:6b1617315cd2bdc7248ed057b449042c215b90c7571e302378d3c8b3202bbb8d
V2=ebv/exchange_core_throughput:v2
O=/job/out; mkdir -p $O/logs
EVAL='cd /home/workspace/exchange-core && python3 /tmp/eval_exchange_core.py'
{ nproc; free -m; df -h /; docker version --format '{{.Server.Version}}'; date -u; } > $O/env.txt 2>&1
docker pull -q $V1 > $O/pull.log 2>&1 || { echo pull-failed | tee -a $O/summary.txt; exit 2; }
docker image inspect $V1 --format '{{.Id}}' >> $O/pull.log
command -v patch >/dev/null || { (apt-get update -qq && apt-get install -y -qq patch) > $O/apt.log 2>&1; }
( cd /job/pkg && bash materialize.sh ) > $O/materialize.log 2>&1 || { echo materialize-failed | tee -a $O/summary.txt; exit 4; }
sha256sum /job/pkg/files/eval_exchange_core.py > $O/v2_eval_sha256.txt
docker build -t $V2 /job/pkg > $O/build.log 2>&1 || { echo build-failed | tee -a $O/summary.txt; exit 3; }
docker image inspect $V2 --format '{{.Id}}' > $O/v2_image_id.txt
for img in $V1 $V2; do docker run --rm --network none $img bash -c 'sha256sum /tmp/eval_exchange_core.py; ls /root/.m2/repository/org/apache/maven/surefire/ | tr "\n" " "; echo'; done > $O/image_files.txt 2>&1
mkdir -p /job/m2v1
docker run --rm --network none -v /job/m2v1:/m2 $V1 bash -c 'cp -a /root/.m2/. /m2/' > $O/m2v1_copy.txt 2>&1
cp -a /job/pkg/files/m2/repository/. /job/m2v1/repository/
run_arm() { # $1 arm(variant) $2 label $3 image $4 extra docker args
  local arm=$1 lab=$2 img=$3 extra=$4 log=$O/logs/$1-$2.log t0=$(date +%s)
  [ -f $log ] && log=$O/logs/$1-$2-rep2.log
  timeout 2500 docker run --rm --network none --cpus 8 --memory 6g -v /job/inputs:/in:ro $extra $img \
    bash -c "python3 /in/mutate.py $arm && $EVAL" > $log 2>&1
  local rc=$?
  echo "$arm $lab exit=$rc wall=$(( $(date +%s) - t0 ))s $(grep -E '^(GATE OK|CASE 0000)' $log | tr '\n' ' ') $(grep -E '^(TOTAL_SCORE|CASES_OK)' $log | tr '\n' ' ')" | tee -a $O/summary.txt
}
for arm in control shutdownbusy shutdownall shutdownbusy; do
  run_arm $arm v1 $V1 "-v /job/m2v1:/root/.m2"
  run_arm $arm v2 $V2 ""
done
date -u >> $O/env.txt
rm -rf /job/pkg/files /job/m2v1
docker image rm $V2 >/dev/null 2>&1; echo done >> $O/summary.txt
