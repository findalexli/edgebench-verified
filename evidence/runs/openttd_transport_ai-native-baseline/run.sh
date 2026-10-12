#!/bin/bash
set -x
J=seededge/edgebench.judge.openttd_transport_ai@sha256:27167956fd001115b0f6bb3e39e2e220ecd84e053dc3624d2fc3bc07bc9fc09c
WI=seededge/edgebench.work.openttd_transport_ai@sha256:8c1921e643eda26524123b772dd3b6c637566f39f4dddb99ccea6db3e68627e0
nproc; free -m; date -u
docker pull -q $J; docker pull -q $WI
docker image inspect $J --format '{{.Id}} {{.Config.User}} {{.Config.WorkingDir}}' > /job/out/judge_image.txt
docker create --name wk $WI true; mkdir -p /job/sub; docker cp wk:/home/workspace/openttd_ai/my_ai /job/sub/; docker rm wk
(cd /job/sub && find . -type f -exec sha256sum {} \; ) > /job/out/submission_sha256.txt
cp -r /job/sub/my_ai /job/out/baseline_my_ai
run_eval () {  # $1 = network mode, $2 = tag
  docker rm -f jd 2>/dev/null
  docker create --name jd --network $1 --memory 6g -v /job/out:/out $J sleep 7200
  docker start jd
  docker exec jd bash -c 'rm -rf /home/workspace/openttd_ai/my_ai' ; docker cp /job/sub/my_ai jd:/home/workspace/openttd_ai/my_ai
  X="docker exec -w /home/workspace/openttd_ai jd"
  $X bash -c 'id; echo HOME=$HOME; sha256sum /tmp/eval_openttd.py /tmp/openttd_original_eval.py my_ai/*; pip show openttdlab 2>/dev/null | head -3; python3 -c "import openttdlab,os;print(openttdlab.__file__)"; python3 -c "import os;print(\"cpu_count\",os.cpu_count())"; ls -la ~ ; find / -xdev \( -iname "*openttd*13.4*" -o -iname "*opengfx*" \) 2>/dev/null | head -20' > /job/out/diag_$2.txt 2>&1
  ( while true; do echo "T $(date +%s)"; $X bash -c 'for d in $(find /tmp -maxdepth 3 -type d 2>/dev/null); do n=$(ls $d/*.sav 2>/dev/null | wc -l); [ $n -gt 0 ] && echo "$d $n"; done; for p in /proc/[0-9]*; do c=$(tr "\0" " " < $p/cmdline 2>/dev/null); case "$c" in *openttd*) echo "${p#/proc/} ${c:0:200}";; esac; done' ; sleep 30; done ) > /job/out/monitor_$2.txt 2>&1 &
  MON=$!
  T0=$(date +%s)
  $X bash -c 'cd /home/workspace/openttd_ai && OPENTTD_N_SEEDS=5 timeout 2600 python3 /tmp/eval_openttd.py' > /job/out/full_eval_$2.txt 2>&1
  echo "exit=$? wall_s=$(( $(date +%s) - T0 ))" > /job/out/full_eval_status_$2.txt
  kill $MON
  docker rm -f jd
}
run_eval none offline
if grep -qiE "ConnectError|Name or service|Temporary failure in name|NetworkUnreachable|getaddrinfo|ConnectTimeout|Network is unreachable" /job/out/full_eval_offline.txt; then
  echo "OFFLINE RUN NEEDED NETWORK -> rerunning with network as a labeled deviation" > /job/out/network_fallback.txt
  run_eval bridge networked
fi
date -u
