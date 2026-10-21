#!/bin/bash
# Regrade archived Qwen3.5-122B submissions (third-party rollouts, fetched on the worker by HTTP range reads,
# not redistributed) with the original judge image (pinned digest) and the fixed one (built from the repair
# package). Same method as opus55-regrade2: judge.sh reproduces sforge judge_submission, one container at a
# time, --network none --cpus 4 --memory 6g. plan.txt: one round per line. params.env: TASK V1 CWD TO1 TO2 PARTS.
# Adaptive deadline: a round starts only if (v1+v2 time of the slowest round so far) * 1.3 fits.
set -u
. /job/params.env
START=$(date +%s); DEADLINE=$((START + ${INNER_BUDGET:-3000}))
O=/job/out; mkdir -p $O/raw $O/logs
command -v patch >/dev/null || (apt-get update -qq && apt-get install -y -qq patch) >/dev/null 2>&1
{ nproc; free -m; df -h / | tail -1; lscpu | grep "Model name"; docker version --format '{{.Server.Version}}'; } > $O/env.txt 2>&1
B=https://huggingface.co/datasets/adafadaq/edgebench-opus-5-5-xhigh-rollouts/resolve/main/qwen3.5-122b-a10b
URLS=""; for p in $PARTS; do URLS="$URLS $B/qwen35-full47-part-$p.zip"; done
RX="harness/$TASK/submissions/($(paste -sd'|' /job/plan.txt))/(submission\.tar\.gz|eval\.sh|allowed_files\.txt)\$"
python3 -I /job/zipfetch.py /tmp/r "$RX" $URLS > $O/logs/fetch.log 2>&1; echo "rc=$?" >> $O/logs/fetch.log
docker pull -q $V1 > $O/logs/pull.log 2>&1; echo "rc=$?" >> $O/logs/pull.log
(cd /job/pkg && EDGEBENCH_ROOT=/job/ebv bash materialize.sh > $O/logs/materialize.log 2>&1; echo "rc=$?" >> $O/logs/materialize.log)
docker build -t ebv-q35/$TASK:v2 /job/pkg > $O/logs/build.log 2>&1; echo "rc=$?" >> $O/logs/build.log
echo "$TASK v1 $(docker image inspect $V1 --format '{{.Id}}') v2 $(docker image inspect ebv-q35/$TASK:v2 --format '{{.Id}}')" > $O/images.txt
echo "setup_s=$(( $(date +%s) - START ))" > $O/progress.txt
MAXR=0
while read -r r; do
  [ -z "$r" ] && continue
  S=/tmp/r/export-qwen35-full47/harness/$TASK/submissions/$r
  if [ ! -f "$S/eval.sh" ]; then echo "$r missing" >> $O/progress.txt; continue; fi
  if [ $(( $(date +%s) + MAXR * 13 / 10 + 30 )) -gt $DEADLINE ]; then echo "$r skipped-deadline" >> $O/progress.txt; continue; fi
  (cd $S && sha256sum submission.tar.gz eval.sh allowed_files.txt 2>/dev/null) > $O/raw/$TASK.$r.sha256
  T0=$(date +%s)
  [ "${V2_ONLY:-0}" = 1 ] || bash /job/judge.sh $V1 $S $CWD $TO1 $O/raw/$TASK.$r.rep1.v1 4 6g
  bash /job/judge.sh ebv-q35/$TASK:v2 $S $CWD $TO2 $O/raw/$TASK.$r.rep1.v2 4 6g
  DT=$(( $(date +%s) - T0 )); [ $DT -gt $MAXR ] && MAXR=$DT
  echo "$r done ${DT}s" >> $O/progress.txt
done < /job/plan.txt
docker image rm ebv-q35/$TASK:v2 >/dev/null 2>&1; echo done > $O/done
