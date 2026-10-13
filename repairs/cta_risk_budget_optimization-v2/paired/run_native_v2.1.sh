#!/bin/bash
# CTA v2.1 native paired run (E2B worker, root, /job). Every arm runs the task's ORIGINAL eval_cmd
# (`cd /home/workspace && python3 scoring/score.py`) with --network none --memory 3g --cpus 2.
#  v1        pinned original judge image
#  v21       image built from pkg/ (this package: materialize.sh in the worker, then docker build)
#  v21strict image built from pkg-strict/ (the superseded first v2.1 candidate; only with ARMS_STRICT=1)
# Submissions: the shipped standard answer (scoring/standard_answer_artifacts.tar.gz, extracted as in
# the historical run), and paired/full_submission/main.py with config-<arm>.json (run by run_eval.py).
# REP_FULL=1 also runs the standard answer and the date-alignment census.
set -uo pipefail
V1=seededge/edgebench.judge.cta_risk_budget_optimization@sha256:34258d854f41e9cd5fc179fadbc6348bb8ff4118506b1862273f2a2a6d941b32
O=/job/out; mkdir -p $O/logs $O/results
{ nproc; free -m; df -h /; docker version --format '{{.Server.Version}}'; date -u; } > $O/env.txt 2>&1
docker pull -q $V1 > $O/pull.log 2>&1 || { echo pull-failed | tee -a $O/summary.txt; exit 2; }
docker image inspect $V1 --format '{{.Id}} {{.RepoDigests}}' >> $O/pull.log
command -v patch >/dev/null || { (apt-get update -qq && apt-get install -y -qq patch) > $O/apt.log 2>&1; }
IMGS="v1=$V1"
build() { # $1 label $2 pkgdir
  ( cd /job/$2 && bash materialize.sh ) > $O/materialize-$1.log 2>&1 || { echo "materialize-$1 failed" | tee -a $O/summary.txt; exit 4; }
  sha256sum /job/$2/files/eval_script.py | tee $O/eval_sha-$1-pkg.txt
  docker build -t ebv/cta:$1 /job/$2 > $O/build-$1.log 2>&1 || { echo "build-$1 failed" | tee -a $O/summary.txt; exit 3; }
  docker image inspect ebv/cta:$1 --format '{{.Id}}' > $O/image_id-$1.txt
  IMGS="$IMGS $1=ebv/cta:$1"
}
build v21 pkg
[ "${ARMS_STRICT:-0}" = 1 ] && build v21strict pkg-strict
for kv in $IMGS; do docker run --rm --network none --entrypoint bash ${kv#*=} -c 'sha256sum /home/workspace/scoring/eval_script.py' | sed "s|^|${kv%%=*} |"; done > $O/eval_sha_images.txt
COLLECT='cp /home/workspace/eval_results.json /out/eval_results.json 2>/dev/null; true'
run_arm() { # $1 arm $2 label $3 image $4 setup-cmd
  local arm=$1 lab=$2 img=$3 setup=$4 d=$O/results/$1-$2; mkdir -p $d; [ -d $d/rep ] || true
  local t0=$(date +%s)
  timeout 900 docker run --rm --network none --memory 3g --cpus 2 -v /job/sub:/sub:ro -v $d:/out --entrypoint bash $img \
    -c "$setup && cd /home/workspace && python3 scoring/score.py; $COLLECT" > $d/stdout.log 2>&1
  local rc=$?
  local ts=$(grep -E '^TOTAL_SCORE' $d/stdout.log | tail -1)
  local cb=$(python3 -c "import json,sys;d=json.load(open('$d/eval_results.json'));r=d['details'].get('risk_constraints',{});print('grand_total=%s risk=%s cross_border=%s gate_failed=%s' % (d['scores'].get('grand_total'), d['scores'].get('risk_constraints'), r.get('cross_border'), r.get('gate_failed',False)))" 2>/dev/null)
  echo "$arm $lab exit=$rc wall=$(( $(date +%s) - t0 ))s $ts $cb | $(grep -E 'Overseas ratio|Veto' $d/stdout.log | head -2 | tr -s ' ' | tr '\n' ' ')" | tee -a $O/summary.txt
}
chmod -R a+rX /job/sub; chmod -R a+rwX $O/results
if [ "${REP_FULL:-0}" = 1 ]; then
  docker run --rm --network none --entrypoint bash $V1 -c 'cd /tmp && tar -xzf /home/workspace/scoring/standard_answer_artifacts.tar.gz ./backtest_results && python3 -c "
import pandas as pd
n=pd.read_csv(\"backtest_results/daily_nav.csv\"); p=pd.read_csv(\"backtest_results/positions.csv\")
nd=set(pd.to_datetime(n[\"date\"])); hd=set(pd.to_datetime(p[\"date\"]))
print(\"standard answer: nav dates\",len(nd),\"holdings dates\",len(hd),\"holdings dates without same-date NAV\",len(hd-nd),\"nav column first value\",n[\"nav\"].iloc[0])
"' > $O/standard_answer_dates.txt 2>&1
  for kv in $IMGS; do run_arm standard_answer ${kv%%=*} ${kv#*=} 'cd /home/workspace && tar -xzf scoring/standard_answer_artifacts.tar.gz -C /home/workspace'; done
fi
for arm in ${ARMS:-leveraged unleveraged unleveraged-navgap}; do
  for kv in $IMGS; do run_arm $arm ${kv%%=*} ${kv#*=} "cp /sub/main.py /home/workspace/main.py && cp /sub/config-$arm.json /home/workspace/config.json"; done
done
date -u >> $O/env.txt
for kv in $IMGS; do [ "${kv%%=*}" = v1 ] || docker image rm ${kv#*=} >/dev/null 2>&1; done
rm -rf /job/pkg/files /job/pkg-strict/files; echo done >> $O/summary.txt
