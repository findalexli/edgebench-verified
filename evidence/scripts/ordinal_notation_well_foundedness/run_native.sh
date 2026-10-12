#!/bin/sh
# Overlay the given submission files on the pinned judge image workspace and run the original judge.
# usage: run_native.sh <submission_dir> <out_file>
SUB=$(cd "$1" && pwd)
IMG=seededge/edgebench.judge.ordinal_notation_well_foundedness@sha256:272b80aa65542b24a19ecca09f4a3156f927c6eba15aeb484c76b921ec8c46a8
timeout 3000 docker run --rm --network none --memory 2g --cpus 2 -v "$SUB:/sub:ro" "$IMG" bash -c \
  'cp /sub/*.v /home/workspace/ordinal_notation_wf/ && cd /home/workspace/ordinal_notation_wf && python3 /opt/sebench/ordinal_notation_wf_eval.py' > "$2" 2>&1
