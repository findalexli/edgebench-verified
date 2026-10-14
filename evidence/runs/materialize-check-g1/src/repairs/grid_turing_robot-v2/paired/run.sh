#!/bin/bash
# Paired v1/v2 evaluation for grid_turing_robot-v2 (E2B worker, root, /job).
# v1 = digest-pinned original judge image; v2 = built from /job/pkg/Dockerfile (one evaluator file
# changed: parallelism at most the cgroup CPU quota). Every arm runs the task's ORIGINAL eval_cmd,
# --network none --memory 4g --cpus <N>, one container at a time. Solutions are bind-mounted
# read-only over solution.py; each writes its own start/end times to /ebvtiming (per-arm host dir),
# which does not affect grading. Arms are listed in /job/arms.txt as "<label> <cpus> <v1|v2> <solution>".
set -uo pipefail
V1=seededge/edgebench.judge.grid_turing_robot@sha256:f67864ad75a3a2af0f7904a05a30b888f66ce2ed5c1f3cac7d7482e578a296c3
V2=ebv/grid_turing_robot:v2
EVALF=/tmp/eval_grid_turing_robot.py
EVAL='cd /home/workspace/grid_turing_robot && python3 /tmp/eval_grid_turing_robot.py'
O=/job/out; mkdir -p $O/logs $O/timing
{ nproc; free -m; lscpu | grep -E 'Model name|^CPU\(s\)|Thread'; docker version --format '{{.Server.Version}}'; } > $O/env.txt 2>&1
docker pull $V1 > $O/pull.log 2>&1 || { echo pull-failed | tee -a $O/summary.txt; exit 2; }
docker build -t $V2 /job/pkg > $O/build.log 2>&1 || { echo build-failed | tee -a $O/summary.txt; exit 3; }
docker image inspect $V1 --format '{{.Id}} {{.RepoDigests}}' > $O/image.txt
docker image inspect $V2 --format '{{.Id}}' > $O/v2_image_id.txt
for img in $V1 $V2; do docker run --rm --network none $img bash -c "sha256sum $EVALF; ls -l $EVALF; grep -n 'max_workers' $EVALF"; done > $O/eval_sha.txt 2>&1
# what the fixed evaluator computes inside the container at each CPU setting
for c in 1 2 4 8; do echo "cpus=$c $(docker run --rm --network none --cpus $c $V2 python3 -c "import sys; sys.path.insert(0, '$(dirname $EVALF)'); import $(basename $EVALF .py) as e; print(open('/sys/fs/cgroup/cpu.max').read().strip() if __import__('os').path.exists('/sys/fs/cgroup/cpu.max') else 'cgroup-v1', 'workers', e.cpu_quota_workers())" 2>&1)"; done > $O/v2_workers.txt
sha256sum /job/sol/* > $O/solutions_sha.txt
while read -r label cpus ver sol; do
  [ -z "$label" ] && continue
  if [ "$ver" = v1 ]; then IMG=$V1; else IMG=$V2; fi
  T=$O/timing/$label; mkdir -p $T; chmod 777 $T
  t0=$(date +%s.%N)
  timeout 900 docker run --rm --network none --memory 4g --cpus $cpus \
    -v /job/sol/$sol:/home/workspace/grid_turing_robot/solution.py:ro -v $T:/ebvtiming \
    $IMG bash -c "$EVAL" > $O/logs/$label.log 2> $O/logs/$label.err
  rc=$?; L=$O/logs/$label.log
  echo "$label cpus=$cpus ver=$ver sol=$sol exit=$rc wall=$(python3 -c "print(round($(date +%s.%N)-$t0,1))" 2>/dev/null)s OK=$(grep -c ' OK ' $L) TLE=$(grep -c ' TLE ' $L) WA=$(grep -c ' WA ' $L) RE=$(grep -c ' RE ' $L) $(grep -E '^TOTAL_SCORE' $L)" | tee -a $O/summary.txt
done < /job/arms.txt
docker image rm $V2 >/dev/null 2>&1; echo done >> $O/summary.txt
