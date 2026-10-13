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
t0=$(date +%s)
timeout 3000 docker run --rm --network none --memory 7600m -e OVERLAY=$OVERLAY -v /job/inputs:/in:ro -v /job/out:/out $IMG bash -c '
  set -e
  cd /home/workspace/cas_rust_benchmark
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
