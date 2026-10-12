#!/bin/bash
# Paired v1/v2 evaluation for borden_source_inversion-v2 (E2B worker, root, /job).
# Judge image is UNCHANGED (pinned v1 digest); every arm runs the ORIGINAL eval_cmd with
# --network none. v1 arm: case/submission dir = v1 work dir + answer.json.
# v2 arm: case/submission dir = v2 work dir (built from ../Dockerfile) + the same answer.json.
# Extra arm v2_fit: an honest solver that uses only the shipped v2 forward_model.py,
# run inside the v2 work image with --network none.
set -uo pipefail
J=seededge/edgebench.judge.borden_source_inversion@sha256:b1a08348b8257d8bbe8a559d76ca5333afa60ac02a82656724d7406913d16dd8
W1=seededge/edgebench.work.borden_source_inversion@sha256:e1ec4b80816e46760c226c902817751e9a905395828b777ce20c563d1843826a
W2=ebv/borden_source_inversion-work:v2
WS=/home/workspace/borden_inverse
EVAL="python /opt/borden_scoring/evaluate.py --submission_dir $WS --case_dir $WS --scoring_dir /opt/borden_scoring --output $WS/score.json"
O=/job/out; mkdir -p $O/logs $O/scores /job/wd /job/run
{ nproc; free -m; docker version --format '{{.Server.Version}}'; date -u; } > $O/env.txt
for i in $J $W1; do docker pull $i >> $O/pull.log 2>&1 || { echo pull-failed $i | tee $O/summary.txt; exit 2; }; done
docker build -t $W2 /job/pkg > $O/build.log 2>&1 || { echo build-failed | tee $O/summary.txt; exit 3; }
docker image inspect $W2 --format '{{.Id}}' > $O/v2_work_image_id.txt
for v in v1 v2; do img=$W1; [ $v = v2 ] && img=$W2
  c=$(docker create $img true); docker cp $c:$WS /job/wd/$v; docker rm $c >/dev/null
  rm -rf /job/wd/$v/.git /job/wd/$v/answer.json
  (cd /job/wd/$v && ls -la && sha256sum *) > $O/workdir_$v.txt 2>&1; done
diff -r /job/wd/v1 /job/wd/v2 > $O/workdir_diff.txt 2>&1
# Shipped forward model vs hidden labels and vs the judge's own model (inside the judge image).
docker run --rm --network none --memory 2g -v /job/wd/v2:/ship:ro -v /job/tools:/tools:ro $J \
  python /tools/label_check.py /ship $WS /opt/borden_scoring > $O/label_check.txt 2>&1
# Honest v2 solver: only the v2 work dir, inside the v2 work image.
mkdir -p /job/solve; cp -r /job/wd/v2/. /job/solve/
t0=$(date +%s)
timeout 2000 docker run --rm --network none --cpus 8 --memory 6g -v /job/solve:/w -v /job/tools:/tools:ro $W2 \
  python /tools/v2_solver.py /w /w/answer_v2_fit.json > $O/v2_solver.log 2>&1
echo "v2_solver exit=$? wall=$(( $(date +%s) - t0 ))s" >> $O/v2_solver.log
[ -f /job/solve/answer_v2_fit.json ] && cp /job/solve/answer_v2_fit.json /job/inputs/v2_fit.json && cp /job/solve/answer_v2_fit.json $O/
sha256sum /job/inputs/* > $O/submissions_sha.txt
run_arm() { # $1 arm  $2 version
  local d=/job/run/$1-$2; rm -rf $d; cp -r /job/wd/$2 $d
  [ -f /job/inputs/$1.json ] && cp /job/inputs/$1.json $d/answer.json
  timeout 700 docker run --rm --network none --cpus 2 --memory 2g -v $d:$WS $J bash -c "$EVAL" > $O/logs/$1-$2.log 2>&1
  local rc=$?
  [ -f $d/score.json ] && cp $d/score.json $O/scores/$1-$2.json
  echo "$1 $2 exit=$rc $(grep -E '^TOTAL_SCORE|^RAW_TOTAL_SCORE' $O/logs/$1-$2.log | tr '\n' ' ')" | tee -a $O/summary.txt
}
for arm in textbook_fit judgeconv_fit baseline_mid truth v2_fit invalid_oob invalid_missing; do run_arm $arm v1; run_arm $arm v2; done
docker image rm $W2 >/dev/null 2>&1; echo done >> $O/summary.txt
