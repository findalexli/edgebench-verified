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
t0=$(date +%s)
timeout 3050 docker run --rm --network none --memory 7600m -e CARGO_BUILD_JOBS=6 -e CRATE_TIMEOUT=1500 \
  -v /job/inputs:/in:ro -v /job/out:/out $IMG bash -c '
  set -e
  cd /home/workspace/cas_rust_benchmark
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
