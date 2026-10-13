#!/bin/bash
# warehouse_forklift_routing-v2: does running 8 inputs at once under the 150 s per-input limit time out
# an honest CPU-bound solution when the grader has 4 CPUs (published leaderboard setting), and does
# limiting parallelism to the CPU quota fix it? (E2B worker, root, /job)
# Images: v1 = digest-pinned original (TIME_LIMIT 60, 8 at once); v2prev = the earlier fixed version
# (TIME_LIMIT 150, 8 at once; /job/pkg-prev); v2 = the extended fixed version (TIME_LIMIT 150, at most
# the cgroup CPU quota at once; /job/pkg). Every arm runs the task's ORIGINAL eval_cmd,
# --network none --memory 4g --cpus <N>, one container at a time. The solution is bind-mounted
# read-only over solution.py; /job/sol is mounted at /opt/ctl so wrappers can exec the generic control.
# Arms are listed in /job/arms.txt as "<label> <cpus> <v1|v2prev|v2> <solution>".
set -uo pipefail
V1=seededge/edgebench.judge.warehouse_forklift_routing@sha256:ac7fdf03bb73d0f9ded21662c7c3ac246ce521ee5e6b237978a2799c7bc29cb3
V2P=ebv/warehouse_forklift_routing:v2prev
V2=ebv/warehouse_forklift_routing:v2
EVALF=/tmp/eval_warehouse_manager.py
EVAL='cd /home/workspace/warehouse_manager && python3 /tmp/eval_warehouse_manager.py'
O=/job/out; mkdir -p $O/logs $O/timing
{ nproc; free -m; lscpu | grep -E 'Model name|^CPU\(s\)|Thread'; docker version --format '{{.Server.Version}}'; } > $O/env.txt 2>&1
docker pull $V1 > $O/pull.log 2>&1 || { echo pull-failed | tee -a $O/summary.txt; exit 2; }
docker build -t $V2P /job/pkg-prev > $O/build-prev.log 2>&1 || { echo build-failed | tee -a $O/summary.txt; exit 3; }
docker build -t $V2 /job/pkg > $O/build.log 2>&1 || { echo build-failed | tee -a $O/summary.txt; exit 3; }
for img in $V1 $V2P $V2; do echo "$img $(docker image inspect $img --format '{{.Id}}')"; done > $O/image.txt
for img in $V1 $V2P $V2; do docker run --rm --network none $img bash -c "sha256sum $EVALF; grep -n '^TIME_LIMIT\|max_workers' $EVALF"; done > $O/eval_sha.txt 2>&1
for c in 1 2 4 8; do echo "cpus=$c $(docker run --rm --network none --cpus $c $V2 python3 -c "import sys, os; sys.path.insert(0, '/tmp'); import eval_warehouse_manager as e; print(open('/sys/fs/cgroup/cpu.max').read().strip() if os.path.exists('/sys/fs/cgroup/cpu.max') else 'cgroup-v1', 'workers', e.cpu_quota_workers())" 2>&1)"; done > $O/v2_workers.txt
sha256sum /job/sol/* > $O/solutions_sha.txt
while read -r label cpus ver sol; do
  [ -z "$label" ] && continue
  case $ver in v1) IMG=$V1;; v2prev) IMG=$V2P;; v2) IMG=$V2;; esac
  T=$O/timing/$label; mkdir -p $T; chmod 777 $T
  t0=$(date +%s.%N)
  timeout 3000 docker run --rm --network none --memory 4g --cpus $cpus \
    -v /job/sol/$sol:/home/workspace/warehouse_manager/solution.py:ro -v /job/sol:/opt/ctl:ro -v $T:/ebvtiming \
    $IMG bash -c "$EVAL" > $O/logs/$label.log 2> $O/logs/$label.err
  rc=$?; L=$O/logs/$label.log
  echo "$label cpus=$cpus ver=$ver sol=$sol exit=$rc wall=$(python3 -c "print(round($(date +%s.%N)-$t0,1))" 2>/dev/null)s OK=$(grep -c ' OK ' $L) TLE=$(grep -c ' TLE ' $L) WA=$(grep -c ' WA ' $L) RE=$(grep -c ' RE ' $L) $(grep -E '^TOTAL_SCORE' $L)" | tee -a $O/summary.txt
done < /job/arms.txt
docker image rm $V2 $V2P >/dev/null 2>&1; echo done >> $O/summary.txt
