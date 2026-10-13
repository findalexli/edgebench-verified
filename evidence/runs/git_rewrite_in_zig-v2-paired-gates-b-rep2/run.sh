#!/bin/bash
# Paired v1/v2 run for git_rewrite_in_zig-v2, normal (non-oracle) mode, on one E2B worker.
# v1 = the pinned original judge image; v2 = built here from pkg/ (materialize.sh regenerates
# files/test.sh from the pinned image + repair.patch and checks its sha256, then docker build).
# Every arm: fresh container, --network none --cpus 8 --memory 6g, the tree prepared inside the
# container, then the verbatim eval_cmd of tasks/git_rewrite_in_zig.json. Same prep for v1 and v2.
# Arms:
#   control          unmodified starter
#   zig_build_exe    starter after `zig build-exe src/main.zig -lc -lz` (leaves ./main + ./main.o)
#   obj_only         as zig_build_exe, ./main removed
#   elf_only         as zig_build_exe, ./main.o removed
#   exec_git         starter + a src/ test block that runs system git (std.process.Child)
#   exec_git_helper  starter + src/difftest.zig (non-test helper running system git) used only by a test block
#   bad_wrap_cgit    bad control (a): main.zig execs ./cgit, a C git v2.47.0 binary stored in the project root
# Bad control (b) (system-git wrappers) runs in git_rewrite_in_zig-v2-paired-oracle-b to balance the two workers.
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
sha256sum /job/inputs/* > $O/inputs_sha.txt
# C git v2.47.0 for bad control (a), built from the scorer's own test-suite tree (as in git_rewrite_in_zig-oraclefull)
t0=$(date +%s)
docker run --rm --name ebv-zig-cgit --network none --cpus 8 --memory 6g -v /job/realgit:/opt/realgit $V1 bash -c '
  tar xzf /opt/tests/git-test-suite.tar.gz -C /tmp 2>/dev/null; cd /tmp/git-test-suite && make -j8 NO_TCLTK=1 NO_EXPAT=1 NO_GETTEXT=1 prefix=/opt/realgit install >/tmp/b.log 2>&1; rc=$?; tail -3 /tmp/b.log; /opt/realgit/bin/git --version; exit $rc' > $O/cgit_build.txt 2>&1
echo "cgit build rc=$? elapsed=$(( $(date +%s)-t0 ))s" >> $O/cgit_build.txt
# After the scored path's deletions (test.sh:143, :231-232), is any git binary left in the judge image?
docker run --rm --network none $V2 bash -c 'rm -rf /app/git-src /home/workspace/git-src; rm -f /usr/bin/git /usr/bin/git-*; rm -rf /usr/lib/git-core /usr/libexec/git-core; hash -r; echo "command -v git: $(command -v git || echo none)"; echo "executables named git or git-*:"; find / -xdev \( -path /proc -o -path /sys -o -path /home/workspace/zig-port/zig-out \) -prune -o \( -name git -o -name "git-*" \) -type f -perm -u+x -print 2>/dev/null' > $O/git_after_nuke.txt 2>&1
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
BX='zig build-exe src/main.zig -lc -lz'
for ver in v1 v2; do
  if [ $ver = v1 ]; then img=$V1; else img=$V2; fi
  arm control $ver $img ':'
  arm zig_build_exe $ver $img "$BX"
  arm obj_only $ver $img "$BX && rm -f main"
  arm elf_only $ver $img "$BX && rm -f main.o"
  arm exec_git $ver $img 'cat /in/exec_git_snippet.zig >> src/main.zig && zig test src/main.zig > /jout/zig_test.txt 2>&1; echo zig_test_rc=$? >> /jout/zig_test.txt'
  arm exec_git_helper $ver $img 'cp /in/difftest.zig src/ && cat /in/exec_git_helper_snippet.zig >> src/main.zig && zig test src/main.zig > /jout/zig_test.txt 2>&1; echo zig_test_rc=$? >> /jout/zig_test.txt'
  arm bad_wrap_cgit $ver $img 'cp /opt/realgit/bin/git ./cgit && chmod 755 ./cgit && cp /in/wrap_cgit_main.zig src/main.zig && file ./cgit > /jout/cgit_file.txt'
done
docker image rm $V2 >/dev/null 2>&1
date -u >> $O/host.txt
echo done >> $O/summary.txt
