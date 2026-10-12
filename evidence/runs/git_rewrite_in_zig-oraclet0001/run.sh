#!/bin/bash
# git_rewrite_in_zig positive control: a real, version-matched git (built from the image's own git-src v2.47.0)
# stands in for the submission via the harness's HARBOR_ORACLE_MODE, through the verbatim eval_cmd.
set -u
IMG=seededge/edgebench.judge.git_rewrite_in_zig@sha256:645bc84baa85454ad3a853ce9ef5bde80a04b502eadf088667e76f203793cae7
EVAL='mkdir -p /logs/verifier /tmp/verifier && ln -sfn /home/workspace /app && ln -sfn /opt/tests /tests && ln -sfn /tmp/verifier /logs/verifier 2>/dev/null; export APP_DIR=/home/workspace VERIFIER_DIR=/logs/verifier && bash /opt/tests/test.sh >/tmp/verifier.log 2>&1 || true; cat /tmp/verifier.log >&2; bash /opt/tests/pytest_shim.sh "/logs/verifier/reward.json"'
mkdir -p /job/out /job/realgit
{ nproc; free -m; date -u; } > /job/out/host.txt
docker pull -q $IMG > /job/out/pull.txt 2>&1
docker image inspect $IMG --format '{{.Id}}' >> /job/out/pull.txt
# 1) build + install real git 2.47.0 from the scorer-shipped test-suite source tree (the extracted git-src lacks t/) into a host dir mounted at /opt/realgit
t0=$(date +%s)
docker run --rm --name ebv-zig-build --network none --cpus 8 --memory 6g -v /job/realgit:/opt/realgit $IMG bash -c '
  tar xzf /opt/tests/git-test-suite.tar.gz -C /tmp 2>/dev/null; cd /tmp/git-test-suite && make -j8 NO_TCLTK=1 NO_EXPAT=1 NO_GETTEXT=1 prefix=/opt/realgit install >/tmp/b.log 2>&1; rc=$?; tail -5 /tmp/b.log; /opt/realgit/bin/git --version; /opt/realgit/bin/git --exec-path; exit $rc' > /job/out/build.txt 2>&1
echo "build rc=$? elapsed=$(( $(date +%s)-t0 ))s" >> /job/out/build.txt
# $1 name, $2 GIT_SKIP_TESTS value, $3 timeout
run() {
  local name=$1 skip=$2 tmo=$3
  mkdir -p /job/out/$name
  local t0=$(date +%s)
  timeout $tmo docker run --rm --name ebv-zig-$name --network none --cpus 8 --memory 6g -v /job/realgit:/opt/realgit:ro -v /job/out/$name:/out $IMG bash -c "
    mkdir -p /home/workspace/zig-port/zig-out/bin && cp -a /opt/realgit/bin/. /home/workspace/zig-port/zig-out/bin/
    export HARBOR_ORACLE_MODE=1
    [ -n '$skip' ] && export GIT_SKIP_TESTS='$skip'
    nproc > /out/nproc.txt
    ( $EVAL ) > /out/eval_stdout.txt 2> /out/eval_stderr.txt
    cp /logs/verifier/reward.json /logs/verifier/evidence.json /logs/verifier/verifier.log /out/ 2>/dev/null
    tar -czf /out/test-results.tgz -C /logs/verifier test-results 2>/dev/null; true" > /job/out/$name/docker_stdout.txt 2>&1
  echo "rc=$? elapsed=$(( $(date +%s)-t0 ))s" > /job/out/$name/docker_rc.txt
}
# 2) t0001 only (all other scripts skipped by git's own GIT_SKIP_TESTS mechanism)
run t0001_only 't[1-9]* t0[1-9]* t00[1-9]* t000[02-9]*' 900
date -u >> /job/out/host.txt
