#!/usr/bin/env bash
# Paired evaluation for arc_compiler_runtime v2 (documentation-only repair of the work image).
# Runs as root in /job on an E2B worker with Docker. Layout expected in /job:
#   Dockerfile, files/ (v2 build context), controls/<name>/ (compiler/src overlays), eval_cmd.sh (original judge.eval_cmd)
# For each version (v1 = original work image, v2 = image built from Dockerfile) and each control:
#   compiler/src is taken from that version's work image, the control overlay is applied, and the
#   submission is scored by the ORIGINAL judge image with the ORIGINAL eval_cmd under --network none.
#   The public score.sh is also run inside the work image (what a solver sees).
set -u
cd /job; OUT=/job/out; mkdir -p $OUT
WORK=seededge/edgebench.work.arc_compiler_runtime@sha256:3d90ab273261321579e7e18d6fd6e9ef75b3a97512f09b3729b898a6ad23eaf9
JUDGE=seededge/edgebench.judge.arc_compiler_runtime@sha256:00a344324ac466d6ea4b572218f8dacb41486df9044649762b670b3219eb579c
APP=/home/workspace/arc-compiler-runtime-implementation
date -u +%FT%TZ > $OUT/started
docker pull -q $WORK > $OUT/pull.log 2>&1 && docker pull -q $JUDGE >> $OUT/pull.log 2>&1 || { echo PULL_FAILED; exit 2; }
docker build -q -t arc-v2-work:local -f Dockerfile files > $OUT/build.log 2>&1 || { echo BUILD_FAILED; cat $OUT/build.log; exit 3; }
docker image inspect --format '{{.Id}}' $WORK arc-v2-work:local $JUDGE > $OUT/image_ids.txt
# solver-visible diff v1 -> v2 (whole agent-start tree, node_modules excluded)
for v in v1 v2; do
  img=$WORK; [ $v = v2 ] && img=arc-v2-work:local
  cid=$(docker create $img); mkdir -p src/$v
  docker cp $cid:$APP/agent-start - | tar -xf - -C src/$v --exclude='agent-start/node_modules'
  docker rm $cid >/dev/null
  docker run --rm --network none $img bash -c 'git status --short' > $OUT/git_status_$v.txt 2>&1
done
diff -ru src/v1/agent-start src/v2/agent-start > $OUT/solver_visible_v1_v2.diff; echo "diff_exit=$?" >> $OUT/solver_visible_v1_v2.diff
echo "version,control,public_score,public_raw,hidden_exit,hidden_line" > $OUT/summary.csv
for v in v1 v2; do
  img=$WORK; [ $v = v2 ] && img=arc-v2-work:local
  for c in $(ls controls); do
    d=sub/$v/$c; mkdir -p $d; cp -R src/$v/agent-start/compiler/src/. $d/; cp -R controls/$c/. $d/; rm -f $d/.keep
    # public smoke (solver-visible) in the work image
    docker run --rm --network none --memory 2g --cpus 2 -v $PWD/$d:/sub:ro $img \
      bash -c "cp -R /sub/. compiler/src/ && timeout 600 bash score.sh" > $OUT/public_${v}_${c}.log 2>&1
    pub=$(grep -E '^SCORE=' $OUT/public_${v}_${c}.log | tail -1); praw=$(grep -E '^RAW_PASSED=' $OUT/public_${v}_${c}.log | tail -1)
    # hidden: original judge image + original eval_cmd
    docker run --rm --network none --memory 4g --cpus 2 -v $PWD/$d:/sub:ro -v $PWD/eval_cmd.sh:/tmp/eval_cmd.sh:ro $JUDGE \
      bash -c "cp -R /sub/. $APP/agent-start/compiler/src/ && timeout 1500 bash /tmp/eval_cmd.sh" > $OUT/hidden_${v}_${c}.log 2>&1
    ex=$?
    js=$(sed -n '/>>>>> Start Structured Result/{n;p}' $OUT/hidden_${v}_${c}.log | python3 -c 'import sys,json;d=json.loads(sys.stdin.read());print(json.dumps({k:d[k] for k in ("valid","score","pass_rate","passed","total_tests")}).replace(",",";"))' 2>/dev/null)
    echo "$v,$c,${pub#SCORE=},${praw#RAW_PASSED=},$ex,$js" >> $OUT/summary.csv
    grep -E '^\s+(strengthened|extra)/' $OUT/hidden_${v}_${c}.log > $OUT/suites_${v}_${c}.txt
  done
done
cat $OUT/summary.csv
date -u +%FT%TZ > $OUT/finished
