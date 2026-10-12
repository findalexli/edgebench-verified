#!/bin/bash
# Paired v1/v2 offline evaluation for college_english_exam_bank (E2B job; root in /job).
# v1 = original judge image; v2 = built here from v2ctx/Dockerfile. Each fixed grading-model
# response is fed by a stand-in `codex` (fake_codex.sh); the ORIGINAL eval_cmd runs end to end
# inside the image with --network none. No model API, no credentials (dummy key strings only).
set -x
J=seededge/edgebench.judge.college_english_exam_bank@sha256:8e9eec1057c7ab1b9b48d95cb493aa336b3ec3cea84df5bd80ad04d3009d58a8
O=/job/out; mkdir -p $O; nproc; free -m; df -h / | tail -1; date -u
docker pull -q $J > $O/pull.log 2>&1
docker image inspect $J --format '{{.Id}} {{.Config.User}} {{.Config.WorkingDir}}' > $O/v1_image.txt
docker build -t college_v2 /job/v2ctx > $O/v2_build.log 2>&1; echo "build_rc=$?" >> $O/v2_build.log
docker image inspect college_v2 --format '{{.Id}}' > $O/v2_image.txt
for V in v1 v2; do
  [ $V = v1 ] && I=$J || I=college_v2
  timeout 1200 docker run --rm --network none --cpus 2 --memory 3g -v /job:/p:ro -v $O:/o $I bash /p/in_container.sh $V
done
date -u
