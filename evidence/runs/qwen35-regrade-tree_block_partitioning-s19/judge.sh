#!/bin/bash
# judge.sh IMAGE SUBDIR CWD TIMEOUT OUTPREFIX CPUS MEM
# Harness-equivalent single judgement (sforge run_evaluation.judge_submission, docker backend):
# fresh container from IMAGE (--network none), copy the archived submission.tar.gz into it, extract
# exactly the files listed in the archived allowed_files.txt (the list EdgeBench's harness itself
# extracted during the run) into CWD, inject the archived TaskSpec eval.sh at /tmp/eval.sh, run it
# as root (sforge DOCKER_USER) with the task timeout, save the raw capture. Container removed afterwards.
set -u
IMG=$1; S=$2; CWD=$3; TO=$4; OUT=$5; CPUS=$6; MEM=$7
name=rg_$$_$RANDOM
docker create --name $name --network none --cpus $CPUS --memory $MEM --entrypoint sleep $IMG infinity >/dev/null
docker start $name >/dev/null
NALLOW=-1
if [ -f $S/submission.tar.gz ]; then
  docker cp $S/submission.tar.gz $name:/tmp/submission.tar.gz
  if [ -s $S/allowed_files.txt ]; then
    NALLOW=$(grep -c . $S/allowed_files.txt)
    docker cp $S/allowed_files.txt $name:/tmp/allowed_files.txt
    docker exec -u root -w "$CWD" $name tar xzf /tmp/submission.tar.gz -T /tmp/allowed_files.txt > $OUT.extract.txt 2>&1
    echo "extract_rc=$?" >> $OUT.extract.txt
  else
    NALLOW=0; echo "no allowed_files: skeleton" > $OUT.extract.txt
  fi
fi
docker cp $S/eval.sh $name:/tmp/eval.sh
T0=$(date +%s.%N)
timeout --kill-after=10 $TO docker exec -u root -w "$CWD" $name /bin/bash /tmp/eval.sh > $OUT.raw.txt 2>&1
RC=$?
T1=$(date +%s.%N)
WALL=$(awk -v a=$T0 -v b=$T1 'BEGIN{printf "%.3f", b - a}')
echo "{\"rc\": $RC, \"timed_out\": $([ $RC = 124 ] && echo true || echo false), \"wall_s\": $WALL, \"n_allowed\": $NALLOW, \"cpus\": \"$CPUS\", \"mem\": \"$MEM\"}" > $OUT.status.json
docker rm -f $name >/dev/null
