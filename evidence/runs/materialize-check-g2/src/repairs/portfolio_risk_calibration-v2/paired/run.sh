#!/bin/bash
# Paired original/fixed run for portfolio_risk_calibration-v2 (E2B worker, root, /job).
# v1 = digest-pinned original judge image; v2 = built from /job/pkg after ./materialize.sh regenerates
# files/eval_script.py from v1 + repair.patch (sha256-checked). Every full arm runs the task's eval_cmd
# (cd /home/workspace && python3 scoring/score.py) with --network none --memory 2g --cpus 2, one at a time.
# Arms: a/b/c from /job/pkg/paired/fixture_optimizer.py (arms.txt); d_starter = the work image's
# /home/workspace submit_paths files as shipped; e_example = the judge image's own scoring/portfolio_optimizer.py.
# threshold_paths.py calls each image's installed metric and score functions on authored NAV paths.
set -uo pipefail
V1=seededge/edgebench.judge.portfolio_risk_calibration@sha256:42997fb5770532b08cf9b97927d28f34466868348cc75ae13824b81c90e9458d
WORK=seededge/edgebench.work.portfolio_risk_calibration:e9e47d60871d
V2=ebv/portfolio_risk_calibration:v2
O=/job/out; mkdir -p $O/logs $O/reports
{ nproc; free -m; docker version --format '{{.Server.Version}}'; date -u; command -v patch; } > $O/env.txt 2>&1
# GNU patch is not on the worker image: install it on the worker (not in any task image)
command -v patch >/dev/null || { (apt-get update -qq && DEBIAN_FRONTEND=noninteractive apt-get install -y -qq patch) > $O/apt.log 2>&1; }
command -v patch >/dev/null || { echo no-patch | tee -a $O/summary.txt; exit 4; }
patch --version | head -1 >> $O/env.txt
docker pull $V1 > $O/pull.log 2>&1 || { echo pull-failed | tee -a $O/summary.txt; exit 2; }
docker image inspect $V1 --format '{{.Id}} {{.RepoDigests}}' > $O/image.txt
( cd /job/pkg && ./materialize.sh ) > $O/materialize.log 2>&1 || { echo materialize-failed | tee -a $O/summary.txt; exit 3; }
docker build -t $V2 /job/pkg > $O/build.log 2>&1 || { echo build-failed | tee -a $O/summary.txt; exit 3; }
docker image inspect $V2 --format '{{.Id}}' > $O/v2_image_id.txt
rm -rf /job/pkg/files   # image-derived; never collected

# submissions
SUB=/job/subs; mkdir -p $SUB
grep -v '^#' /job/pkg/paired/arms.txt | while read -r label gross sign formula; do
  mkdir -p $SUB/$label
  sed -e "s/^GROSS = 1.0$/GROSS = $gross/" -e "s/^SIGN = 1$/SIGN = $sign/" \
      -e "s/^EXCESS_FORMULA = 'stated'/EXCESS_FORMULA = '$formula'/" \
      /job/pkg/paired/fixture_optimizer.py > $SUB/$label/portfolio_optimizer.py
  grep -E '^(GROSS|SIGN|EXCESS_FORMULA) =' $SUB/$label/portfolio_optimizer.py | tr '\n' ' ' | sed "s/^/$label: /" >> $O/arms_resolved.txt; echo >> $O/arms_resolved.txt
done
sha256sum $SUB/*/portfolio_optimizer.py /job/pkg/paired/fixture_optimizer.py > $O/fixtures_sha.txt
docker pull $WORK > $O/pull_work.log 2>&1 && docker image inspect $WORK --format '{{.Id}} {{.RepoDigests}}' > $O/work_image.txt
mkdir -p $SUB/d_starter
docker run --rm --network none --entrypoint bash $WORK -c 'ls -la /home/workspace; find /home/workspace -maxdepth 2 -type f | sort | xargs sha256sum' > $O/work_inventory.txt 2>&1
CID=$(docker create $WORK true)
for f in portfolio_optimizer.py requirements.txt backtest_results.json; do docker cp -L $CID:/home/workspace/$f $SUB/d_starter/$f 2>/dev/null && echo "starter has $f"; done >> $O/work_inventory.txt
docker rm $CID >/dev/null
ls -la $SUB/d_starter >> $O/work_inventory.txt
mkdir -p $SUB/e_example   # filled from the judge image itself at run time (cp scoring/portfolio_optimizer.py)

for v in v1 v2; do img=$V1; [ $v = v2 ] && img=$V2
  docker run --rm --network none --entrypoint bash $img -c 'sha256sum /home/workspace/scoring/eval_script.py; ls -l /home/workspace/scoring/eval_script.py; sed -n 925,928p /home/workspace/scoring/eval_script.py' > $O/eval_sha-$v.txt 2>&1
  for arm in a_instructions b_grader c_wrong d_starter e_example; do
    mkdir -p $O/reports/$arm-$v; chmod 777 $O/reports/$arm-$v
    PRE='cp -r /sub/. /home/workspace/'
    [ $arm = e_example ] && PRE='cp /home/workspace/scoring/portfolio_optimizer.py /home/workspace/portfolio_optimizer.py'
    KEEP='cp /home/workspace/score_report.json /out/ 2>/dev/null; cp /home/workspace/backtest_results.json /out/ 2>/dev/null'
    case $arm in d_starter|e_example) KEEP='cp /home/workspace/score_report.json /out/ 2>/dev/null';; esac
    t0=$(date +%s)
    timeout 900 docker run --rm --network none --memory 2g --cpus 2 -v $SUB/$arm:/sub:ro -v $O/reports/$arm-$v:/out \
      --entrypoint bash $img -c "$PRE; cd /home/workspace && python3 scoring/score.py; rc=\$?; $KEEP; exit \$rc" > $O/logs/$arm-$v.log 2>&1
    rc=$?
    echo "$arm $v exit=$rc cpus=2 secs=$(( $(date +%s) - t0 )) $(grep -E '^TOTAL_SCORE' $O/logs/$arm-$v.log | tr '\n' ' ')" | tee -a $O/summary.txt
  done
  timeout 600 docker run --rm --network none --memory 2g --cpus 2 -v /job/pkg/paired:/s:ro --entrypoint python3 $img -I /s/threshold_paths.py > $O/logs/threshold-$v.log 2>&1
  echo "threshold $v exit=$? cpus=2" | tee -a $O/summary.txt
done
docker image rm $V2 >/dev/null 2>&1; echo done >> $O/summary.txt
