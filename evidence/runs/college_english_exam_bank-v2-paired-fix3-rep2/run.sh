#!/bin/bash
# Paired v1/v2 offline evaluation for college_english_exam_bank (E2B job; root in /job).
# v1 = original judge image; v2 = built here from v2ctx/Dockerfile. Each fixed grading-model
# response is fed by a stand-in `codex` (fake_codex.sh); the ORIGINAL eval_cmd runs end to end
# inside the image with --network none. No model API, no credentials (dummy key strings only).
# Optional third arm v2prev: if /job/v2prevctx exists it is built the same way (the earlier
# fixed grader) and run on the same responses.
# If /job/pkg exists (a copy of the committed package without files/), v2 is regenerated there by
# the package's own materialize.sh and built from the package Dockerfile instead of v2ctx/.
set -x
J=seededge/edgebench.judge.college_english_exam_bank@sha256:8e9eec1057c7ab1b9b48d95cb493aa336b3ec3cea84df5bd80ad04d3009d58a8
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
docker build -t college_v2 $V2CTX > $O/v2_build.log 2>&1; echo "build_rc=$?" >> $O/v2_build.log
docker image inspect college_v2 --format '{{.Id}}' > $O/v2_image.txt
ARMS="v1 v2"
if [ -d /job/v2prevctx ]; then
  docker build -t college_v2prev /job/v2prevctx > $O/v2prev_build.log 2>&1; echo "build_rc=$?" >> $O/v2prev_build.log
  docker image inspect college_v2prev --format '{{.Id}}' > $O/v2prev_image.txt
  ARMS="v1 v2prev v2"
fi
for V in $ARMS; do
  case $V in v1) I=$J ;; v2) I=college_v2 ;; v2prev) I=college_v2prev ;; esac
  timeout 1200 docker run --rm --network none --cpus 2 --memory 3g -v /job:/p:ro -v $O:/o $I bash /p/in_container.sh $V
done
date -u
