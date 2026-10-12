#!/bin/bash
# Paired v1/v2 evaluation for dabic_gravity_inversion-v2 (E2B worker, root, /job).
# Every arm runs the task's ORIGINAL eval_cmd inside the judge image, --network none;
# only the image differs (v1 = pinned original, v2 = built from ../Dockerfile).
set -uo pipefail
V1=seededge/edgebench.judge.dabic_gravity_inversion@sha256:fe3dc29058385bb3f44101df77fc935d8dd7859bbe8aa0add21fc93e83c0731d
V2=ebv/dabic_gravity_inversion:v2
O=/job/out; mkdir -p $O/logs /job/sub
WS=/home/workspace/dabic_gravity_vinton
EVAL="cd $WS && PYTHONPATH=/opt/evaluator python /opt/evaluator/eval_dabic_v2.py $WS/outputs/"
{ nproc; free -m; docker version --format '{{.Server.Version}}'; date -u; } > $O/env.txt
docker pull $V1 > $O/pull.log 2>&1 || { echo pull-failed | tee $O/summary.txt; exit 2; }
docker build -t $V2 /job/pkg > $O/build.log 2>&1 || { echo build-failed | tee $O/summary.txt; exit 3; }
docker image inspect $V2 --format '{{.Id}}' > $O/v2_image_id.txt
for img in $V1 $V2; do docker run --rm --network none $img sha256sum /opt/evaluator/eval_dabic_v2.py /opt/dabic_judge_files/eval_dabic_v2.py; done > $O/eval_sha.txt
docker run --rm --network none $V1 bash -c "ls -la $WS $WS/outputs" > $O/shipped_workspace_ls.txt 2>&1
# Submissions: data / model = reviewer's two honest forms (identical except FORM);
# invalid = data form with np.linalg.det log-determinant. Same fixtures for B/D/F in all arms.
for arm in data model invalid; do mkdir -p /job/sub/$arm
  cp /job/inputs/results_fixture.json /job/sub/$arm/results.json; cp /job/inputs/report_fixture.md /job/sub/$arm/report.md; done
cp /job/inputs/dabic_directive_data.py /job/sub/data/dabic_directive.py
cp /job/inputs/dabic_directive_model.py /job/sub/model/dabic_directive.py
docker run --rm --network none -v /job/inputs:/in:ro -v /job/sub:/sub -v /job/tools:/tools:ro $V1 \
  python -I /tools/make_invalid_variant.py /in/dabic_directive_data.py /sub/invalid/dabic_directive.py
sha256sum /job/inputs/* /job/sub/*/* > $O/submissions_sha.txt
run_arm() { # $1 arm  $2 version  $3 image
  local t0=$(date +%s) mnt=""
  if [ "$1" != shipped ]; then rm -rf /job/run/$1-$2; mkdir -p /job/run/$1-$2; cp /job/sub/$1/* /job/run/$1-$2/; mnt="-v /job/run/$1-$2:$WS/outputs"; fi
  timeout 1400 docker run --rm --network none --cpus 8 --memory 6g $mnt $3 bash -c "$EVAL" > $O/logs/$1-$2.log 2>&1
  local rc=$?
  [ -f /job/run/$1-$2/eval_result.json ] && cp /job/run/$1-$2/eval_result.json $O/logs/$1-$2.eval_result.json
  local sr=$(sed -n '/>>>>> Start Structured Result/{n;p}' $O/logs/$1-$2.log | head -1)
  echo "$1 $2 exit=$rc wall=$(( $(date +%s) - t0 ))s $(echo "$sr" | grep -oE '"(valid|score|raw_total|structural_penalty|is_data_space|structural_failure)": [^,]+' | tr '\n' ' ')" | tee -a $O/summary.txt
  echo "$sr" > $O/logs/$1-$2.structured.json
}
for arm in data model invalid shipped; do run_arm $arm v1 $V1; run_arm $arm v2 $V2; done
# Derived strong-tier check with each image's own structural_penalty_v34 (C replaced only).
for v in v1 v2; do img=$V1; [ $v = v2 ] && img=$V2
  for arm in data model; do [ -f $O/logs/$arm-$v.eval_result.json ] && docker run --rm --network none -v $O/logs:/l:ro -v /job/tools:/tools:ro $img \
    python /tools/penalty_check.py /l/$arm-$v.eval_result.json "$arm-$v"; done; done > $O/penalty_check.txt 2>&1
docker image rm $V2 >/dev/null 2>&1; echo done >> $O/summary.txt
