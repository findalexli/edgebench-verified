#!/bin/bash
# k12_math_recommendation: first positive control (shipped reference infer) under a sound envelope,
# plus a reproduction of the audit's earlier RLIMIT_AS=512MiB / 1 GiB envelope.
set -u
IMG=seededge/edgebench.judge.k12_math_recommendation@sha256:6489d4ea0e486d4c2421261c452a3abf099ba4099b587572de149c2fd7be4f72
mkdir -p /job/out
{ nproc; free -m; date -u; } > /job/out/host.txt
docker pull -q $IMG > /job/out/pull.txt 2>&1
docker image inspect $IMG --format '{{.Id}}' >> /job/out/pull.txt
# $1 name, $2 reference stage dir, $3 docker memory, $4 prefix wrapper, $5 cpus, $6 wall timeout
run() {
  local name=$1 stage=$2 mem=$3 wrap=$4 cpus=$5 tmo=$6
  mkdir -p /job/out/$name
  local t0=$(date +%s)
  timeout 1500 docker run --rm --name ebv-k12-$name --network none --cpus $cpus --memory $mem -v /job/out/$name:/out $IMG bash -c "
    set -u
    R=/home/workspace/scoring/reference_implementation/$stage
    cp \$R/train.py \$R/infer.py \$R/requirements.txt \$R/README.md /home/workspace/
    cp -r \$R/models /home/workspace/models
    cd /home/workspace && sha256sum infer.py models/* > /out/submission.sha256
    ( while true; do cat /sys/fs/cgroup/memory.current >> /out/mem_samples.txt 2>/dev/null; sleep 1; done ) & SAMP=\$!
    $wrap timeout $tmo python3 scoring/score.py > /out/score_stdout.txt 2> /out/score_stderr.txt
    echo score_rc=\$? > /out/score_rc.txt; kill \$SAMP
    cat /sys/fs/cgroup/memory.peak > /out/cgroup_memory_peak.txt 2>/dev/null
    cat /sys/fs/cgroup/memory.events > /out/cgroup_memory_events.txt 2>/dev/null
    cp /home/workspace/report.json /out/ 2>/dev/null; true" > /job/out/$name/docker_stdout.txt 2>&1
  echo "rc=$? elapsed=$(( $(date +%s)-t0 ))s" > /job/out/$name/docker_rc.txt
}
run stage2_6g stage2_advanced 6g "" 4 900
run stage1_6g stage1_baseline 6g "" 4 900
# earlier audit envelope: 1 GiB container, RLIMIT_AS 512 MiB, RLIMIT_CPU 120 s
run stage2_audit_envelope stage2_advanced 1g "prlimit --as=536870912 --cpu=120:120" 1 178
date -u >> /job/out/host.txt
