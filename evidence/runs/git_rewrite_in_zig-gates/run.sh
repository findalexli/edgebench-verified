#!/bin/bash
# git_rewrite_in_zig escalation E1: exercise the anti-cheat gates of test.sh/compute_reward.py in NORMAL
# (non-oracle) mode, through the verbatim eval_cmd of tasks/git_rewrite_in_zig.json, on the pinned judge image.
# Arms (each a fresh container; the judge image already holds the task's starter scaffold at /home/workspace/zig-port):
#   control       unmodified scaffold
#   zig_build_exe scaffold after `zig build-exe src/main.zig -lc -lz` run in the project root (leaves ./main ELF + ./main.o)
#   obj_only      as zig_build_exe, but ./main deleted (only ./main.o, non-executable relocatable ELF)
#   elf_only      as zig_build_exe, but ./main.o deleted (only ./main, executable ELF)
#   exec_git      scaffold + a src/ test block that runs system git via std.process.Child (differential test)
set -u
IMG=seededge/edgebench.judge.git_rewrite_in_zig@sha256:645bc84baa85454ad3a853ce9ef5bde80a04b502eadf088667e76f203793cae7
EVAL='mkdir -p /logs/verifier /tmp/verifier && ln -sfn /home/workspace /app && ln -sfn /opt/tests /tests && ln -sfn /tmp/verifier /logs/verifier 2>/dev/null; export APP_DIR=/home/workspace VERIFIER_DIR=/logs/verifier && bash /opt/tests/test.sh >/tmp/verifier.log 2>&1 || true; cat /tmp/verifier.log >&2; bash /opt/tests/pytest_shim.sh "/logs/verifier/reward.json"'
mkdir -p /job/out
{ nproc; free -m; date -u; } > /job/out/host.txt
docker pull -q $IMG > /job/out/pull.txt 2>&1
docker image inspect $IMG --format '{{.Id}}' >> /job/out/pull.txt
cat > /job/out/exec_git_snippet.zig <<'ZIG'

test "init matches system git" {
    const alloc = std.testing.allocator;
    var child = std.process.Child.init(&.{ "git", "--version" }, alloc);
    child.stdout_behavior = .Ignore;
    _ = try child.spawnAndWait();
}
ZIG
arm() {
  local name=$1 prep=$2
  mkdir -p /job/out/$name
  local t0=$(date +%s)
  timeout 1500 docker run --rm --name ebv-gate-$name --network none --cpus 8 --memory 6g -v /job/out:/jout $IMG bash -c "
    cd /home/workspace/zig-port
    $prep
    find /home/workspace/zig-port -not -path '*/.zig-cache/*' -type f -exec ls -l {} + > /jout/$name/tree_before_eval.txt 2>&1
    cd /home/workspace/zig-port
    ( $EVAL ) > /jout/$name/eval_stdout.txt 2> /jout/$name/eval_stderr.txt
    cp /logs/verifier/reward.json /logs/verifier/evidence.json /logs/verifier/verifier.log /jout/$name/ 2>/dev/null
    cp /logs/verifier/build.log /jout/$name/ 2>/dev/null; true" > /job/out/$name/docker_stdout.txt 2>&1
  echo "rc=$? elapsed=$(( $(date +%s)-t0 ))s" > /job/out/$name/docker_rc.txt
}
arm control ':'
arm zig_build_exe 'zig build-exe src/main.zig -lc -lz'
arm obj_only 'zig build-exe src/main.zig -lc -lz && rm -f main'
arm elf_only 'zig build-exe src/main.zig -lc -lz && rm -f main.o'
arm exec_git 'cat /jout/exec_git_snippet.zig >> src/main.zig && zig test src/main.zig > /jout/exec_git/zig_test.txt 2>&1; echo zig_test_rc=$? >> /jout/exec_git/zig_test.txt'
date -u >> /job/out/host.txt
