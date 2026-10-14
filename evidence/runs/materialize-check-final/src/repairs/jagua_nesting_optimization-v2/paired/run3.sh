#!/bin/bash
# v2.1 revision (2026-10-13): paired original (v1) / superseded fix (v2, orientation tolerance 1e-6 deg) /
# current fix (v2.1, 1e-3 deg) on the same inputs (E2B job; root in /job). v1 = original judge image;
# v2 and v2.1 built here from v2ctx/ and v21ctx/. Original eval_cmd via the TaskSpec eval.sh, --network none.
set -x
J=seededge/edgebench.judge.jagua_nesting_optimization@sha256:4f029bf7c86d4762ecb7f183b6e1a016fcf8b705ac0efe28aed8f5e9e5208466
CWD=/home/workspace/jagua-rs
CASES=blaz1,jakobs2,mao,marques,shapes1,shirts,swim,swim_cr,trousers,gardeyn0,gardeyn1,gardeyn2,gardeyn3,gardeyn4,gardeyn5,gardeyn6
O=/job/out; mkdir -p $O/refsol; nproc; free -m; df -h / | tail -1; date -u
docker pull -q $J > $O/pull.log 2>&1
docker image inspect $J --format '{{.Id}} {{.Config.User}} {{.Config.WorkingDir}}' > $O/v1_image.txt
docker build -t jagua_v2 /job/v2ctx > $O/v2_build.log 2>&1; echo "build_rc=$?" >> $O/v2_build.log
docker build -t jagua_v21 /job/v21ctx > $O/v2.1_build.log 2>&1; echo "build_rc=$?" >> $O/v2.1_build.log
docker image inspect jagua_v2 --format '{{.Id}}' > $O/v2_image.txt
docker image inspect jagua_v21 --format '{{.Id}}' > $O/v2.1_image.txt
for V in v1 v2 v2.1; do
  case $V in v1) I=$J;; v2) I=jagua_v2;; v2.1) I=jagua_v21;; esac
  docker run --rm --network none $I bash -c "sha256sum /home/workspace/jagua_task_scorer/*; cd /home/workspace/jagua-rs-ref/assets && sha256sum \$(echo $CASES | tr , ' ' | sed 's/\([a-z0-9_]*\)/\1.json/g')" > $O/pins_$V.txt 2>&1
  # 1) witnesses through validate_solution of this image's evaluate.py
  docker run --rm --network none -v /job:/job:ro $I python3 /job/validate_witnesses.py /home/workspace/jagua_task_scorer/evaluate.py /job/witnesses > $O/witnesses_$V.txt 2>&1
done
# 2) reference lbf outputs (as written, f32-derived angles, angles + 0.01 deg) validated by v1, v2, v2.1
docker run --rm --network none --cpus 4 --memory 4g -v /job:/job:ro -v $O/refsol:/o $J bash -c \
  "cd /home/workspace/jagua-rs-ref && RUSTC_BOOTSTRAP=1 cargo build --release --bin lbf >/dev/null 2>&1; python3 /job/ref_validity3.py $CASES; for n in \$(echo $CASES | tr , ' '); do echo -n \"\$n \"; python3 /job/max_overlap.py /job/v21ctx/files/home/workspace/jagua_task_scorer/evaluate.py assets/\$n.json /o/\$n.sol.json; done" > $O/ref_validity.txt 2>&1
# 3) full original scorer: v1 and v2.1 of the same submission concurrently (3 CPUs each), then v2 (3 CPUs)
for m in baseline seed_shift drop_last_item seed_shift_f32deg seed_shift_wrongdeg; do
  bash /job/judge_one.sh $J /job/subs/$m $CWD 1200 $O/v1.$m 3 3g &
  bash /job/judge_one.sh jagua_v21 /job/subs/$m $CWD 1200 $O/v2.1.$m 3 3g &
  wait
  bash /job/judge_one.sh jagua_v2 /job/subs/$m $CWD 1200 $O/v2.$m 3 3g
done
date -u
