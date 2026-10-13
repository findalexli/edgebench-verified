#!/bin/bash
# Paired v1/v2 run for git_rewrite_in_zig-v2: the full real-git oracle suite at --cpus 8.
# Positive control as in git_rewrite_in_zig-oraclefull / -nproc-c8c4: real git v2.47.0 built from the
# scorer's own test-suite tree into zig-out/bin, scored with HARBOR_ORACLE_MODE=1 through the verbatim
# eval_cmd (oracle mode skips the checks, build, strace and git removal; the helper build, the full
# test run and the reward follow the scored path). Same inputs for v1 (pinned original image) and v2
# (built here from pkg/). One container at a time, --network none --cpus 8 --memory 6g.
# Also bad control (b), normal (non-oracle) mode, verbatim eval_cmd, same flags:
#   bad_shell_git          main.zig forwards every call to the system `git` via std.process.Child (non-test code)
#   bad_shell_git_oneline  the same, with "git" on the std.process.Child line (matches the original source check)
set -u
V1=seededge/edgebench.judge.git_rewrite_in_zig@sha256:645bc84baa85454ad3a853ce9ef5bde80a04b502eadf088667e76f203793cae7
V2=ebv/git_rewrite_in_zig-judge:v2
EVAL='mkdir -p /logs/verifier /tmp/verifier && ln -sfn /home/workspace /app && ln -sfn /opt/tests /tests && ln -sfn /tmp/verifier /logs/verifier 2>/dev/null; export APP_DIR=/home/workspace VERIFIER_DIR=/logs/verifier && bash /opt/tests/test.sh >/tmp/verifier.log 2>&1 || true; cat /tmp/verifier.log >&2; bash /opt/tests/pytest_shim.sh "/logs/verifier/reward.json"'
O=/job/out; mkdir -p $O /job/realgit
{ nproc; free -m; date -u; docker version --format '{{.Server.Version}}'; command -v patch python3 sha256sum; } > $O/host.txt 2>&1
docker pull -q $V1 > $O/pull.txt 2>&1
docker image inspect $V1 --format '{{.Id}}' >> $O/pull.txt
( cd /job/pkg && ./materialize.sh ) > $O/materialize.log 2>&1 || {
  # fallback if the worker lacks GNU patch: extract and patch inside the original image, then check sha256
  echo "materialize.sh failed; patching inside the original image" >> $O/materialize.log
  mkdir -p /job/pkg/files && docker run --rm --network none -v /job/pkg:/p $V1 bash -c 'cp -p /opt/tests/test.sh /p/files/test.sh && cd /p && patch -p1 --forward --batch < repair.patch' >> $O/materialize.log 2>&1
  want=$(python3 -c "import json;print(json.load(open('/job/pkg/source-lock.json'))['materialize']['outputs']['files/test.sh'])")
  [ "$(sha256sum /job/pkg/files/test.sh | cut -d' ' -f1)" = "$want" ] || { echo materialize-failed >> $O/summary.txt; exit 2; }
  echo "fallback OK: files/test.sh sha256 $want" >> $O/materialize.log; }

docker build -t $V2 /job/pkg > $O/build_v2.log 2>&1 || { echo build-failed >> $O/summary.txt; exit 3; }
docker image inspect $V2 --format '{{.Id}}' > $O/v2_image_id.txt
for img in $V1 $V2; do docker run --rm --network none $img bash -c 'sha256sum /opt/tests/test.sh /opt/tests/compute_reward.py /opt/tests/pytest_shim.sh'; done > $O/grader_sha.txt 2>&1
t0=$(date +%s)
docker run --rm --name ebv-zig-build --network none --cpus 8 --memory 6g -v /job/realgit:/opt/realgit $V1 bash -c '
  tar xzf /opt/tests/git-test-suite.tar.gz -C /tmp 2>/dev/null; cd /tmp/git-test-suite && make -j8 NO_TCLTK=1 NO_EXPAT=1 NO_GETTEXT=1 prefix=/opt/realgit install >/tmp/b.log 2>&1; rc=$?; tail -3 /tmp/b.log; /opt/realgit/bin/git --version; exit $rc' > $O/realgit_build.txt 2>&1
echo "build rc=$? elapsed=$(( $(date +%s)-t0 ))s" >> $O/realgit_build.txt
sha256sum /job/realgit/bin/git >> $O/realgit_build.txt
run() {  # run VERSION IMAGE
  local ver=$1 img=$2 d=$O/oracle/$1
  mkdir -p $d
  local t0=$(date +%s)
  timeout 2400 docker run --rm --name ebv-zig-oracle-$ver --network none --cpus 8 --memory 6g -v /job/realgit:/opt/realgit:ro -v $d:/out $img bash -c "
    mkdir -p /home/workspace/zig-port/zig-out/bin && cp -a /opt/realgit/bin/. /home/workspace/zig-port/zig-out/bin/
    export HARBOR_ORACLE_MODE=1
    nproc > /out/nproc.txt; cat /sys/fs/cgroup/cpu.max > /out/cpu_max.txt 2>&1
    date +%s.%N > /out/eval_start.txt
    ( $EVAL ) > /out/eval_stdout.txt 2> /out/eval_stderr.txt
    date +%s.%N > /out/eval_end.txt
    cd /logs/verifier/test-results && for f in t*.out; do echo \"\${f%.out} \$(grep -c '^ok ' \$f) \$(grep -c '^not ok ' \$f) \$(grep -c 'TIMEOUT after' \$f)\"; done > /out/per_script_ok_notok_timeout.txt
    cp /logs/verifier/reward.json /logs/verifier/evidence.json /logs/verifier/verifier.log /out/ 2>/dev/null; true" > $d/docker_stdout.txt 2>&1
  local rc=$?
  local reward=$(python3 -c "import json;d=json.load(open('$d/reward.json'));print(d.get('reward'),d.get('total_passed'),d.get('total_failed'),d.get('scripts_run'))" 2>/dev/null)
  echo "oracle $ver rc=$rc wall=$(( $(date +%s)-t0 ))s reward/passed/failed/scripts=[$reward] $(grep -E '^TOTAL_SCORE' $d/eval_stdout.txt)" | tee -a $O/summary.txt
}
run v1 $V1
run v2 $V2
arm() {  # arm NAME VERSION IMAGE PREP
  local name=$1 ver=$2 img=$3 prep=$4 d=$O/$1/$2
  mkdir -p $d
  local t0=$(date +%s)
  timeout 1500 docker run --rm --name ebv-gate-$name-$ver --network none --cpus 8 --memory 6g \
    -v /job/inputs:/in:ro -v /job/realgit:/opt/realgit:ro -v $d:/jout $img bash -c "
    cd /home/workspace/zig-port
    $prep
    find /home/workspace/zig-port -not -path '*/.zig-cache/*' \( -type f -o -type l \) -exec ls -l {} + > /jout/tree_before_eval.txt 2>&1
    cd /home/workspace/zig-port
    ( $EVAL ) > /jout/eval_stdout.txt 2> /jout/eval_stderr.txt
    find /home/workspace/zig-port -not -path '*/.zig-cache/*' \( -type f -o -type l \) -exec ls -l {} + > /jout/tree_after_eval.txt 2>&1
    cp /logs/verifier/reward.json /logs/verifier/evidence.json /logs/verifier/verifier.log /jout/ 2>/dev/null
    cp /logs/verifier/build.log /jout/ 2>/dev/null; true" > $d/docker_stdout.txt 2>&1
  local rc=$?
  local reward=$(python3 -c "import json,sys;d=json.load(open('$d/reward.json'));print(d.get('reward'),d.get('total_passed'),d.get('reason',''))" 2>/dev/null)
  echo "$name $ver rc=$rc wall=$(( $(date +%s)-t0 ))s reward/passed/reason=[$reward] $(grep -E '^TOTAL_SCORE' $d/eval_stdout.txt)" | tee -a $O/summary.txt
}
sha256sum /job/inputs/* > $O/inputs_sha.txt
for ver in v1 v2; do
  if [ $ver = v1 ]; then img=$V1; else img=$V2; fi
  arm bad_shell_git $ver $img 'cp /in/shell_git_main.zig src/main.zig'
  arm bad_shell_git_oneline $ver $img 'cp /in/shell_git_oneline_main.zig src/main.zig'
done
if cmp -s $O/oracle/v1/per_script_ok_notok_timeout.txt $O/oracle/v2/per_script_ok_notok_timeout.txt; then echo "per-script counts identical" >> $O/summary.txt; else echo "per-script counts differ" >> $O/summary.txt; diff $O/oracle/v1/per_script_ok_notok_timeout.txt $O/oracle/v2/per_script_ok_notok_timeout.txt >> $O/summary.txt; fi
docker image rm $V2 >/dev/null 2>&1
date -u >> $O/host.txt
echo done >> $O/summary.txt
