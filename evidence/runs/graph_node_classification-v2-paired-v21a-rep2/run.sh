#!/bin/bash
# Paired v1/v2 evaluation for graph_node_classification (E2B job; root in /job).
# v1 = original judge image; v2 = built here from v2ctx/Dockerfile. Original eval_cmd via the
# TaskSpec eval.sh, --network none, full 10-split run, 4 workers (as in the review).
# If /job/pkg exists (a copy of the committed package without files/), v2 is regenerated there by
# the package's own materialize.sh and built from the package Dockerfile instead of v2ctx/.
# Optional third arm v2prev: if /job/v2prevctx exists it is built the same way (the earlier fixed
# verifier) and run on the same submissions. /job/subs.txt, if present, lists the submissions.
set -x
J=seededge/edgebench.judge.graph_node_classification@sha256:518c105ec283ea9231ecb87886e0937c14a7bd937d8e385afaa3369800c5c3bd
CWD=/home/workspace/045_graph_node_classification
O=/job/out; mkdir -p $O; nproc; free -m; df -h / | tail -1; date -u
docker pull -q $J > $O/pull.log 2>&1
docker image inspect $J --format '{{.Id}} {{.Config.User}} {{.Config.WorkingDir}}' > $O/v1_image.txt
V2CTX=/job/v2ctx
if [ -d /job/pkg ]; then
  command -v patch > /dev/null || (apt-get update -qq && apt-get install -y -qq patch) > $O/apt_patch.log 2>&1
  bash /job/pkg/materialize.sh > $O/materialize.log 2>&1; echo "materialize_rc=$?" >> $O/materialize.log
  (cd /job/pkg && sha256sum Dockerfile $(find files -type f | sort)) > $O/materialized_sha256.txt
  V2CTX=/job/pkg
fi
docker build -t graph_v2 $V2CTX > $O/v2_build.log 2>&1; echo "build_rc=$?" >> $O/v2_build.log
docker image inspect graph_v2 --format '{{.Id}}' > $O/v2_image.txt
ARMS="v1 v2"
if [ -d /job/v2prevctx ]; then
  docker build -t graph_v2prev /job/v2prevctx > $O/v2prev_build.log 2>&1; echo "build_rc=$?" >> $O/v2prev_build.log
  docker image inspect graph_v2prev --format '{{.Id}}' > $O/v2prev_image.txt
  ARMS="v1 v2prev v2"
fi
img() { case $1 in v1) echo $J ;; v2) echo graph_v2 ;; v2prev) echo graph_v2prev ;; esac; }
for V in $ARMS; do
  docker run --rm --network none $(img $V) bash -c "cd $CWD && sha256sum verifier.py runner.py judge_eval.py config.yaml solution/solution.py solution/solution_template.py" > $O/pins_$V.txt 2>&1
done
SUBS="baseline shrink neighbor nanconf missing_half"; [ -f /job/subs.txt ] && SUBS=$(cat /job/subs.txt)
for m in $SUBS; do
  for V in $ARMS; do
    bash /job/judge_one.sh $(img $V) /job/subs/$m $CWD 1800 $O/$V.$m 4 6g SEB_PARALLEL_WORKERS=4
  done
done
date -u
