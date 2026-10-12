#!/bin/bash
# Control: same original evaluator, side 1 = Wesnoth's own stock RCA AI config (id renamed to my_custom_ai).
# Purpose: per-game time when side 1 actually plays (the shipped baseline cannot recruit), vs 900 s for 60 games.
set -x
J=seededge/edgebench.judge.wesnoth_tactical_ai@sha256:660e126eddcd91464431e83fdc0b432cea8f8e4e4d0a087d356e864460e154c8
nproc; date -u
docker pull -q $J
docker create --name jd --network none --memory 6g -v /job/out:/out -v /job/game1.py:/game1.py:ro -v /job/timed_eval.py:/timed_eval.py:ro $J sleep 7200
docker start jd
X="docker exec -w /home/wesnoth_agent jd"
D=/usr/share/games/wesnoth/1.18/data
$X bash -c "ls $D/ai/ais/; grep -rn 'recruitment' $D/core/macros/ai_candidate_actions.cfg | head -20; grep -rn 'aspect_recruitment_phase' $D | head; cat $D/ai/ais/ai_default_rca.cfg" > /job/out/stock_ai_files.txt 2>&1
cp /dev/null /job/out/baseline_cfg_original.txt
$X cat /home/wesnoth_agent/my_custom_ai.cfg > /job/out/baseline_cfg_original.txt
# A) stock RCA as side 1
$X bash -c "sed 's/^\([[:space:]]*\)id=ai_default_rca/\1id=my_custom_ai/' $D/ai/ais/ai_default_rca.cfg > /home/wesnoth_agent/my_custom_ai.cfg; sha256sum /home/wesnoth_agent/my_custom_ai.cfg; grep -n 'id=' /home/wesnoth_agent/my_custom_ai.cfg | head -3" > /job/out/control_cfg.txt 2>&1
$X cp /home/wesnoth_agent/my_custom_ai.cfg /out/control_my_custom_ai.cfg
$X env TAG=rca python3 /game1.py multiplayer_Weldyn_Channel multiplayer_The_Freelands multiplayer_Fallenstar_Lake > /job/out/rca_game1.jsonl 2>&1
T0=$(date +%s)
$X env TAG=rca timeout 900 python3 /timed_eval.py > /job/out/rca_full_eval.txt 2>&1
echo "exit=$? wall_s=$(( $(date +%s) - T0 ))" > /job/out/rca_full_eval_status.txt
docker rm -f jd
date -u
