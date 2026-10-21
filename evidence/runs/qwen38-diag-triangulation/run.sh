#!/bin/bash
# Rule x inputs diagnosis (see ../qwen35-diag-triangulation) for the FINAL archive of the third-party
# Qwen3.8 Flash Next 12-hour run (fetched by HTTP range read, not redistributed).
set -u; . /job/params.env; O=/job/out; mkdir -p $O/logs; W=$CWD; V2=ebv-q35/$TASK:v2
command -v patch >/dev/null || (apt-get update -qq && apt-get install -y -qq patch) >/dev/null 2>&1
python3 -I /job/zipfetch.py /tmp/r "harness/$TASK/final_archive\.tar\.gz$" https://huggingface.co/datasets/adafadaq/edgebench-opus-5-5-xhigh-rollouts/resolve/main/qwen3.8-flash-next/qwen38fn-full47-part-02.zip > $O/logs/fetch.log 2>&1
docker pull -q $V1 > $O/logs/pull.log 2>&1
(cd /job/pkg && EDGEBENCH_ROOT=/job/ebv bash materialize.sh > $O/logs/materialize.log 2>&1; echo "rc=$?" >> $O/logs/materialize.log)
docker build -t $V2 /job/pkg > $O/logs/build.log 2>&1; echo "rc=$?" >> $O/logs/build.log
echo "v1 $(docker image inspect $V1 --format '{{.Id}}') v2 $(docker image inspect $V2 --format '{{.Id}}')" > $O/images.txt
A=$(find /tmp/r -name final_archive.tar.gz | head -1); sha256sum $A | cut -d' ' -f1 > $O/final_archive.sha256
mkdir -p /tmp/sub; tar xzf $A -C /tmp/sub; S=$(find /tmp/sub -name solution.py | head -1); echo "solution: ${S#/tmp/sub/}" > $O/solution_path.txt
for v in v1 v2; do I=$V1; [ $v = v2 ] && I=$V2; c=$(docker create $I); docker cp $c:$W/cases /tmp/cases_$v; docker rm $c >/dev/null; done
for rule in v1 v2; do I=$V1; [ $rule = v2 ] && I=$V2
 for inp in v1 v2; do
  docker run --rm --network none --cpus 4 --memory 6g -v /tmp/cases_$inp:/cases:ro -v $S:$W/solution.py:ro --entrypoint bash $I -c "cd $W; for f in /cases/*; do timeout 30 python3 solution.py < \$f > /tmp/o.txt 2>/dev/null; rc=\$?; t=\$(tools/bin/tester \$f /tmp/o.txt 2>&1 | grep -iE 'score|invalid|error' | head -1); echo \"\$(basename \$f) rc=\$rc \$t\"; done" > $O/m_final_rule${rule}_in${inp}.txt 2>&1
  echo "final rule=$rule inputs=$inp: $(grep -c 'Score' $O/m_final_rule${rule}_in${inp}.txt) scored, $(grep -ci invalid $O/m_final_rule${rule}_in${inp}.txt) invalid, $(grep -c 'rc=124' $O/m_final_rule${rule}_in${inp}.txt) timeouts" | tee -a $O/matrix.log
 done; done
