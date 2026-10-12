#!/usr/bin/env bash
# Measure original evaluate.py CPU/RSS on the real data with a fixed submission (no infer run).
# usage: measure_evaluate.sh <workspace_root_extracted> <evaluate.py> <submission.json> <out_report>
set -eu
WS=$1; EV=$2; SUB=$3; OUT=$4
STUB=$(cd "$(dirname "$0")" && pwd)/stubs
cp "$EV" "$(dirname "$OUT")/evaluate_copy.py"; cp "$WS/scoring/评测资源/student_simulator.py" "$(dirname "$OUT")/"
cd "$(dirname "$OUT")"
PYTHONPATH=$STUB timeout 900 /usr/bin/time -v python3 evaluate_copy.py --submission "$SUB" --infer_time_seconds 10 \
  --ground_truth "$WS/scoring/评测资源/test_ground_truth.json" --scenarios "$WS/scoring/评测资源/test_scenarios.json" \
  --logs "$WS/input/输入数据/answering_logs.csv" --questions "$WS/input/输入数据/question_bank.csv" \
  --kp_graph "$WS/input/输入数据/knowledge_graph.csv" --deliverables_dir "$(dirname "$OUT")" --output "$OUT" > eval.stdout 2> eval.time
grep -E "User time|System time|Elapsed|Maximum resident" eval.time; python3 -c "import json;d=json.load(open('$OUT'));print('total',d['total_score'],{k:round(d[k]['score'],2) for k in d if k.startswith('M')})"
