#!/bin/bash
# Paired v1/v2 evaluation for order_addition_permutation_optimization (E2B job; run as root in /job).
# v1 = original judge image (pinned digest); v2 = image built here from ../Dockerfile (copied to v2ctx/).
# Every judgement uses the original eval_cmd via the TaskSpec eval.sh, --network none.
set -x
J=seededge/edgebench.judge.order_addition_permutation_optimization@sha256:6d1a1506f52a5cc7c95680c6df7cd72cb95f81fa236b9794aa507490b947fbd8
CWD=/home/workspace/complex_job_scheduling
O=/job/out; mkdir -p $O/subs; nproc; free -m; df -h / | tail -1; date -u
docker pull -q $J > $O/pull.log 2>&1
docker image inspect $J --format '{{.Id}} {{.Config.User}} {{.Config.WorkingDir}}' > $O/v1_image.txt
docker build -t order_v2 /job/v2ctx > $O/v2_build.log 2>&1; echo "build_rc=$?" >> $O/v2_build.log
docker image inspect order_v2 --format '{{.Id}}' > $O/v2_image.txt
# Preflight (guards against the earlier pilot's zero-test capture): checker present, hashes, 5 tests collected.
for V in v1 v2; do
  [ $V = v1 ] && I=$J || I=order_v2
  docker run --rm --network none $I bash -c "cd $CWD && sha256sum tests/* vcpom_m1000_final_result.txt && grep -n EXPECTED_SCORE_HELPER_SHA256 tests/test_final_result.py | head -1 && python -m pytest tests/test_final_result.py --collect-only -q" > $O/preflight_$V.txt 2>&1
done
# Submissions, generated once in the v1 image with only the public black-box function.
for m in identity search badcost dup; do
  mkdir -p $O/subs/$m
  docker run --rm --network none --cpus 2 --memory 4g -v /job:/job:ro -v $O/subs/$m:/o $J bash -c \
    "cd $CWD && python /job/make_result.py $m 60 > /o/gen.txt 2>&1 && cp final_result.txt /o/final_result.txt && cp /job/make_result.py /o/solver.py"
  mv $O/subs/$m/gen.txt $O/subs/$m.gen.txt
done
for V in v1 v2; do
  [ $V = v1 ] && I=$J || I=order_v2
  for m in identity search badcost dup; do
    bash /job/judge_one.sh $I $O/subs/$m $CWD 600 $O/$V.$m 2 4g
  done
done
sha256sum $O/subs/*/* > $O/subs.sha256
date -u
