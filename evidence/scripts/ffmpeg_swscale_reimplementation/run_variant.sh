#!/bin/sh
# usage: run_variant.sh <variant_dir> <out_dir>
# Runs the task's exact judge eval_cmd in the pinned judge image with the variant as the submission.
set -u
V=$(cd "$1" && pwd); O=$2; mkdir -p "$O"; O=$(cd "$O" && pwd)
H=$(cd "$(dirname "$0")" && pwd)
IMG=seededge/edgebench.judge.ffmpeg_swscale_reimplementation@sha256:38b256686afe14f6cec76790a7e884eb46ac70eb918a60351942a9c35c0f879f
timeout 3000 docker run --rm --network none --memory ${MEM:-2g} --cpus ${CPUS:-2} \
  -v "$V:/sub:ro" -v "$H/eval_cmd.sh:/eval_cmd.sh:ro" -v "$O:/out" "$IMG" bash -c '
  cp -r /sub/. /home/workspace/swscale-impl/ && cd /home/workspace && bash /eval_cmd.sh > /out/stdout.txt 2> /out/stderr.txt;
  cp /logs/verifier/reward.json /out/reward.json 2>/dev/null; echo done'
