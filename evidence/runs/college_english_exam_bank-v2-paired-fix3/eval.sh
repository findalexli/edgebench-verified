#!/bin/bash
set -uxo pipefail
echo ">>>>> Start Test Output"
cd /home/workspace && python3 scoring/grade_with_codex.py --report . --scoring-dir scoring --task-id college_english_exam_bank --input-dir input --timeout 900 2>&1
EXIT_CODE=$?
echo ">>>>> End Test Output"
echo "Exit code: $EXIT_CODE"
exit 0
