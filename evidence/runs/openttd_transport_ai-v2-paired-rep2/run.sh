#!/bin/bash
# Paired native run for openttd_transport_ai v1/v2 (EdgeBench Verified). Runs as root in /job on
# one E2B worker with Docker. Assembled by stage.sh: /job/pkg = the repair package (no image files),
# /job/root/tasks/openttd_transport_ai.json = the original task JSON.
# The judge image and eval_cmd are unchanged in v2, so each submission runs once in the judge:
#   baseline_v1  shipped my_ai/ from the v1 work image          (expected: script dies, score 0)
#   probe_min    calls GetQuarterlyCompanyValue monthly only    (expected: no crash)
#   baseline_v2  my_ai/ from the v2 work image (Dockerfile.work) (expected: no crash)
#   probe_value  positive-value control: 8 bus stops + loan cut, logs the value monthly
# For each: the exact original eval_cmd (offline), then diag_log.py (same run shape plus
# `-d script=4`, so AILog lines are captured) to compare logged values with the scorer.
set -u
J=seededge/edgebench.judge.openttd_transport_ai@sha256:27167956fd001115b0f6bb3e39e2e220ecd84e053dc3624d2fc3bc07bc9fc09c
WI=seededge/edgebench.work.openttd_transport_ai@sha256:8c1921e643eda26524123b772dd3b6c637566f39f4dddb99ccea6db3e68627e0
EVAL_CMD='cd /home/workspace/openttd_ai && OPENTTD_N_SEEDS=5 python3 /tmp/eval_openttd.py'
O=/job/out; mkdir -p $O; exec 3>>$O/progress.log
log(){ echo "$(date -u +%FT%TZ) $*" | tee -a /dev/fd/3; }
log "start nproc=$(nproc) mem=$(free -m | awk '/Mem/{print $2}')MiB"
pull(){ for i in 1 2 3 4; do docker pull -q "$1" >&3 2>&1 && return 0; log "pull retry $i $1"; sleep 15; done; return 1; }
pull $J && pull $WI || { log "pull failed"; exit 2; }
command -v patch >/dev/null || (apt-get update -qq && apt-get install -y -qq patch) >&3 2>&1 || { log "cannot install patch"; exit 5; }
# v2 work image from the package (materialize.sh pulls nothing new: WI is already present)
( cd /job/pkg && EDGEBENCH_ROOT=/job/root ./materialize.sh ) > $O/materialize.log 2>&1 || { log "materialize failed"; exit 3; }
( cd /job/pkg && DOCKER_BUILDKIT=0 docker build -q -f Dockerfile.work -t ebv/openttd-work-v2:latest . ) > $O/build_v2.log 2>&1 || { log "build failed"; exit 4; }
docker image inspect $J $WI ebv/openttd-work-v2:latest --format '{{.Id}} {{.RepoTags}}' > $O/image_ids.txt
python3 - > $O/prompt_check.txt <<'PY'
import json
v1 = json.load(open('/job/root/tasks/openttd_transport_ai.json'))['work']['agent_query']
v2 = json.load(open('/job/pkg/task.json.in'))['work']['agent_query']
print('v2 prompt == materialized files/agent_query.md:', v2 == open('/job/pkg/files/agent_query.md').read())
for name, q in (('v1', v1), ('v2', v2)):
    print(name, 'mentions GetCompanyValue(:', 'GetCompanyValue(' in q.replace('GetQuarterlyCompanyValue(', ''),
          '| mentions GetQuarterlyCompanyValue:', 'GetQuarterlyCompanyValue' in q)
PY
# submissions (copied out of the images to /job/sub, never into /job/out)
mkdir -p /job/sub/baseline_v1 /job/sub/baseline_v2
c=$(docker create $WI true); docker cp $c:/home/workspace/openttd_ai/my_ai/. /job/sub/baseline_v1/; docker rm $c >/dev/null
c=$(docker create ebv/openttd-work-v2:latest true); docker cp $c:/home/workspace/openttd_ai/my_ai/. /job/sub/baseline_v2/; docker rm $c >/dev/null
cp -r /job/variants/probe_min /job/variants/probe_value /job/sub/
( cd /job/sub && find . -type f | sort | xargs sha256sum ) > $O/submission_sha256.txt
diff -u /job/sub/baseline_v1/main.nut /job/sub/baseline_v2/main.nut > $O/baseline_v1_v2.diff
# engine-level API check: script API names compiled into the cached OpenTTD 13.4 binary; evaluator hashes
docker run --rm --network none --entrypoint bash $J -c '
sha256sum /tmp/eval_openttd.py /tmp/openttd_original_eval.py /usr/local/lib/python3.10/site-packages/openttdlab.py
A=$(find / -xdev -name "openttd-13.4-linux*" 2>/dev/null | head -1); echo "archive: $A"; mkdir -p /tmp/x && tar -xf "$A" -C /tmp/x
B=$(find /tmp/x -type f -name openttd | head -1); echo "binary: ${B#/tmp/x/}"; sha256sum "$B"
python3 - "$B" <<PY
import sys, re
b = open(sys.argv[1], "rb").read()
for name in (b"GetCompanyValue", b"GetQuarterlyCompanyValue", b"GetQuarterlyIncome", b"CURRENT_QUARTER"):
    print(name.decode(), "as NUL-terminated string:", len(re.findall(b"\x00" + name + b"\x00", b)))
PY' > $O/engine_api_check.txt 2>&1
run_variant(){  # $1 name
  local v=$1 d=$O/$1; mkdir -p $d
  docker rm -f jd >/dev/null 2>&1
  docker create --name jd --network none --memory 6g -v /job/diag_log.py:/diag_log.py:ro $J sleep 7200 >/dev/null
  docker start jd >/dev/null
  docker exec jd rm -rf /home/workspace/openttd_ai/my_ai; docker cp /job/sub/$v jd:/home/workspace/openttd_ai/my_ai
  docker exec jd bash -c 'sha256sum /home/workspace/openttd_ai/my_ai/*' > $d/my_ai_sha256.txt
  local t0=$(date +%s)
  docker exec jd bash -c "timeout 2600 bash -c '$EVAL_CMD'" > $d/eval.txt 2>&1
  echo "exit=$? wall_s=$(( $(date +%s) - t0 ))" > $d/eval_status.txt
  t0=$(date +%s)
  docker exec -w /home/workspace/openttd_ai jd timeout 900 python3 /diag_log.py /home/workspace/openttd_ai/my_ai 5 > $d/diag.txt 2>&1
  echo "exit=$? wall_s=$(( $(date +%s) - t0 ))" > $d/diag_status.txt
  docker rm -f jd >/dev/null
  log "done $v $(cat $d/eval_status.txt) $(grep -E '^TOTAL_SCORE' $d/eval.txt) | diag $(cat $d/diag_status.txt)"
}
for v in baseline_v1 probe_min baseline_v2 probe_value; do run_variant $v; done
log "finished"
