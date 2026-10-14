#!/bin/bash
# judge_one.sh IMAGE SUBDIR CWD TIMEOUT OUTPREFIX [CPUS] [MEM] [ENV...]
# Harness-equivalent single judgement (sforge run_evaluation.judge_submission, docker backend):
# fresh container from IMAGE (--network none), copy the submitted files from SUBDIR into CWD
# (SUBDIR mirrors CWD-relative submit paths; only those files are copied), inject the
# TaskSpec-generated ${EVAL_SH:-/job/eval.sh} at /tmp/eval.sh, run it as root with the task timeout,
# save the raw capture. Container removed afterwards.
set -u
IMG=$1; SUB=$2; CWD=$3; TO=$4; OUT=$5; CPUS=${6:-2}; MEM=${7:-4g}; shift 7 2>/dev/null || shift $#
ENVARGS=(); for e in "$@"; do ENVARGS+=(-e "$e"); done
name=jd_$$_$RANDOM
docker create --name $name --network none --cpus $CPUS --memory $MEM "${ENVARGS[@]}" --entrypoint sleep $IMG infinity >/dev/null
docker start $name >/dev/null
if [ -n "$SUB" ] && [ -d "$SUB" ]; then
  (cd "$SUB" && find . -type f ! -name .keep | sed 's#^\./##' | sort) > $OUT.files.txt
  tar -C "$SUB" --exclude=.keep -cf - . | docker exec -i -w "$CWD" $name tar -xf -
fi
docker cp ${EVAL_SH:-/job/eval.sh} $name:/tmp/eval.sh
T0=$(date +%s.%N)
timeout --kill-after=10 $TO docker exec -w "$CWD" $name /bin/bash /tmp/eval.sh > $OUT.raw.txt 2>&1
RC=$?
T1=$(date +%s.%N)
WALL=$(awk -v a=$T0 -v b=$T1 'BEGIN{printf "%.3f", b - a}')
echo "{\"rc\": $RC, \"timed_out\": $([ $RC = 124 ] && echo true || echo false), \"wall_s\": $WALL}" > $OUT.status.json
docker rm -f $name >/dev/null
