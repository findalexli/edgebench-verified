#!/bin/bash
# Prompt revision check for borden_source_inversion-v2 (E2B worker, root, /job), 2026-10-12.
# The revision changes only text (README.md in the work image and work.agent_query). The judge image
# is UNCHANGED (pinned v1 digest); every arm runs the ORIGINAL eval_cmd with --network none.
#   v1:     case/submission dir = original v1 work dir + answer.json
#   v2prev: work dir from the first published fixed work image (pkgprev/: previous README.md)
#   v2:     work dir from the revised fixed work image (pkg/: revised README.md)
# The answers are the fixed inputs of run r2 (v2_fit.json = r2's answer_v2_fit.json); no solver runs.
set -uo pipefail
J=seededge/edgebench.judge.borden_source_inversion@sha256:b1a08348b8257d8bbe8a559d76ca5333afa60ac02a82656724d7406913d16dd8
W1=seededge/edgebench.work.borden_source_inversion@sha256:e1ec4b80816e46760c226c902817751e9a905395828b777ce20c563d1843826a
WS=/home/workspace/borden_inverse
EVAL="python /opt/borden_scoring/evaluate.py --submission_dir $WS --case_dir $WS --scoring_dir /opt/borden_scoring --output $WS/score.json"
O=/job/out; mkdir -p $O/logs $O/scores /job/wd /job/run
{ nproc; free -m; docker version --format '{{.Server.Version}}'; date -u; } > $O/env.txt
for i in $J $W1; do docker pull $i >> $O/pull.log 2>&1 || { echo pull-failed $i | tee $O/summary.txt; exit 2; }; done
docker build -t ebv/borden-work:v2prev /job/pkgprev > $O/build.log 2>&1 || { echo build-failed v2prev | tee $O/summary.txt; exit 3; }
docker build -t ebv/borden-work:v2 /job/pkg >> $O/build.log 2>&1 || { echo build-failed v2 | tee $O/summary.txt; exit 3; }
docker image inspect ebv/borden-work:v2prev ebv/borden-work:v2 --format '{{.Id}} {{.RepoTags}}' > $O/work_image_ids.txt
for v in v1 v2prev v2; do img=$W1; [ $v != v1 ] && img=ebv/borden-work:$v
  c=$(docker create $img true); docker cp $c:$WS /job/wd/$v; docker rm $c >/dev/null
  rm -rf /job/wd/$v/.git /job/wd/$v/answer.json
  (cd /job/wd/$v && ls -la && sha256sum *) > $O/workdir_$v.txt 2>&1; done
diff -r /job/wd/v1 /job/wd/v2prev > $O/workdir_diff_v1_v2prev.txt 2>&1
diff -r /job/wd/v2prev /job/wd/v2 > $O/workdir_diff_v2prev_v2.txt 2>&1
sha256sum /job/inputs/* > $O/submissions_sha.txt
run_arm() { # $1 arm  $2 version
  local d=/job/run/$1-$2; rm -rf $d; cp -r /job/wd/$2 $d
  [ -f /job/inputs/$1.json ] && cp /job/inputs/$1.json $d/answer.json
  timeout 700 docker run --rm --network none --cpus 2 --memory 2g -v $d:$WS $J bash -c "$EVAL" > $O/logs/$1-$2.log 2>&1
  local rc=$?
  [ -f $d/score.json ] && cp $d/score.json $O/scores/$1-$2.json
  echo "$1 $2 exit=$rc $(grep -E '^TOTAL_SCORE|^RAW_TOTAL_SCORE' $O/logs/$1-$2.log | tr '\n' ' ')" | tee -a $O/summary.txt
}
for arm in textbook_fit judgeconv_fit baseline_mid truth v2_fit invalid_oob invalid_missing; do for v in v1 v2prev v2; do run_arm $arm $v; done; done
docker image rm ebv/borden-work:v2prev ebv/borden-work:v2 >/dev/null 2>&1; echo done >> $O/summary.txt
