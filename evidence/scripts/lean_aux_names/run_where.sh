#!/usr/bin/env bash
# Map each baseline aux target to its module/parent kind inside the pinned judge image.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
IMG=seededge/edgebench.judge.lean_analysis_proofs@sha256:41ece9c40d197540af701c6a9bd592101126708c3f3c46e8f6b0da531597513b
timeout 1200 docker run --rm --network none --memory 4g --cpus 2 -v "$HERE":/ebv:ro --entrypoint bash "$IMG" -lc '
  cd /home/workspace/judge/se-bmk-intern/analysis && cp /ebv/WhereAux.lean ./EbvWhereAux.lean && lake env lean EbvWhereAux.lean'
