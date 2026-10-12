#!/usr/bin/env bash
# Quick elaboration check of the honest variants (no scoring). Pinned judge image, no network.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
IMG=seededge/edgebench.judge.lean_analysis_proofs@sha256:41ece9c40d197540af701c6a9bd592101126708c3f3c46e8f6b0da531597513b
timeout 1200 docker run --rm --network none --memory 4g --cpus 2 -v "$HERE":/ebv:ro -e CHECK="${CHECK:-T S}" --entrypoint bash "$IMG" -lc '
  cd /home/workspace/judge/se-bmk-intern/analysis
  for v in ${CHECK:-T S}; do echo "== variant $v"; cp /ebv/Section_4_1.$v.lean /tmp/S41_$v.lean; lake env lean /tmp/S41_$v.lean 2>&1 | grep -v "declaration uses .sorry." | head -40; done'
