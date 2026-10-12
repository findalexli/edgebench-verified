#!/bin/bash
# exchange_core_throughput: does the original eval accept a wrong engine and still award throughput credit?
set -u
IMG=seededge/edgebench.judge.exchange_core_throughput@sha256:6b1617315cd2bdc7248ed057b449042c215b90c7571e302378d3c8b3202bbb8d
mkdir -p /job/out
{ nproc; free -m; date -u; } > /job/out/host.txt
docker pull -q $IMG > /job/out/pull.txt 2>&1
docker image inspect $IMG --format '{{.Id}}' >> /job/out/pull.txt
# The pinned image's ~/.m2 lacks org.apache.maven.surefire:surefire-junit-platform:3.0.0-M3, so with
# --network none every run (including the unmodified engine) fails with ClassNotFoundException
# JUnitPlatformProvider -> "CASE 0000 RE score=0" (attempt 1). Provider overlay: copy the image's ~/.m2 to
# /job/m2, let surefire fetch only what it is missing while running one tiny shipped unit test WITH network,
# record the added files, then run every scored/oracle run with --network none and the overlay mounted.
mkdir -p /job/m2 /job/out/overlay
docker run --rm --name ebv-exch-m2copy -v /job/m2:/m2 $IMG bash -c 'cp -a /root/.m2/. /m2/' > /job/out/overlay/copy.txt 2>&1
find /job/m2 -type f | sort > /job/out/overlay/before.txt
docker run --rm --name ebv-exch-m2fetch -v /job/m2:/root/.m2 -v /job/inputs:/in:ro -v /job/out/overlay:/out $IMG bash /in/it_test.sh SimpleEventsProcessorTest > /job/out/overlay/fetch.txt 2>&1
echo "fetch rc=$?" >> /job/out/overlay/fetch.txt
find /job/m2 -type f | sort > /job/out/overlay/after.txt
comm -13 /job/out/overlay/before.txt /job/out/overlay/after.txt | grep -v -E '_remote.repositories$|\.lastUpdated$|resolver-status.properties$' | xargs -r sha256sum > /job/out/overlay/added.sha256
run() {  # $1 name  $2 shell command run after the mutation
  local name=$1 variant=$2 cmd=$3
  mkdir -p /job/out/$name
  local t0=$(date +%s)
  timeout 2400 docker run --rm --name ebv-exch-$name --network none --cpus 8 --memory 6g \
    -v /job/inputs:/in:ro -v /job/out/$name:/out -v /job/m2:/root/.m2 $IMG \
    bash -c "python3 /in/mutate.py $variant > /out/mutation.txt 2>&1 && cd /home/workspace/exchange-core && $cmd; cp -r target/surefire-reports /out/ 2>/dev/null; true" > /job/out/$name/stdout.txt 2> /job/out/$name/stderr.txt
  echo "rc=$? elapsed=$(( $(date +%s)-t0 ))s" > /job/out/$name/docker_rc.txt
}
EVAL='python3 /tmp/eval_exchange_core.py'
run perf_control control "$EVAL"
run perf_feeswap feeswap "$EVAL"
run perf_dropevents dropevents "$EVAL"
date -u >> /job/out/host.txt
