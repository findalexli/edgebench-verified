#!/usr/bin/env bash
# Usage: run_judge.sh OUTDIR -- runs the original judge eval_cmd on each submission in subs/
set -u
IMG=seededge/edgebench.judge.wireless_electricity_layout@sha256:78c341ca6e52849dfa7644f6664cbdbf87cd144cc72ff156c2508f5d623906d9
HERE=$(cd "$(dirname "$0")" && pwd); OUT=$1; mkdir -p "$OUT"
for s in "$HERE"/subs/*/; do
  name=$(basename "$s")
  timeout 900 docker run --rm --network none --memory 2g --cpus 2 -v "$s":/sub:ro "$IMG" bash -c '
    cd /home/workspace/wirel && cp /sub/solution.cpp solution.cpp
    echo ">>>>> Start Test Output"; cd /home/workspace/wirel && bash /tmp/eval_wirel.sh 2>&1; echo ">>>>> End Test Output"' > "$OUT/$name.log" 2>&1
  tail -3 "$OUT/$name.log"
done
