#!/bin/bash
# KB-06b: run the task's ORIGINAL eval_cmd, verbatim, in the digest-pinned judge image, on a
# "reference" submission = starter agent-start (from the image's own cas_rust_benchmark.tar.gz)
# with the 507 starter files that contain todo!() replaced by the upstream CAS source
# (github.com/codingagentsystem/cas @ a0a4b5adbc83a522147ce7d87e09ea982b300368, v1.0.0).
# Set OVERLAY=0 (starter-control job) to grade the unmodified starter instead.
set -uo pipefail
IMG=seededge/edgebench.judge.rust_multicrate_reconstruction@sha256:d1d18aed02e81e5f09938de0272a76a72fab174a784613aefa3eb51443f6e408
OVERLAY=0
O=/job/out; mkdir -p $O
{ nproc; free -m; df -h /; docker version --format '{{.Server.Version}}'; date -u; } > $O/env.txt 2>&1
docker pull -q $IMG > $O/pull.log 2>&1 || { echo pull-failed | tee -a $O/summary.txt; exit 2; }
docker image inspect $IMG --format '{{.Id}}' >> $O/pull.log
sha256sum /job/inputs/* > $O/inputs.sha256
# --- r2: restore the 4 files missing from vendored cc 1.2.55 (cas_rust_benchmark.tar.gz omits
# vendor-deps/cc/src/target/, so cargo's vendored-source checksum fails and every crate with a cc
# build-dependency is scored TEST_CRASH). Source: the crates.io cc-1.2.55.crate, verified against the
# package sha256 in vendor-deps/cc/.cargo-checksum.json; each file then verified by its listed sha256.
mkdir -p /job/cc && cd /job/cc
curl -sSfL -o cc.crate https://static.crates.io/crates/cc/cc-1.2.55.crate || { echo cc-download-failed | tee -a $O/summary.txt; exit 4; }
echo "47b26a0954ae34af09b50f0de26458fa95369a0d478d8236d3f93082b219bd29  cc.crate" | sha256sum -c > $O/cc_verify.txt 2>&1 || { echo cc-sha-mismatch | tee -a $O/summary.txt; exit 5; }
tar -xzf cc.crate && mkdir -p /job/ccfix/target && cp cc-1.2.55/src/target/*.rs /job/ccfix/target/
( cd /job/ccfix/target && sha256sum *.rs ) >> $O/cc_verify.txt
cd /job
t0=$(date +%s)
timeout 3100 docker run --rm --network none --memory 7600m -e CARGO_BUILD_JOBS=8 -e OVERLAY=$OVERLAY -v /job/inputs:/in:ro -v /job/ccfix:/ccfix:ro -v /job/out:/out $IMG bash -c '
  set -e
  cd /home/workspace/cas_rust_benchmark
  mkdir -p /tmp/fix && tar -xzf cas_rust_benchmark.tar.gz -C /tmp/fix && mkdir -p /tmp/fix/cas_rust_benchmark/workspace/agent-start/vendor-deps/cc/src/target && cp /ccfix/target/*.rs /tmp/fix/cas_rust_benchmark/workspace/agent-start/vendor-deps/cc/src/target/ && tar -czf cas_rust_benchmark.tar.gz -C /tmp/fix cas_rust_benchmark && rm -rf /tmp/fix && echo cc-restored
  mkdir -p /tmp/sub && tar -xzf cas_rust_benchmark.tar.gz -C /tmp/sub cas_rust_benchmark/workspace/agent-start
  mv /tmp/sub/cas_rust_benchmark/workspace/agent-start ./agent-start
  if [ "$OVERLAY" = 1 ]; then tar -xzf /in/reference-overlay.tgz -C agent-start; echo overlay-applied; fi
  grep -rl "todo!()" agent-start --include=*.rs --exclude-dir=vendor-deps | wc -l | sed "s/^/files_with_todo=/"
  sha256sum /home/workspace/cas_rust_benchmark/cas_rust_benchmark.tar.gz
  cargo --version; rustc --version
  set +e
  bash /in/eval_cmd.sh
  echo "EVAL_CMD_EXIT=$?"
  cp /tmp/cas_eval/run/score-results.json /out/ 2>/dev/null
  true' > $O/eval.log 2>&1
rc=$?
echo "exit=$rc wall=$(( $(date +%s) - t0 ))s $(grep -E '^(SCORE=|SCORE_STATUS=|RAW_PASSED=|EVAL_CMD_EXIT=)' $O/eval.log | tr '\n' ' ')" | tee -a $O/summary.txt
grep -E '\[(public|combined)\] Testing' $O/eval.log > $O/crate_lines.txt
date -u >> $O/env.txt
echo done >> $O/summary.txt
# Does the WORK image ship a complete vendored cc? (agents built in it)
W=seededge/edgebench.work.rust_multicrate_reconstruction:7f639fc9d090
if timeout 600 docker pull -q $W > $O/work_pull.log 2>&1; then
  docker image inspect $W --format '{{.Id}} {{.RepoDigests}}' >> $O/work_pull.log
  docker run --rm --network none $W bash -c 'cd /home/workspace/cas_rust_benchmark; ls -la; for d in agent-start/vendor-deps/cc/src/target $(find / -path /proc -prune -o -type d -path "*vendor-deps/cc/src/target" -print 2>/dev/null); do echo "DIR $d"; ls $d; done; find / -path /proc -prune -o -name "*.tar.gz" -path "*cas*" -print 2>/dev/null' > $O/work_image_cc.txt 2>&1
else echo work-pull-failed >> $O/summary.txt; fi
