#!/bin/bash
# Fail-fast isolation for rust_multicrate_reconstruction v2. Grades the submissions in SUBS with the
# task's eval_cmd, verbatim, in "v2ff": the v2 judge image (repairs/rust_multicrate_reconstruction-v2)
# with ONLY `--no-fail-fast` taken out of score.py again. Compared with the v2 arm of the
# rust_multicrate_reconstruction-v2-paired-r2-<sub> jobs (same submission bytes, see submission.sha256),
# the difference is the effect of cargo stopping at the first failing test binary.
# Same disk watcher as the paired jobs (deletes the public phase's target/ after it is final).
set -uo pipefail
SUBS="starter bad"
DIAG=0
IMG=seededge/edgebench.judge.rust_multicrate_reconstruction@sha256:d1d18aed02e81e5f09938de0272a76a72fab174a784613aefa3eb51443f6e408
O=/job/out; mkdir -p $O
{ nproc; free -m; df -h /; docker version --format '{{.Server.Version}}'; date -u; } > $O/env.txt 2>&1
( while true; do echo "$(date -u +%T) $(df -m / | tail -n 1)"; sleep 20; done ) > $O/df.log 2>&1 &
docker pull -q $IMG > $O/pull.log 2>&1 || { echo pull-failed | tee -a $O/summary.txt; exit 2; }
docker image inspect $IMG --format '{{.Id}}' >> $O/pull.log
sha256sum /job/inputs/* /job/inputs/pkg/* > $O/inputs.sha256 2>/dev/null
command -v patch >/dev/null || { apt-get update -qq && apt-get install -y -qq patch; } > $O/apt.log 2>&1
# --- v2 image from the package
cp -r /job/inputs/pkg /job/pkg && cd /job/pkg && ./materialize.sh > $O/materialize.log 2>&1 || { echo materialize-failed | tee -a $O/summary.txt; exit 3; }
docker build -q -t ebv/rust-v2 /job/pkg > $O/build-v2.log 2>&1 || { echo build-v2-failed | tee -a $O/summary.txt; exit 4; }
# --- v2ff image: v2 with --no-fail-fast removed again (only change)
mkdir -p /job/v2ff && cat > /job/v2ff/Dockerfile <<DF
FROM ebv/rust-v2
RUN set -eu; cd /home/workspace/cas_rust_benchmark; t=\$(mktemp -d); tar -xzf cas_rust_benchmark.tar.gz -C "\$t"; f="\$t/cas_rust_benchmark/judge/tools/score.py"; grep -c '"--no-fail-fast", ' "\$f"; sed -i 's/"--no-fail-fast", //' "\$f"; ! grep -q 'no-fail-fast", ' "\$f"; tar --numeric-owner -czf cas_rust_benchmark.tar.gz -C "\$t" cas_rust_benchmark; rm -rf "\$t"
DF
docker build -q -t ebv/rust-v2ff /job/v2ff > $O/build-v2ff.log 2>&1 || { echo build-v2ff-failed | tee -a $O/summary.txt; exit 5; }
for t in ebv/rust-v2 ebv/rust-v2ff; do docker run --rm --network none --entrypoint bash $t -c 'sha256sum /home/workspace/cas_rust_benchmark/cas_rust_benchmark.tar.gz; tar -xzOf /home/workspace/cas_rust_benchmark/cas_rust_benchmark.tar.gz cas_rust_benchmark/judge/tools/score.py | sha256sum; tar -tzf /home/workspace/cas_rust_benchmark/cas_rust_benchmark.tar.gz | grep -c "cc/src/target/"' | tr '\n' ' ' | sed "s|^|$t |"; echo; done > $O/images.txt
# --- the submission (agent-start as a solver would submit it: no vendor-deps/, no target/)
cd /job; mkdir -p /job/tgz /job/sub
cid=$(docker create $IMG true); docker cp $cid:/home/workspace/cas_rust_benchmark/cas_rust_benchmark.tar.gz /job/tgz/t.tar.gz; docker rm -f $cid >/dev/null
tar -xzf /job/tgz/t.tar.gz -C /job/tgz cas_rust_benchmark/workspace/agent-start cas_rust_benchmark/judge/hidden-tests/hidden-sources && rm /job/tgz/t.tar.gz
mkdir -p /job/up && tar -xzf /job/inputs/reference-overlay.tgz -C /job/up
for SUB in $SUBS; do
rm -rf /job/sub; mkdir -p /job/sub
python3 -I /job/inputs/build_sub.py $SUB /job/tgz/cas_rust_benchmark/workspace/agent-start /job/up /job/tgz/cas_rust_benchmark/judge/hidden-tests/hidden-sources /job/sub/agent-start > $O/build_sub-$SUB.log 2>&1 || { echo build-sub-failed | tee -a $O/summary.txt; exit 6; }
( cd /job/sub && find agent-start -type f | LC_ALL=C sort | xargs sha256sum | sha256sum ) > $O/submission-$SUB.sha256
for ARM in v2ff; do
  T=ebv/rust-v2ff
  mkdir -p $O/$SUB-$ARM; t0=$(date +%s)
  timeout 3000 docker run --rm --network none --memory 7600m -e CARGO_BUILD_JOBS=8 -e DIAG=$DIAG -e ARM=$ARM \
    -v /job/sub:/sub:ro -v /job/inputs:/in:ro -v $O/$SUB-$ARM:/out --entrypoint bash $T -c '
    cd /home/workspace/cas_rust_benchmark && cp -a /sub/agent-start ./agent-start
    ( until ls -d /tmp/cas-hidden-inject-* >/dev/null 2>&1; do sleep 3; done; rm -rf /tmp/cas_eval/run/agent-start/target; echo "public target removed $(date -u +%T)" ) > /out/watcher.log 2>&1 &
    cargo --version; rustc --version
    bash /in/eval_cmd.sh
    echo "EVAL_CMD_EXIT=$?"
    cp /tmp/cas_eval/run/score-results.json /out/ 2>/dev/null
    if [ "$DIAG" = 1 ] && [ "$ARM" = origcc ]; then python3 -I /in/diag.py cas-search cas-mcp cas > /out/diag.txt 2>&1; fi
    true' > $O/$SUB-$ARM/eval.log 2>&1
  echo "$SUB $ARM exit=$? wall=$(( $(date +%s) - t0 ))s $(grep -E '^(SCORE=|SCORE_STATUS=|RAW_PASSED=|EVAL_CMD_EXIT=)' $O/$SUB-$ARM/eval.log | tr '\n' ' ')" | tee -a $O/summary.txt
  grep -E '\[(public|combined)\] Testing' $O/$SUB-$ARM/eval.log > $O/$SUB-$ARM/crate_lines.txt
  grep -ciE 'no space left|signal: 9|SIGKILL' $O/$SUB-$ARM/eval.log | sed 's/^/disk_or_oom_hits=/' >> $O/$SUB-$ARM/crate_lines.txt
done
done
rm -rf /job/tgz /job/up
date -u >> $O/env.txt
echo done >> $O/summary.txt
