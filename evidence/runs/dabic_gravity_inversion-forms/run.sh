#!/bin/bash
# dabic_gravity_inversion: same D-ABIC math in data-space vs model-space form through the original evaluator.
set -u
IMG=seededge/edgebench.judge.dabic_gravity_inversion@sha256:fe3dc29058385bb3f44101df77fc935d8dd7859bbe8aa0add21fc93e83c0731d
mkdir -p /job/out
{ nproc; free -m; date -u; } > /job/out/host.txt
docker pull -q $IMG > /job/out/pull.txt 2>&1
docker image inspect $IMG --format '{{.Id}}' >> /job/out/pull.txt
sha256sum /job/inputs/* > /job/out/inputs.sha256
for form in data model; do
  mkdir -p /job/out/$form/outputs
  cp /job/inputs/dabic_directive_$form.py /job/out/$form/outputs/dabic_directive.py
  cp /job/inputs/results_fixture.json /job/out/$form/outputs/results.json
  cp /job/inputs/report_fixture.md /job/out/$form/outputs/report.md
  t0=$(date +%s)
  timeout 1400 docker run --rm --name ebv-dabic-$form --network none --cpus 8 --memory 6g \
    -v /job/out/$form/outputs:/home/workspace/dabic_gravity_vinton/outputs $IMG \
    bash -c 'cd /home/workspace/dabic_gravity_vinton && PYTHONPATH=/opt/evaluator python /opt/evaluator/eval_dabic_v2.py /home/workspace/dabic_gravity_vinton/outputs/' \
    > /job/out/$form/stdout.txt 2> /job/out/$form/stderr.txt
  echo "rc=$? elapsed=$(( $(date +%s)-t0 ))s" > /job/out/$form/docker_rc.txt
done
date -u >> /job/out/host.txt
