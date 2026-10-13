#!/usr/bin/env bash
# One hidden suite hangs: what does the ORIGINAL arc_compiler_runtime judge report?
# Runs as root in /job on an E2B worker. Original judge image (pinned digest), original
# judge.eval_cmd (eval_cmd.sh, copied verbatim from tasks/arc_compiler_runtime.json), --network none.
# Each arm edits agent-start/compiler/src/runtime.js of the judge image's own starter (identical to
# the work image's compiler/src, checked locally with diff -r) with mutate.py, inside the container.
#   a_starter : shipped starter, unchanged (good control; expected 35.59 valid)
#   t_hang    : starter + an interpolation scanner whose "[" skip never advances (typo indexOf("[")
#               for indexOf("]")+1): an infinite loop on "{x[i]}" inside a string literal
#   t_throw   : same scanner, but it throws on "[" instead of looping (diagnostic: shows which
#               suites and cases reach the construct, and the score if the suite were scored 0/N)
set -u
cd /job; OUT=/job/out; mkdir -p $OUT
JUDGE=seededge/edgebench.judge.arc_compiler_runtime@sha256:00a344324ac466d6ea4b572218f8dacb41486df9044649762b670b3219eb579c
APP=/home/workspace/arc-compiler-runtime-implementation
{ nproc; free -m; date -u +%FT%TZ; } > $OUT/env.txt
docker pull -q $JUDGE > $OUT/pull.log 2>&1 || { echo PULL_FAILED; exit 2; }
docker image inspect --format '{{.Id}} {{json .RepoDigests}}' $JUDGE > $OUT/image_ids.txt
sha256sum mutate.py eval_cmd.sh > $OUT/inputs.sha256
echo "arm,wall_s,docker_exit,structured" > $OUT/summary.csv
for c in a_starter t_hang t_throw t_hang; do
  n=$c; [ -f $OUT/hidden_$c.log ] && n=${c}_rep2
  t0=$(date +%s)
  docker run --rm --network none --memory 4g --cpus 2 -v $PWD/mutate.py:/p/mutate.py:ro -v $PWD/eval_cmd.sh:/tmp/eval_cmd.sh:ro $JUDGE \
    bash -c "R=$APP/agent-start/compiler/src/runtime.js; python /p/mutate.py $c \$R && node --check \$R && sha256sum \$R && timeout 1500 bash /tmp/eval_cmd.sh" > $OUT/hidden_$n.log 2>&1
  ex=$?; t1=$(date +%s)
  js=$(sed -n '/>>>>> Start Structured Result/{n;p}' $OUT/hidden_$n.log | python3 -c 'import sys,json;d=json.loads(sys.stdin.read());m=d["metrics"];print(json.dumps({"valid":d["valid"],"score":d["score"],"pass_rate":d["pass_rate"],"passed":d["passed"],"runner_returncode":m["runner_returncode"],"summary":d["summary"]}).replace(",",";"))' 2>&1)
  echo "$n,$((t1-t0)),$ex,$js" >> $OUT/summary.csv
  grep -E '^\s+(strengthened|extra)/|HIDDEN_INFRA_ERROR|SCORE_STATUS|^SCORE=|RUNNER_|FAIL: .*interpolation|diagnostic' $OUT/hidden_$n.log > $OUT/suites_$n.txt
done
cat $OUT/summary.csv
date -u +%FT%TZ >> $OUT/env.txt
