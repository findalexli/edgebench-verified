#!/usr/bin/env bash
# Usage: run_judge.sh OUTDIR   -- runs original eval_cmd for 4 submissions, plus a
# one-literal repaired test (expected helper hash -> installed hash) for each.
set -u
IMG=seededge/edgebench.judge.order_addition_permutation_optimization@sha256:6d1a1506f52a5cc7c95680c6df7cd72cb95f81fa236b9794aa507490b947fbd8
HERE=$(cd "$(dirname "$0")" && pwd); OUT=$1; mkdir -p "$OUT"
for mode in identity search badcost dup; do
  timeout 600 docker run --rm --network none --memory 2g --cpus 2 \
    -v "$HERE":/s:ro -v "$OUT":/o "$IMG" bash -c "
    cd /home/workspace/complex_job_scheduling
    python /s/make_result.py $mode 30 > /o/$mode.gen.txt 2>&1
    cp final_result.txt /o/$mode.final_result.txt
    sha256sum tests/score_vcpom_result.py > /o/installed_helper.sha256
    python -m pytest tests/test_final_result.py -s -v > /o/$mode.original.log 2>&1
    sed -i 's/3023b9a449119e862d4ca86d3ab45599e2496e182be82959a642522f915dbbac/337837af7067b3dae8d4ef068d26d8dd8ff779f9a627d95451af2ca411c99630/' tests/test_final_result.py
    python -m pytest tests/test_final_result.py -s -v > /o/$mode.repaired.log 2>&1
    chmod a+r /o/*"
done
