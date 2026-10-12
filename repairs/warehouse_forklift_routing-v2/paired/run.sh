#!/bin/bash
# Paired v1/v2 evaluation for warehouse_forklift_routing-v2 (E2B worker, root, /job).
# Every arm runs the task's ORIGINAL eval_cmd inside the judge image, --network none;
# only the image differs (v1 = pinned original, v2 = built from /job/pkg/Dockerfile).
# Arms run one container at a time. The solution is bind-mounted read-only over solution.py;
# /job/sol is mounted at /opt/ctl so wrappers can exec the generic control.
set -uo pipefail
V1=seededge/edgebench.judge.warehouse_forklift_routing@sha256:ac7fdf03bb73d0f9ded21662c7c3ac246ce521ee5e6b237978a2799c7bc29cb3
V2=ebv/warehouse_forklift_routing:v2
O=/job/out; mkdir -p $O/logs
EVAL='cd /home/workspace/warehouse_manager && python3 /tmp/eval_warehouse_manager.py'
nproc > $O/env.txt; free -m >> $O/env.txt; docker version --format '{{.Server.Version}}' >> $O/env.txt
docker pull $V1 > $O/pull.log 2>&1 || { echo pull-failed | tee -a $O/summary.txt; exit 2; }
docker build -t $V2 /job/pkg > $O/build.log 2>&1 || { echo build-failed | tee -a $O/summary.txt; exit 3; }
docker image inspect $V2 --format '{{.Id}}' > $O/v2_image_id.txt
for img in $V1 $V2; do docker run --rm --network none $img bash -c 'sha256sum /tmp/eval_warehouse_manager.py; grep -n "^TIME_LIMIT" /tmp/eval_warehouse_manager.py'; done > $O/eval_sha.txt 2>&1
sha256sum /job/sol/* > $O/submissions_sha.txt
run_arm() { # $1 arm  $2 version  $3 image  $4 solution file
  local t0=$(date +%s)
  timeout 2000 docker run --rm --network none --memory 2g --cpus 2 \
    -v /job/sol/$4:/home/workspace/warehouse_manager/solution.py:ro -v /job/sol:/opt/ctl:ro \
    $3 bash -c "$EVAL" > $O/logs/$1-$2.stdout 2> $O/logs/$1-$2.stderr
  local rc=$?; local L=$O/logs/$1-$2.stdout
  echo "$1 $2 exit=$rc wall=$(( $(date +%s) - t0 ))s OK=$(grep -c ' OK ' $L) TLE=$(grep -c ' TLE ' $L) WA=$(grep -c ' WA ' $L) RE=$(grep -c ' RE ' $L) $(grep -E '^TOTAL_SCORE' $L)" | tee -a $O/summary.txt
}
# fast arms first, then the time-budget trigger, then the near-limit arm
run_arm control v1 $V1 control_solution.py;   run_arm control v2 $V2 control_solution.py
run_arm one_bug v1 $V1 sol_one_bug.py;         run_arm one_bug v2 $V2 sol_one_bug.py
run_arm starter v1 $V1 starter_solution.py;    run_arm starter v2 $V2 starter_solution.py
run_arm time_budget v1 $V1 sol_time_budget.py; run_arm time_budget v2 $V2 sol_time_budget.py
run_arm near_limit v1 $V1 sol_near_limit.py;   run_arm near_limit v2 $V2 sol_near_limit.py
docker image rm $V2 >/dev/null 2>&1; echo done >> $O/summary.txt
