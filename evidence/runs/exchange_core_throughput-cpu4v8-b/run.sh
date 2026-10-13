#!/bin/bash
# exchange_core_throughput: raw throughput of the SHIPPED engine (and the prompt's 2ME+1RE tip) at 4 vs 8 CPUs.
# Every arm runs the task's ORIGINAL eval_cmd in the digest-pinned judge image, --network none --memory 4g.
# The original image cannot resolve the surefire JUnit-platform provider offline, so (as in
# exchange_core_throughput-v2-paired-b) ~/.m2 is mounted: the image's own ~/.m2 plus the 30 public Maven Central
# files the v2 repair adds (downloaded here and checked against repairs/exchange_core_throughput-v2/source-lock.json).
# /job/arms.txt lines: "<label> <cpus> <variant: control|topo21>".
set -uo pipefail
V1=seededge/edgebench.judge.exchange_core_throughput@sha256:6b1617315cd2bdc7248ed057b449042c215b90c7571e302378d3c8b3202bbb8d
W1=seededge/edgebench.work.exchange_core_throughput@sha256:86aaeee58b150afb10aa5e5258dde977147216027760ba9ff8fc91f462e1a1bb
O=/job/out; mkdir -p $O/logs $O/docs
EVAL='cd /home/workspace/exchange-core && python3 /tmp/eval_exchange_core.py'
{ nproc; free -m; lscpu | grep -E 'Model name|^CPU\(s\)|Thread'; docker version --format '{{.Server.Version}}'; date -u; } > $O/env.txt 2>&1
docker pull -q $V1 > $O/pull.log 2>&1 || { echo pull-failed | tee -a $O/summary.txt; exit 2; }
docker image inspect $V1 --format '{{.Id}} {{.RepoDigests}}' >> $O/pull.log
docker run --rm --network none $V1 bash -c 'sha256sum /tmp/eval_exchange_core.py; grep -n "TIMEOUT =" /tmp/eval_exchange_core.py; cd /home/workspace/exchange-core; grep -n -iE "matchingEnginesNum|riskEnginesNum|waitStrategy|AffinityThreadFactory|THREAD_AFFINITY" src/main/java/exchange/core2/core/common/config/PerformanceConfiguration.java | head -30; grep -rniE "cpu|core[s]? |thread|second|timeout" README.md | head -30' > $O/docs/judge.txt 2>&1
for c in 4 8; do echo "--cpus $c: nproc=$(docker run --rm --network none --cpus $c $V1 nproc) cpu.max=$(docker run --rm --network none --cpus $c $V1 cat /sys/fs/cgroup/cpu.max)"; done >> $O/docs/judge.txt 2>&1
docker pull -q $W1 >> $O/pull.log 2>&1 && docker run --rm --network none $W1 bash -c 'cd /home/workspace/exchange-core 2>/dev/null || cd /home/workspace; pwd; ls; grep -rniE "cpu|core[s]? |thread|second|timeout|machine|hardware" --include="*.md" . 2>/dev/null | grep -v "^./src" | head -40' > $O/docs/work.txt 2>&1; docker image rm $W1 >/dev/null 2>&1
mkdir -p /job/m2v1
docker run --rm --network none -v /job/m2v1:/m2 $V1 bash -c 'cp -a /root/.m2/. /m2/' > $O/m2v1_copy.txt 2>&1
bad=0
while read -r url rel sha; do
  mkdir -p "/job/m2v1/repository/$(dirname $rel)"
  curl -fsSL --retry 3 -o "/job/m2v1/repository/$rel" "$url" || bad=1
  echo "$sha  /job/m2v1/repository/$rel" | sha256sum -c --quiet - || bad=1
done < /job/inputs/maven.txt
echo "maven overlay files=$(wc -l < /job/inputs/maven.txt) bad=$bad" | tee -a $O/summary.txt
[ $bad = 0 ] || exit 4
while read -r label cpus variant; do
  [ -z "$label" ] && continue
  log=$O/logs/$label.log; t0=$(date +%s)
  timeout 1950 docker run --rm --network none --cpus $cpus --memory 4g -v /job/inputs:/in:ro -v /job/m2v1:/root/.m2 $V1 \
    bash -c "python3 /in/mutate.py $variant && $EVAL" > $log 2>&1
  rc=$?
  echo "$label cpus=$cpus variant=$variant exit=$rc wall=$(( $(date +%s) - t0 ))s $(grep -E '^CASE 0000' $log | tr '\n' ' ') $(grep -E '^(TOTAL_SCORE|CASES_OK)' $log | tr '\n' ' ') rounds=[$(grep -oE '^\s*[0-9]+\. [0-9.]+ MT/s' $log | awk '{print $2}' | tr '\n' ' ')]" | tee -a $O/summary.txt
done < /job/arms.txt
date -u >> $O/env.txt
rm -rf /job/m2v1; echo done >> $O/summary.txt
