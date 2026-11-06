#!/bin/bash
# EdgeBench end-to-end run inside one E2B worker (root, /job): original sforge harness,
# docker backend, OpenCode agent on Gemini via the flex proxy. Settings come from /job/params.env.
set -uo pipefail
. /job/params.env
O=/job/out; mkdir -p $O
{ nproc; free -m; df -h / | tail -1; docker version --format '{{.Server.Version}}'; python3 --version; date -u; } > $O/env.txt 2>&1
python3 -m venv /opt/sf > $O/setup.log 2>&1 && /opt/sf/bin/pip install -q docker fastapi uvicorn pydantic requests pyyaml markupsafe typing_extensions python-multipart >> $O/setup.log 2>&1 \
  || { echo setup-failed; exit 2; }
PROXY_LOG=$O/proxy.jsonl GEMINI_KEY_FILE=/run/ebv/gemini_key nohup python3 /job/common/flex_proxy.py > $O/proxy.stderr 2>&1 &
sleep 2
curl -s -m 120 "http://127.0.0.1:9090/v1/models/$MODEL_ID:generateContent" -H 'content-type: application/json' -H 'x-goog-api-key: dummy' \
  -d '{"contents":[{"parts":[{"text":"Reply OK"}]}]}' | head -c 300 > $O/proxy_selftest.txt
cd /job/ebv
SF="/opt/sf/bin/python -m sforge --log-dir $O/sforge-logs --tasks-dir /job/ebv/tasks"
$SF pull --task $TASK --registry seededge > $O/pull.log 2>&1 || { echo pull-failed; tail -20 $O/pull.log; exit 3; }
if [ "${VERSION:-v1}" = v2 ]; then
  # Fixed version: rebuild the repair package's images on this worker from the pinned originals,
  # tag them with the names sforge derives from task.json.in, then swap in the fixed task spec.
  ( cd /job/pkg && EDGEBENCH_ROOT=/job/ebv bash materialize.sh ) > $O/materialize.log 2>&1 || { echo materialize-failed; tail -20 $O/materialize.log; exit 4; }
  read JT WT < <(python3 -c "import json,sys;a=json.load(open('/job/ebv/tasks/$TASK.json'));b=json.load(open('/job/pkg/task.json.in'));print(b['judge']['image_tag'] if b['judge'].get('image_tag')!=a['judge'].get('image_tag') else '-', b['work']['image_tag'] if b['work'].get('image_tag')!=a['work'].get('image_tag') else '-')")
  if [ "$JT" != - ]; then docker build -t edgebench.judge.$TASK:$JT /job/pkg > $O/build_judge.log 2>&1 || { echo judge-build-failed; tail -20 $O/build_judge.log; exit 5; }; fi
  if [ "$WT" != - ]; then docker build -f /job/pkg/Dockerfile.work -t edgebench.work.$TASK:$WT /job/pkg > $O/build_work.log 2>&1 || { echo work-build-failed; tail -20 $O/build_work.log; exit 6; }; fi
  echo "judge_tag=$JT work_tag=$WT" > $O/v2_images.txt
  cp /job/pkg/task.json.in /job/ebv/tasks/$TASK.json
fi
docker images --digests > $O/images.txt
nohup $SF serve --port 8080 > $O/judge_server.log 2>&1 &
for i in $(seq 60); do curl -s -o /dev/null http://127.0.0.1:8080/ && break; sleep 2; done; tail -3 $O/judge_server.log > $O/judge_server_up.txt
{ cat /job/common/experiment.yaml; printf 'tasks:\n  %s: {}\n' $TASK; } > /job/experiment.yaml
export SFORGE_AGENT_API_BASE_URL=http://host.docker.internal:9090 SFORGE_AGENT_API_KEY=dummy
date -u +%s > $O/agent_start
$SF run --backend docker --task $TASK --agent opencode --model google/$MODEL_ID \
  --experiment /job/experiment.yaml --timeout $AGENT_TIMEOUT --eval-interval $EVAL_INTERVAL \
  --work-cpu-limit $WORK_CPU --work-mem-limit $WORK_MEM --judge-cpu-limit $JUDGE_CPU --judge-mem-limit $JUDGE_MEM \
  --run-id $RUN_ID > $O/run_stdout.log 2>&1
echo "run exit=$?" | tee $O/run_exit.txt
date -u +%s > $O/agent_end
curl -s "http://127.0.0.1:8080/api/v1/history" > $O/history.json 2>/dev/null
sleep 2; echo done
