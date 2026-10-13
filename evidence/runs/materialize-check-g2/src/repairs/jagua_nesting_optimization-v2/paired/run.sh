#!/bin/bash
# Paired v1/v2 evaluation for jagua_nesting_optimization (E2B job; root in /job).
# v1 = original judge image; v2 = built here from v2ctx/Dockerfile. Original eval_cmd via the
# TaskSpec eval.sh, --network none.
set -x
J=seededge/edgebench.judge.jagua_nesting_optimization@sha256:4f029bf7c86d4762ecb7f183b6e1a016fcf8b705ac0efe28aed8f5e9e5208466
CWD=/home/workspace/jagua-rs
CASES=blaz1,jakobs2,mao,marques,shapes1,shirts,swim,swim_cr,trousers,gardeyn0,gardeyn1,gardeyn2,gardeyn3,gardeyn4,gardeyn5,gardeyn6
O=/job/out; mkdir -p $O/refsol; nproc; free -m; df -h / | tail -1; date -u
docker pull -q $J > $O/pull.log 2>&1
docker image inspect $J --format '{{.Id}} {{.Config.User}} {{.Config.WorkingDir}}' > $O/v1_image.txt
docker build -t jagua_v2 /job/v2ctx > $O/v2_build.log 2>&1; echo "build_rc=$?" >> $O/v2_build.log
docker image inspect jagua_v2 --format '{{.Id}}' > $O/v2_image.txt
for V in v1 v2; do
  [ $V = v1 ] && I=$J || I=jagua_v2
  docker run --rm --network none $I bash -c "sha256sum /home/workspace/jagua_task_scorer/*; cd /home/workspace/jagua-rs-ref/assets && sha256sum \$(echo $CASES | tr , ' ' | sed 's/\([a-z0-9_]*\)/\1.json/g')" > $O/pins_$V.txt 2>&1
  # 1) witnesses through validate_solution of this image's evaluate.py
  docker run --rm --network none -v /job:/job:ro $I python3 /job/validate_witnesses.py /home/workspace/jagua_task_scorer/evaluate.py /job/witnesses > $O/witnesses_$V.txt 2>&1
done
# 2) reference lbf outputs on all 16 scored instances, validated by v1 and v2 (+ largest relative overlap under v2)
docker run --rm --network none --cpus 4 --memory 4g -v /job:/job:ro -v $O/refsol:/o $J bash -c \
  "cd /home/workspace/jagua-rs-ref && RUSTC_BOOTSTRAP=1 cargo build --release --bin lbf >/dev/null 2>&1; python3 /job/ref_validity.py $CASES; for n in \$(echo $CASES | tr , ' '); do echo -n \"\$n \"; python3 /job/max_overlap.py /job/v2ctx/files/home/workspace/jagua_task_scorer/evaluate.py assets/\$n.json /o/\$n.sol.json; done" > $O/ref_validity.txt 2>&1
# 3) full original scorer: v1 and v2 of the same submission run concurrently (3 CPUs each)
for m in baseline seed_shift drop_last_item; do
  bash /job/judge_one.sh $J /job/subs/$m $CWD 1200 $O/v1.$m 3 3g &
  bash /job/judge_one.sh jagua_v2 /job/subs/$m $CWD 1200 $O/v2.$m 3 3g &
  wait
done
date -u
