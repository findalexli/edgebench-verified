#!/bin/bash
# git_rewrite_in_zig escalation E2: per-script test times under a CPU quota while test.sh uses NPARALLEL=$(nproc).
# Positive control as in git_rewrite_in_zig-oraclefull: real git v2.47.0 built from the scorer's own test-suite tree,
# scored via HARBOR_ORACLE_MODE=1 through the verbatim eval_cmd (oracle mode changes only the gates/build/strace/nuke
# steps; helper build, test run and reward are the scored path). Per-script start/end times are recorded by a
# sidecar loop in the same container that polls the results dir once per second (it adds negligible load).
set -u
CPUS_LIST="${CPUS_LIST:-2}"
IMG=seededge/edgebench.judge.git_rewrite_in_zig@sha256:645bc84baa85454ad3a853ce9ef5bde80a04b502eadf088667e76f203793cae7
EVAL='mkdir -p /logs/verifier /tmp/verifier && ln -sfn /home/workspace /app && ln -sfn /opt/tests /tests && ln -sfn /tmp/verifier /logs/verifier 2>/dev/null; export APP_DIR=/home/workspace VERIFIER_DIR=/logs/verifier && bash /opt/tests/test.sh >/tmp/verifier.log 2>&1 || true; cat /tmp/verifier.log >&2; bash /opt/tests/pytest_shim.sh "/logs/verifier/reward.json"'
mkdir -p /job/out /job/realgit
{ nproc; free -m; date -u; } > /job/out/host.txt
docker pull -q $IMG > /job/out/pull.txt 2>&1
docker image inspect $IMG --format '{{.Id}}' >> /job/out/pull.txt
t0=$(date +%s)
docker run --rm --name ebv-zig-build --network none --cpus 8 --memory 6g -v /job/realgit:/opt/realgit $IMG bash -c '
  tar xzf /opt/tests/git-test-suite.tar.gz -C /tmp 2>/dev/null; cd /tmp/git-test-suite && make -j8 NO_TCLTK=1 NO_EXPAT=1 NO_GETTEXT=1 prefix=/opt/realgit install >/tmp/b.log 2>&1; rc=$?; tail -5 /tmp/b.log; /opt/realgit/bin/git --version; exit $rc' > /job/out/build.txt 2>&1
echo "build rc=$? elapsed=$(( $(date +%s)-t0 ))s" >> /job/out/build.txt
cat > /job/sidecar.sh <<'SC'
#!/bin/bash
# poll every second; log first-seen time of each result file (created when its script starts)
D=/logs/verifier/test-results; seen=/tmp/.sc_seen; : > $seen
while [ ! -f /out/.stop ]; do
  now=$(date +%s.%N)
  if [ -d "$D" ]; then
    ls "$D" 2>/dev/null | sort > /tmp/.sc_now
    comm -13 $seen /tmp/.sc_now | while read f; do echo "$now $f" >> /out/first_seen.txt; done
    cp /tmp/.sc_now $seen
  fi
  sleep 1
done
SC
chmod +x /job/sidecar.sh
run() {
  local cpus=$1 name=cpus$1
  mkdir -p /job/out/$name
  local t0=$(date +%s)
  timeout 2400 docker run --rm --name ebv-zig-$name --network none --cpus $cpus --memory 6g -v /job/realgit:/opt/realgit:ro -v /job/sidecar.sh:/sidecar.sh:ro -v /job/out/$name:/out $IMG bash -c "
    mkdir -p /home/workspace/zig-port/zig-out/bin && cp -a /opt/realgit/bin/. /home/workspace/zig-port/zig-out/bin/
    export HARBOR_ORACLE_MODE=1
    nproc > /out/nproc.txt; cat /sys/fs/cgroup/cpu.max > /out/cpu_max.txt 2>&1
    /sidecar.sh & SC=\$!
    date +%s.%N > /out/eval_start.txt
    ( $EVAL ) > /out/eval_stdout.txt 2> /out/eval_stderr.txt
    date +%s.%N > /out/eval_end.txt
    touch /out/.stop; wait \$SC
    cd /logs/verifier/test-results && stat -c '%n %W %Y' *.out > /out/stat_times.txt
    grep -l 'TIMEOUT after 120s' *.out > /out/timeouts.txt; true
    cp /logs/verifier/reward.json /logs/verifier/evidence.json /logs/verifier/verifier.log /out/ 2>/dev/null
    tar -czf /out/test-results.tgz -C /logs/verifier test-results 2>/dev/null; true" > /job/out/$name/docker_stdout.txt 2>&1
  echo "rc=$? elapsed=$(( $(date +%s)-t0 ))s" > /job/out/$name/docker_rc.txt
}
for c in $CPUS_LIST; do run $c; done
date -u >> /job/out/host.txt
