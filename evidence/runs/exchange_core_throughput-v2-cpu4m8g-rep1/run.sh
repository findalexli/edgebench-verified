#!/bin/bash
# exchange_core_throughput v2 at the leaderboard judge setting (judge_cpu_limit 4, judge_mem_limit 8g), issue #64.
# Layout of exchange_core_throughput-cpu4v8-a/run.sh, with the v2 image built here from the package
# (pkg/: materialize.sh + docker build, as in exchange_core_throughput-v2-paired-shutdownfail-rep3).
#  v2 = image built from pkg/, run without any mount (offline Maven pre-seed is in the image)
#  v1 = pinned original + the same 30 Maven Central files mounted at /root/.m2 (needed to resolve surefire offline)
# Every arm: the task's ORIGINAL eval_cmd, docker run --network none --cpus 4 --memory 8g.
set -uo pipefail
V1=seededge/edgebench.judge.exchange_core_throughput@sha256:6b1617315cd2bdc7248ed057b449042c215b90c7571e302378d3c8b3202bbb8d
V2=ebv/exchange_core_throughput:v2
O=/job/out; mkdir -p $O/logs
EVAL='cd /home/workspace/exchange-core && python3 /tmp/eval_exchange_core.py'
{ nproc; free -m; df -h /; lscpu | grep -E 'Model name|^CPU\(s\)'; docker version --format '{{.Server.Version}}'; date -u; } > $O/env.txt 2>&1
docker pull -q $V1 > $O/pull.log 2>&1 || { echo pull-failed | tee -a $O/summary.txt; exit 2; }
docker image inspect $V1 --format '{{.Id}}' >> $O/pull.log
command -v patch >/dev/null || { (apt-get update -qq && apt-get install -y -qq patch) > $O/apt.log 2>&1; }
( cd /job/pkg && bash materialize.sh ) > $O/materialize.log 2>&1 || { echo materialize-failed | tee -a $O/summary.txt; exit 4; }
sha256sum /job/pkg/files/eval_exchange_core.py > $O/v2_eval_sha256.txt
docker build -t $V2 /job/pkg > $O/build.log 2>&1 || { echo build-failed | tee -a $O/summary.txt; exit 3; }
docker image inspect $V2 --format '{{.Id}}' > $O/v2_image_id.txt
echo "--cpus 4 --memory 8g: nproc=$(docker run --rm --network none --cpus 4 --memory 8g $V2 nproc) cpu.max=$(docker run --rm --network none --cpus 4 --memory 8g $V2 cat /sys/fs/cgroup/cpu.max) memory.max=$(docker run --rm --network none --cpus 4 --memory 8g $V2 cat /sys/fs/cgroup/memory.max)" >> $O/env.txt 2>&1
mkdir -p /job/m2v1
docker run --rm --network none -v /job/m2v1:/m2 $V1 bash -c 'cp -a /root/.m2/. /m2/' > $O/m2v1_copy.txt 2>&1
cp -a /job/pkg/files/m2/repository/. /job/m2v1/repository/
fail=0
run_arm() { # $1 variant $2 label $3 image $4 extra docker args
  local arm=$1 lab=$2 img=$3 extra=$4 log=$O/logs/$1-$2.log t0=$(date +%s)
  timeout 2450 docker run --rm --network none --cpus 4 --memory 8g -v /job/inputs:/in:ro $extra $img \
    bash -c "python3 /in/mutate.py $arm && $EVAL" > $log 2>&1
  local rc=$?; [ $rc = 0 ] || fail=1
  echo "$arm $lab exit=$rc wall=$(( $(date +%s) - t0 ))s $(grep -E '^(GATE OK|CASE 0000)' $log | tr '\n' ' ') $(grep -E '^(TOTAL_SCORE|CASES_OK)' $log | tr '\n' ' ')" | tee -a $O/summary.txt
}
for arm in control topo21; do
  run_arm $arm v2 $V2 ""
  run_arm $arm v1 $V1 "-v /job/m2v1:/root/.m2"
done
date -u >> $O/env.txt
rm -rf /job/pkg/files /job/m2v1
docker image rm $V2 >/dev/null 2>&1; echo "done fail=$fail" >> $O/summary.txt
exit $fail
