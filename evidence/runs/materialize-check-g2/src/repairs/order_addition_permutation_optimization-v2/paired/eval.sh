#!/bin/bash
set -uxo pipefail
echo ">>>>> Start Test Output"
cd /home/workspace/complex_job_scheduling && python -m pytest tests/test_final_result.py -s -v 2>&1
EXIT_CODE=$?
echo ">>>>> End Test Output"
echo "Exit code: $EXIT_CODE"
exit 0
