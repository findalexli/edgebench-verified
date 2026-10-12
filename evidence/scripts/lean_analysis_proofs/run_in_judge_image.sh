#!/usr/bin/env bash
# Kernel-check Refute.lean against the task's installed definitions inside the pinned judge image.
# Uses the image's prebuilt Analysis oleans (judge baseline repo); no network; container removed.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
IMG=seededge/edgebench.judge.lean_analysis_proofs@sha256:41ece9c40d197540af701c6a9bd592101126708c3f3c46e8f6b0da531597513b
timeout 900 docker run --rm --network none --memory 4g --cpus 2 -v "$HERE":/ebv:ro --entrypoint bash "$IMG" -lc '
  cd /home/workspace/judge/se-bmk-intern/analysis
  lean --version
  sha256sum Analysis/Section_11_1.lean Analysis/Section_11_2.lean Analysis/Section_11_3.lean
  cp /ebv/Refute.lean ./EbvRefute.lean && sha256sum EbvRefute.lean
  lake env lean EbvRefute.lean'
# Optional baseline target count (prints ~7.7k lines):
#   docker run ... -lc 'cd /home/workspace/judge/se-bmk-intern/analysis && lake build ListDeclAxiom'
