#!/bin/bash
set -uxo pipefail
echo ">>>>> Start Test Output"
cd /home/workspace/045_graph_node_classification && CUDA_VISIBLE_DEVICES= NVIDIA_VISIBLE_DEVICES=none python judge_eval.py 2>&1
EXIT_CODE=$?
echo ">>>>> End Test Output"
echo "Exit code: $EXIT_CODE"
exit 0
