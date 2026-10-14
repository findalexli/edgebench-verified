#!/bin/bash
# Paired v1/v2 evaluation for graph_node_classification (E2B job; root in /job).
# v1 = original judge image; v2 = built here from v2ctx/Dockerfile. Original eval_cmd via the
# TaskSpec eval.sh, --network none, full 10-split run, 4 workers (as in the review).
set -x
J=seededge/edgebench.judge.graph_node_classification@sha256:518c105ec283ea9231ecb87886e0937c14a7bd937d8e385afaa3369800c5c3bd
CWD=/home/workspace/045_graph_node_classification
O=/job/out; mkdir -p $O; nproc; free -m; df -h / | tail -1; date -u
docker pull -q $J > $O/pull.log 2>&1
docker image inspect $J --format '{{.Id}} {{.Config.User}} {{.Config.WorkingDir}}' > $O/v1_image.txt
docker build -t graph_v2 /job/v2ctx > $O/v2_build.log 2>&1; echo "build_rc=$?" >> $O/v2_build.log
docker image inspect graph_v2 --format '{{.Id}}' > $O/v2_image.txt
for V in v1 v2; do
  [ $V = v1 ] && I=$J || I=graph_v2
  docker run --rm --network none $I bash -c "cd $CWD && sha256sum verifier.py runner.py judge_eval.py config.yaml solution/solution.py solution/solution_template.py" > $O/pins_$V.txt 2>&1
done
for m in baseline shrink neighbor nanconf missing_half; do
  for V in v1 v2; do
    [ $V = v1 ] && I=$J || I=graph_v2
    bash /job/judge_one.sh $I /job/subs/$m $CWD 1800 $O/$V.$m 4 6g SEB_PARALLEL_WORKERS=4
  done
done
date -u
