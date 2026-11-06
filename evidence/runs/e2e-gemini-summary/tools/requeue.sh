#!/bin/bash
# requeue.sh JOB...: keep the failed attempt as result-attemptN, refresh run.sh, and insert the job before END.
E=/home/alex/edgebench-verified/evidence/runs/e2e-gemini-summary/tools
cd /home/alex/edgebench-verified/evidence/runs
for j in "$@"; do
  n=1; while [ -e $j/result-attempt$n ]; do n=$((n+1)); done
  mv $j/result $j/result-attempt$n; mv $j.launch.log $j.attempt$n.launch.log
  cp $E/common/run.sh $j/run.sh
  sed -i "/^END$/i $j" $E/queue_e2e.txt
  echo "requeued $j (attempt $n kept)"
done
