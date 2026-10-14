#!/bin/bash
set -uxo pipefail
echo ">>>>> Start Test Output"
cd /home/workspace/jagua-rs && JAGUA_EVAL_CASES=16 JAGUA_EVAL_SAMPLES=900 JAGUA_CASE_TIMEOUT=20 JAGUA_BUILD_TIMEOUT=300 CANDIDATE_ROOT=/home/workspace/jagua-rs REFERENCE_ROOT=/home/workspace/jagua-rs-ref bash /home/workspace/jagua_task_scorer/score.sh 2>&1
EXIT_CODE=$?
echo ">>>>> End Test Output"
echo "Exit code: $EXIT_CODE"
exit 0
