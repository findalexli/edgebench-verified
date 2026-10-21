#!/bin/bash
# 2x2 diagnosis: rule (tester image v1/v2) x inputs (cases from v1/v2) for one archived submission.
. /job/params.env; W=$CWD; V2=ebv-q35/$TASK:v2
for v in v1 v2; do I=$V1; [ $v = v2 ] && I=$V2; c=$(docker create $I); rm -rf /tmp/cases_$v; docker cp $c:$W/cases /tmp/cases_$v; docker rm $c >/dev/null; done
for r in $ROUNDS; do S=/tmp/r/export-qwen35-full47/harness/$TASK/submissions/$r; mkdir -p /tmp/sub_$r; tar xzf $S/submission.tar.gz -C /tmp/sub_$r solution.py
 for rule in v1 v2; do I=$V1; [ $rule = v2 ] && I=$V2
  for inp in v1 v2; do
   docker run --rm --network none --cpus 4 --memory 6g -v /tmp/cases_$inp:/cases:ro -v /tmp/sub_$r/solution.py:$W/solution.py:ro --entrypoint bash $I -c "cd $W; for f in /cases/*; do timeout 30 python3 solution.py < \$f > /tmp/o.txt 2>/dev/null; rc=\$?; t=\$(tools/bin/tester \$f /tmp/o.txt 2>&1 | grep -iE 'score|invalid|error' | head -1); echo \"\$(basename \$f) rc=\$rc \$t\"; done" > /job/out/m_${r}_rule${rule}_in${inp}.txt 2>&1
   echo "$r rule=$rule inputs=$inp: $(grep -c 'Score' /job/out/m_${r}_rule${rule}_in${inp}.txt) scored, $(grep -ci invalid /job/out/m_${r}_rule${rule}_in${inp}.txt) invalid, $(grep -c 'rc=124' /job/out/m_${r}_rule${rule}_in${inp}.txt) timeouts"
  done; done; done
