#!/usr/bin/env bash
# Runs the ORIGINAL judge command in the pinned judge image with the wrapper
# submission under several confidence modes. Output: one JSON metrics line per mode.
set -euo pipefail
I=seededge/edgebench.judge.graph_node_classification@sha256:518c105ec283ea9231ecb87886e0937c14a7bd937d8e385afaa3369800c5c3bd
HERE=$(cd "$(dirname "$0")" && pwd)
for mode in ${MODES:-orig nan zero big one neg inf}; do
  timeout 1800 docker run --rm --network none --memory 2g --cpus 2 \
    -e CONF_MODE=$mode -e SEB_PARALLEL_WORKERS=${SEB_PARALLEL_WORKERS:-4} -e CONF_CONST=${CONF_CONST:-0.5} \
    -v "$HERE/wrapper_solution.py:/home/workspace/045_graph_node_classification/solution/solution.py:ro" \
    $I bash -c 'cd /home/workspace/045_graph_node_classification && CUDA_VISIBLE_DEVICES= NVIDIA_VISIBLE_DEVICES=none python judge_eval.py' \
  | python3 -c "
import sys,json
t=sys.stdin.read(); s=t.split('>>>>> Start Structured Result')[1].split('>>>>> End Structured Result')[0]
r=json.loads(s); m=r['metrics']
if 'overall_score' not in m: print(json.dumps({'mode':'$mode','valid':r['valid'],'score':r['score'],'summary':r['summary']})); sys.exit()
print(json.dumps({'mode':'$mode','valid':r['valid'],'score':r['score'],'overall':m['overall_score'],'one_minus_ece':m['one_minus_ece'],'ece':m['ece'],'macro_f1':m['macro_f1'],'micro_f1':m['micro_f1'],'bal_acc':m['balanced_accuracy'],'time_pen':m['avg_time_penalty']}))"
done
