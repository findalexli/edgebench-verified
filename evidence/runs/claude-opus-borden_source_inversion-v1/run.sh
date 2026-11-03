#!/bin/bash
# One E2B worker, three phases on the same machine:
#  1. Run: EdgeBench's original harness (sforge, docker backend) with Claude Code 2.1.301 (common/sf_main.py: the harness's own claude-code agent, newer npm pin; Opus 5.5 needs >= 2.1.280) on the original task (v1).
#     The agent reaches the Anthropic API through claude_proxy.py, which adds the real credential.
#  2. Grade: every submission the run archived, with the original judge (pinned digest) and the fixed judge
#     (built here from the repair package), one container at a time, --network none --cpus 4 --memory 6g.
#  3. Verify: a separate Claude Code session on this worker checks the run and the paired grades and writes
#     /job/out/verify/. Before it starts, the sha256 of every result file is recorded (out/results.sha256).
# Settings come from /job/params.env.
set -uo pipefail
. /job/params.env
O=/job/out; mkdir -p $O/raw $O/logs
{ nproc; free -m; df -h / | tail -1; docker version --format '{{.Server.Version}}'; python3 --version; date -u; } > $O/env.txt 2>&1
phase() { echo "$(date -u +%s) $*" >> $O/phases.txt; }
phase start
if [ "${DOCKER_OVERLAY2:-0}" = 1 ]; then
  python3 -c "import json,os;p='/etc/docker/daemon.json';d=json.load(open(p)) if os.path.exists(p) else {};d.setdefault('features',{})['containerd-snapshotter']=False;json.dump(d,open(p,'w'))"
  (systemctl restart docker || service docker restart) > $O/logs/docker_restart.log 2>&1
  for i in $(seq 30); do docker info >/dev/null 2>&1 && break; sleep 2; done
fi
command -v patch >/dev/null || (apt-get update -qq && apt-get install -y -qq patch) > $O/logs/patch_install.log 2>&1
python3 -m venv /opt/sf > $O/logs/setup.log 2>&1 && /opt/sf/bin/pip install -q docker fastapi uvicorn pydantic requests pyyaml markupsafe typing_extensions python-multipart >> $O/logs/setup.log 2>&1 \
  || { echo setup-failed; exit 2; }
PROXY_LOG=$O/proxy.jsonl CLAUDE_TOKEN_FILE=/run/ebv/claude_token nohup python3 /job/common/claude_proxy.py > $O/logs/proxy.stderr 2>&1 &
sleep 2
curl -s -m 120 http://127.0.0.1:9090/v1/messages -H 'content-type: application/json' -H 'anthropic-version: 2023-06-01' -H 'authorization: Bearer dummy' \
  -d "{\"model\":\"$MODEL_ID\",\"max_tokens\":16,\"messages\":[{\"role\":\"user\",\"content\":\"Reply OK\"}]}" | head -c 300 > $O/proxy_selftest.txt
# Recorded only: with a subscription token the API rejects requests that do not come from Claude Code (429),
# so this bare call is expected to fail; the agent's own calls in proxy.jsonl show whether access works.

# ---- 1. run ----
cd /job/ebv
SF="/opt/sf/bin/python /job/common/sf_main.py --log-dir $O/sforge-logs --tasks-dir /job/ebv/tasks"
for k in 1 2 3 4; do
  $SF pull --task $TASK --registry seededge >> $O/logs/pull.log 2>&1 && ! grep -q 'FAILED' <(tail -6 $O/logs/pull.log) && break
  [ $k = 4 ] && { echo pull-failed; tail -20 $O/logs/pull.log; exit 3; }; sleep 30
done
if [ "${VERSION:-v1}" = v2 ]; then
  # Fixed task (repairs that change the work image or the task spec): rebuild the repair's images from the pinned
  # originals under the names sforge derives from task.json.in, then swap in the fixed task spec (as the Gemini sweep).
  ( cd /job/pkg && EDGEBENCH_ROOT=/job/ebv MATERIALIZE_KEEP_IMAGES=1 bash materialize.sh ) > $O/logs/materialize_v2task.log 2>&1 || { echo materialize-failed; exit 4; }
  : > $O/v2_images.txt
  for df in /job/pkg/Dockerfile /job/pkg/Dockerfile.work; do
    [ -f $df ] || continue
    role=$(sed -n 's/^FROM .*edgebench\.\(judge\|work\)\..*/\1/p' $df | head -1)
    [ -n "$role" ] || { echo "no judge/work FROM in $df"; exit 5; }
    tag=$(python3 -c "import json;a=json.load(open('/job/ebv/tasks/$TASK.json'))['$role'];b=json.load(open('/job/pkg/task.json.in'))['$role'];print(b['image_tag'] if b.get('image_tag')!=a.get('image_tag') else '-')")
    echo "$(basename $df) role=$role new_tag=$tag" >> $O/v2_images.txt
    [ "$tag" = - ] && continue
    ctx=/job/pkg; [ $TASK = arc_compiler_runtime ] && ctx=/job/pkg/files
    docker build -f $df -t edgebench.$role.$TASK:$tag $ctx > $O/logs/build_$role.log 2>&1 || { echo $role-build-failed; exit 5; }
  done
  cp /job/pkg/task.json.in /job/ebv/tasks/$TASK.json
  { docker container prune -f; docker builder prune -af; df -h / | tail -1; } > $O/logs/v2_cleanup.log 2>&1
fi
docker images --digests > $O/images.txt
nohup $SF serve --port 8080 > $O/logs/judge_server.log 2>&1 &
for i in $(seq 60); do curl -s -o /dev/null http://127.0.0.1:8080/ && break; sleep 2; done
{ cat /job/common/experiment.yaml; printf 'tasks:\n  %s: {}\n' $TASK; } > /job/experiment.yaml
export SFORGE_AGENT_API_BASE_URL=http://host.docker.internal:9090 SFORGE_AGENT_API_KEY=dummy
phase run
$SF run --backend docker --task $TASK --agent claude-code-2.1.301 --model $MODEL_ID --effort $EFFORT \
  --experiment /job/experiment.yaml --timeout $AGENT_TIMEOUT --eval-interval $EVAL_INTERVAL \
  --work-cpu-limit $WORK_CPU --work-mem-limit $WORK_MEM --judge-cpu-limit $JUDGE_CPU --judge-mem-limit $JUDGE_MEM \
  --run-id $RUN_ID > $O/run_stdout.log 2>&1
echo "run exit=$?" | tee $O/run_exit.txt
curl -s "http://127.0.0.1:8080/api/v1/history" > $O/history.json 2>/dev/null
find $O/sforge-logs -name .judge-admin-secret -delete

# ---- 2. grade with both judges ----
phase grade
if [ "${GRADE:-1}" = 1 ]; then
( cd /job/pkg && EDGEBENCH_ROOT=/job/ebv bash materialize.sh ) > $O/logs/materialize.log 2>&1; echo "rc=$?" >> $O/logs/materialize.log
grep -q "^rc=0" $O/logs/materialize.log || { echo materialize-failed; exit 4; }
docker build -t ebv-xg/$TASK:v2 /job/pkg > $O/logs/build.log 2>&1 || { echo v2-build-failed; exit 5; }
docker pull -q $V1 > $O/logs/pull_v1.log 2>&1
echo "$TASK v1 $(docker image inspect $V1 --format '{{.Id}}') v2 $(docker image inspect ebv-xg/$TASK:v2 --format '{{.Id}}')" > $O/xg_images.txt
for ev in $(ls $O/sforge-logs/runs/*/$TASK/submissions/*/eval.sh 2>/dev/null); do
  S=$(dirname $ev); r=$(basename $S)
  (cd $S && sha256sum submission.tar.gz eval.sh allowed_files.txt 2>/dev/null) > $O/raw/$TASK.$r.sha256
  T0=$(date +%s)
  bash /job/judge.sh $V1 $S $CWD $TO1 $O/raw/$TASK.$r.rep1.v1 4 6g
  bash /job/judge.sh ebv-xg/$TASK:v2 $S $CWD $TO2 $O/raw/$TASK.$r.rep1.v2 4 6g
  echo "$r done $(( $(date +%s) - T0 ))s" >> $O/progress.txt
done

fi
# ---- 3. verify on the same machine ----
phase verify
(cd $O && find . -type f ! -path './verify/*' -print0 | sort -z | xargs -0 sha256sum) > /job/results.sha256; cp /job/results.sha256 $O/results.sha256
mkdir -p $O/verify
bash /job/common/fix_verifier.sh > $O/verify/install.log 2>&1
claude --version > $O/verify/version.txt 2>&1
{ [ "${GRADE:-1}" = 1 ] || echo "NOTE: this repair does not change the judge, so there is no re-grade with two judges (/job/out/raw is empty). This run is the ${VERSION:-v1} task; check the run and its in-run grades (points 1, 2 against the in-run judge only, 4 and 5), and say what in the ${VERSION:-v1} task (work image, prompt, rescale; /job/pkg/README.md) the agent met."
  sed "s#@TASK@#$TASK#g; s#@V1@#$V1#g" /job/common/verify_prompt.md; } > /job/verify_prompt.md
( cd /job && CLAUDE_CODE_OAUTH_TOKEN=$(cat /run/ebv/claude_token) CLAUDE_CODE_EFFORT_LEVEL=$EFFORT timeout ${VERIFY_TIMEOUT:-2700} \
  claude -p "$(cat /job/verify_prompt.md)" --model $MODEL_ID --output-format stream-json --verbose --dangerously-skip-permissions \
  > $O/verify/transcript.jsonl 2> $O/verify/stderr.log; echo "verify exit=$?" > $O/verify/exit.txt )
grep -l -r "$(head -c 24 /run/ebv/claude_token)" $O > $O/verify/token_leak_check.txt 2>/dev/null && echo "TOKEN FOUND IN OUTPUT" >> $O/verify/token_leak_check.txt
phase done
docker image rm ebv-xg/$TASK:v2 >/dev/null 2>&1
echo done
