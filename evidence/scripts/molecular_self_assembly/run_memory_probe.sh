#!/bin/sh
# Usage: run_memory_probe.sh <hog_MiB> <helper_workers> [docker_mem]
# Runs the ORIGINAL /tmp/eval_molecules.py on all 50 official cases in the pinned judge image.
set -u
IMG=seededge/edgebench.judge.molecular_self_assembly@sha256:8afd932de7e54bacee44bcc33ceb4dab1125ad563aa81c1141717f1fc25c6da5
HERE=$(cd "$(dirname "$0")" && pwd)
HOG=$1; WK=$2; MEM=${3:-2g}
sed "s/__HOG_MB__/$HOG/" "$HERE/hog_solution.py" > "$HERE/.sol_$HOG.py"
NAME=ebv-mol-probe-$$
timeout 900 docker run --rm --name $NAME --network none --memory $MEM --memory-swap $MEM --cpus 2 \
  -e SEBENCH_MOLECULES_WORKERS=$WK -v "$HERE/.sol_$HOG.py:/sol.py:ro" "$IMG" sh -c '
cd /home/workspace/molecules && cp /sol.py solution.py && sha256sum /tmp/eval_molecules.py tools/bin/tester
echo "cgroup memory.max: $(cat /sys/fs/cgroup/memory.max 2>/dev/null || cat /sys/fs/cgroup/memory/memory.limit_in_bytes)"
python3 /tmp/eval_molecules.py > /tmp/eval.out; echo "helper_exit=$?"
grep -v "^CASE .* OK " /tmp/eval.out | head -20
echo "OK_cases=$(grep -c "^CASE .* OK " /tmp/eval.out)"
sort -n /tmp/rss.log | awk "NR==1{mn=\$1} {mx=\$1; n++} END{print \"rss_samples=\" n, \"min_peak_rss=\" mn, \"max_peak_rss=\" mx}"
'
echo "docker_exit=$?"
rm -f "$HERE/.sol_$HOG.py"
