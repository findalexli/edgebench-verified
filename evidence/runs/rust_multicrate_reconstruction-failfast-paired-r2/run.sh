#!/bin/bash
# KB-06b paired v1/v2 (fail-fast vs --no-fail-fast) on a reference submission, original judge image.
# Reference = starter agent-start (from the image's cas_rust_benchmark.tar.gz) with the 507 files that
# contain todo!() replaced by upstream CAS (github.com/codingagentsystem/cas @ a0a4b5ad..., v1.0.0).
# Workspace set up with the first half of the task's eval_cmd (extract, copy, ghostty stub); then
# inputs/paired.py drives the original score.py functions. CARGO_BUILD_JOBS=6 only to bound memory.
set -uo pipefail
IMG=seededge/edgebench.judge.rust_multicrate_reconstruction@sha256:d1d18aed02e81e5f09938de0272a76a72fab174a784613aefa3eb51443f6e408
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
timeout 3150 docker run --rm --network none --memory 7600m -e CARGO_BUILD_JOBS=6 -e CRATE_TIMEOUT=1200 \
  -v /job/inputs:/in:ro -v /job/ccfix:/ccfix:ro -v /job/out:/out $IMG bash -c '
  set -e
  cd /home/workspace/cas_rust_benchmark
  mkdir -p /tmp/fix && tar -xzf cas_rust_benchmark.tar.gz -C /tmp/fix && mkdir -p /tmp/fix/cas_rust_benchmark/workspace/agent-start/vendor-deps/cc/src/target && cp /ccfix/target/*.rs /tmp/fix/cas_rust_benchmark/workspace/agent-start/vendor-deps/cc/src/target/ && tar -czf cas_rust_benchmark.tar.gz -C /tmp/fix cas_rust_benchmark && rm -rf /tmp/fix && echo cc-restored
  mkdir -p /tmp/sub && tar -xzf cas_rust_benchmark.tar.gz -C /tmp/sub cas_rust_benchmark/workspace/agent-start
  mv /tmp/sub/cas_rust_benchmark/workspace/agent-start ./agent-start
  tar -xzf /in/reference-overlay.tgz -C agent-start
  grep -rl "todo!()" agent-start --include=*.rs --exclude-dir=vendor-deps | wc -l | sed "s/^/files_with_todo=/"
  # first part of eval_cmd (verbatim up to, not including, score.sh)
  rm -rf /tmp/cas_eval /tmp/cas_submitted_agent_start && mkdir -p /tmp/cas_eval
  cp -a agent-start /tmp/cas_submitted_agent_start; rm -rf /tmp/cas_submitted_agent_start/target /tmp/cas_submitted_agent_start/vendor-deps /tmp/cas_submitted_agent_start/.git
  tar -xzf cas_rust_benchmark.tar.gz -C /tmp/cas_eval && mkdir -p /tmp/cas_eval/run
  cp -a /tmp/cas_eval/cas_rust_benchmark/workspace/. /tmp/cas_eval/run/ && cp -a /tmp/cas_eval/cas_rust_benchmark/judge/. /tmp/cas_eval/run/
  cp -a /tmp/cas_submitted_agent_start/. /tmp/cas_eval/run/agent-start/
  cd /tmp/cas_eval/run && cc -c agent-start/.ghostty-stub/ghostty_vt_stub.c -o agent-start/.ghostty-stub/ghostty_vt_stub.o && ar rcs agent-start/.ghostty-stub/libghostty_vt.a agent-start/.ghostty-stub/ghostty_vt_stub.o
  sha256sum tools/score.py
  python3 /in/paired.py cas-cli,cas-search,cas-factory,cas-tui-test,cas-mux,cas-pty,cas-recording,cas-types,cas-code,cas-factory-protocol,cas-diffs,cas-store,cas-core,cas-mcp
  ' > $O/paired.log 2>&1
rc=$?
echo "exit=$rc wall=$(( $(date +%s) - t0 ))s $(grep -E ' SCORE ' $O/paired.log | tr '\n' ' ')" | tee -a $O/summary.txt
date -u >> $O/env.txt
echo done >> $O/summary.txt
