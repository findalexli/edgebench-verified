#!/bin/bash
set -x
J=seededge/edgebench.judge.wesnoth_tactical_ai@sha256:660e126eddcd91464431e83fdc0b432cea8f8e4e4d0a087d356e864460e154c8
WI=seededge/edgebench.work.wesnoth_tactical_ai@sha256:4d9b1e6515b2ac2f00c22c3a2537127fd8b0c009cf5f93e747059b1555fe6a67
nproc; free -m; date -u
docker pull -q $J; docker pull -q $WI
docker image inspect $J --format '{{.Id}} {{.Config.User}} {{.Config.WorkingDir}}' > /job/out/judge_image.txt
# baseline submission = work image's /home/wesnoth_agent (submit_paths ".", excluding .git)
docker create --name wk $WI true; mkdir -p /job/sub; docker cp wk:/home/wesnoth_agent /job/sub/; docker rm wk
rm -rf /job/sub/wesnoth_agent/.git
(cd /job/sub && find . -type f -exec sha256sum {} \; ) > /job/out/submission_sha256.txt
docker create --name jd --network none --memory 6g -v /job/out:/out -v /job/game1.py:/game1.py:ro $J sleep 7200
docker cp /job/sub/wesnoth_agent/. jd:/home/wesnoth_agent/
docker start jd
X="docker exec -w /home/wesnoth_agent jd"
$X bash -c 'id; echo HOME=$HOME; sha256sum /tmp/eval_wesnoth.py /home/wesnoth_agent/my_custom_ai.cfg; ls -la /home/wesnoth_agent /home/wesnoth_agent/.config 2>&1 | head -40; /usr/games/wesnoth-1.18 --version; /usr/games/wesnoth-1.18 --userdata-path; /usr/games/wesnoth-1.18 --userconfig-path; nproc' > /job/out/diag.txt 2>&1
# 1) one original run_game per map (seed 0), default HOME
$X python3 /game1.py multiplayer_Weldyn_Channel multiplayer_The_Freelands multiplayer_Fallenstar_Lake > /job/out/game1.jsonl 2>&1
# 2) full default evaluation under eval_timeout 900 s, exact eval_cmd; monitor wesnoth processes
( while true; do echo "T $(date +%s)"; $X bash -c 'for p in /proc/[0-9]*; do c=$(tr "\0" " " < $p/cmdline 2>/dev/null); case "$c" in /usr/games/wesnoth-1.18*) echo "${p#/proc/} $c";; esac; done' ; sleep 2; done ) > /job/out/ps_monitor.txt 2>&1 &
MON=$!
T0=$(date +%s)
$X timeout 900 python3 /tmp/eval_wesnoth.py > /job/out/full_eval.txt 2>&1
echo "exit=$? wall_s=$(( $(date +%s) - T0 ))" > /job/out/full_eval_status.txt
kill $MON
docker rm -f jd
date -u
