#!/bin/bash
# ann_vector_search_qps, issue #3: isolated honest gradings on the ORIGINAL evaluator at the leaderboard
# judge setting (4 CPUs, 8 GiB). One worker per repeat; on each worker two separate gradings, each in a
# fresh container from the digest-pinned judge image, running the task's own eval_cmd unchanged:
#   honest  = FAISS IVF-flat nlist 1024 nprobe 32 (config.yml lists only this configuration)
#   nprobe1 = the same module with nprobe 1 (below-threshold recall control)
set -uo pipefail
I=seededge/edgebench.judge.ann_vector_search_qps@sha256:aa2856a379c10b93b0661a0b91b729a80fc2cf9bf119cc1385beea6b93eef288
EVAL='cd /home/workspace/ann-benchmarks && python3 /tmp/eval_ann_search.py'
SLOT=/home/workspace/ann-benchmarks/ann_benchmarks/algorithms/custom
O=/job/out; mkdir -p $O/logs
{ nproc; free -m; df -h /; lscpu | grep -E 'Model name|^CPU\(s\)|Thread|Socket|MHz'; docker version --format '{{.Server.Version}}'; date -u; } > $O/env.txt 2>&1
docker pull -q $I > $O/pull.log 2>&1 || { echo pull-failed | tee -a $O/summary.txt; exit 2; }
docker image inspect $I --format '{{.Id}}' >> $O/pull.log
(cd /job/inputs && sha256sum honest/custom/* nprobe1/custom/*) > $O/submission_sha256.txt
docker run --rm --network none --cpus 4 --memory 8g --entrypoint sh $I -c '
  echo nproc=$(nproc) cpu.max=$(cat /sys/fs/cgroup/cpu.max 2>/dev/null) memory.max=$(cat /sys/fs/cgroup/memory.max 2>/dev/null)
  sha256sum /tmp/eval_ann_search.py
  grep -m1 "model name" /proc/cpuinfo
  python3 -c "import sys,faiss,numpy,h5py; print(\"python\", sys.version.split()[0]); print(\"faiss\", faiss.__version__); print(\"numpy\", numpy.__version__); print(\"h5py\", h5py.__version__)"
  cd /home/workspace/ann-benchmarks && (git rev-parse HEAD 2>/dev/null || echo "no git metadata")' > $O/container_env.txt 2>&1
fail=0
for arm in honest nprobe1; do
  t0=$(date +%s)
  timeout 2400 docker run --rm --network none --cpus 4 --memory 8g -v /job/inputs/$arm/custom:$SLOT:ro \
    --entrypoint sh $I -c "$EVAL" > $O/logs/$arm.stdout 2> $O/logs/$arm.stderr
  rc=$?; [ $rc = 0 ] || fail=1
  echo "$arm exit=$rc wall=$(( $(date +%s) - t0 ))s $(grep -E '^(CASE|TOTAL_SCORE|CASES_OK|CASES_TOTAL)' $O/logs/$arm.stdout | tr '\n' ' ')" | tee -a $O/summary.txt
done
date -u >> $O/env.txt
echo "done fail=$fail" >> $O/summary.txt
exit $fail
