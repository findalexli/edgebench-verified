#!/bin/bash
set -x
J=seededge/edgebench.judge.nethack_dungeon_agent@sha256:2917aca0e831dd91e88d8c40a453b73d0080230cdf4d9824291b0b601c08f1e0
WI=seededge/edgebench.work.nethack_dungeon_agent@sha256:6adeba51c22d1bbc412a4d7926428424cdf467cd4f6f897d90b623ca1587c9cd
nproc; free -m; date -u
docker pull -q $J; docker pull -q $WI
docker image inspect $J --format '{{.Id}} {{.Config.User}} {{.Config.WorkingDir}}' > /job/out/judge_image.txt
docker create --name wk $WI true; mkdir -p /job/sub; docker cp wk:/home/nethack_agent/agent.py /job/sub/; docker rm wk
sha256sum /job/sub/agent.py > /job/out/submission_sha256.txt
docker create --name jd --network none --memory 6g -v /job/out:/out -v /job/diag.py:/diag.py:ro -v /job/evalpath_fp.py:/evalpath_fp.py:ro $J sleep 7200
docker cp /job/sub/agent.py jd:/home/nethack_agent/agent.py
docker start jd
X="docker exec -w /home/nethack_agent jd"
$X bash -c 'id; sha256sum /tmp/eval_nethack.py /home/nethack_agent/agent.py; pip show nle gymnasium 2>/dev/null | grep -E "^(Name|Version)"; nproc' > /job/out/diag_env.txt 2>&1
$X timeout 300 python3 /diag.py > /job/out/diag_seed.txt 2>&1
for i in 1 2 3; do $X timeout 120 python3 /evalpath_fp.py; done > /job/out/evalpath_fp.txt 2>&1
for i in 1 2 3; do S=$(date +%s%N); $X timeout 130 python3 /tmp/eval_nethack.py --run-seed 0 | tail -1; echo "game_wall_ms=$(( ($(date +%s%N) - S)/1000000 ))"; done > /job/out/single_game_timing.txt 2>&1
for r in 1 2; do
  T0=$(date +%s)
  $X timeout 1100 python3 /tmp/eval_nethack.py > /job/out/full_eval_run$r.txt 2>&1
  echo "exit=$? wall_s=$(( $(date +%s) - T0 ))" > /job/out/full_eval_status_run$r.txt
done
docker rm -f jd
date -u
