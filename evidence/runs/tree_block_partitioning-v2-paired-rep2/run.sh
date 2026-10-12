#!/bin/bash
# Paired v1/v2 evaluation for tree_block_partitioning-v2 (E2B worker, root, /job).
# Every arm runs the task's ORIGINAL eval_cmd (all six subtasks) inside the judge image,
# --network none; only the image differs (v1 = pinned original, v2 = built from ../Dockerfile).
set -uo pipefail
V1=seededge/edgebench.judge.tree_block_partitioning@sha256:6ebbb44ab188660b15d260143e942ddcf0ba3bceb0bb7d7c78e976b1a36669d2
V2=ebv/tree_block_partitioning:v2
O=/job/out; mkdir -p $O/logs /job/sub
EVAL='cd /home/workspace/p1 && python3 /opt/p1_judge/prob/P1/eval.py --source-root /home/workspace/p1 --time-factor 1 --time-grace 0 --score-sum'
LIB=/opt/p1_judge/prob/P1/T2_P7881/data/interactive_lib.cpp
nproc > $O/env.txt; free -m >> $O/env.txt; docker version --format '{{.Server.Version}}' >> $O/env.txt
docker pull $V1 > $O/pull.log 2>&1 || { echo pull-failed; exit 2; }
docker build -t $V2 /job/pkg > $O/build.log 2>&1 || { echo build-failed; exit 3; }
docker image inspect $V2 --format '{{.Id}}' > $O/v2_image_id.txt
for img in $V1 $V2; do docker run --rm --network none $img sha256sum $LIB; done > $O/lib_sha.txt
# Reference sources and derived submissions (derivation scripts run in the judge image's python3).
docker run --rm --network none -v /job/sub:/sub -v /job/tools:/tools:ro $V1 bash -c '
set -e; P=/opt/p1_judge/prob/P1
mkdir -p /sub/ref /sub/alias /sub/invalid
for i in 1 2 3 4 5 6; do d=$(ls -d $P/T${i}_*); cp $d/std.cpp /sub/ref/T$i.cpp; : > /sub/alias/T$i.cpp; : > /sub/invalid/T$i.cpp; done
python3 -I /tools/make_alias_variant.py $P/T2_P7881/std.cpp /sub/alias/T2.cpp
python3 -I /tools/make_invalid_variant.py $P/T2_P7881/std.cpp /sub/invalid/T2.cpp
sha256sum /sub/*/T*.cpp' > $O/submissions_sha.txt 2>&1
run_arm() { # $1 arm  $2 version  $3 image
  local M=""; for i in 1 2 3 4 5 6; do M="$M -v /job/sub/$1/T$i.cpp:/home/workspace/p1/T$i.cpp:ro"; done
  local t0=$(date +%s)
  timeout 700 docker run --rm --network none --memory 4g --cpus 2 $M $3 bash -c "$EVAL" > $O/logs/$1-$2.log 2>&1
  local rc=$?; echo "$1 $2 exit=$rc wall=$(( $(date +%s) - t0 ))s $(grep -E '^TOTAL_SCORE' $O/logs/$1-$2.log)" | tee -a $O/summary.txt
}
for arm in ref alias invalid; do run_arm $arm v1 $V1; run_arm $arm v2 $V2; done
docker image rm $V2 >/dev/null 2>&1; echo done >> $O/summary.txt
