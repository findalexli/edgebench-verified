#!/bin/bash
# grid_turing_robot: does an honest solution within the README's "30 seconds / test case" time out
# when the grader has 4 CPUs (published leaderboard setting, judge_cpu_limit: 4) but not at 8?
# Runs the task's ORIGINAL eval_cmd in the digest-pinned judge image, --network none, one arm at a
# time. Solutions are bind-mounted read-only over solution.py; each solution writes its own start/end
# wall time to /ebvtiming/<pid>.txt (a per-arm host dir), which does not affect grading.
# Arms are listed in /job/arms.txt as "<label> <cpus> <solution file>".
set -uo pipefail
IMG=seededge/edgebench.judge.grid_turing_robot@sha256:f67864ad75a3a2af0f7904a05a30b888f66ce2ed5c1f3cac7d7482e578a296c3
EVAL='cd /home/workspace/grid_turing_robot && python3 /tmp/eval_grid_turing_robot.py'
O=/job/out; mkdir -p $O/logs $O/timing
{ nproc; free -m; lscpu | grep -E 'Model name|^CPU\(s\)|Thread'; docker version --format '{{.Server.Version}}'; } > $O/env.txt 2>&1
docker pull $IMG > $O/pull.log 2>&1 || { echo pull-failed | tee -a $O/summary.txt; exit 2; }
docker image inspect $IMG --format '{{.Id}} {{.RepoDigests}}' > $O/image.txt
docker run --rm --network none $IMG bash -c 'sha256sum /tmp/eval_grid_turing_robot.py; grep -n "TIME_LIMIT =\|max_workers" /tmp/eval_grid_turing_robot.py' > $O/eval_sha.txt 2>&1
sha256sum /job/sol/* > $O/solutions_sha.txt
while read -r label cpus sol; do
  [ -z "$label" ] && continue
  T=$O/timing/$label; mkdir -p $T; chmod 777 $T
  t0=$(date +%s.%N)
  timeout 900 docker run --rm --network none --memory 4g --cpus $cpus \
    -v /job/sol/$sol:/home/workspace/grid_turing_robot/solution.py:ro -v $T:/ebvtiming \
    $IMG bash -c "$EVAL" > $O/logs/$label.log 2> $O/logs/$label.err
  rc=$?; L=$O/logs/$label.log
  echo "$label cpus=$cpus sol=$sol exit=$rc wall=$(python3 -c "print(round($(date +%s.%N)-$t0,1))" 2>/dev/null)s OK=$(grep -c ' OK ' $L) TLE=$(grep -c ' TLE ' $L) WA=$(grep -c ' WA ' $L) RE=$(grep -c ' RE ' $L) $(grep -E '^TOTAL_SCORE' $L)" | tee -a $O/summary.txt
done < /job/arms.txt
echo done >> $O/summary.txt
