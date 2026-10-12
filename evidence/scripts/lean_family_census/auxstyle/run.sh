#!/usr/bin/env bash
# Usage: run.sh <image@digest>  -- runs AuxStyle.lean with the image's own Lean (core only, no Mathlib).
set -uo pipefail
exec 9>/tmp/ebv-heavy.lock && flock -w 7200 9 || exit 5
HERE="$(cd "$(dirname "$0")" && pwd)"
timeout 600 docker run --rm --network none --memory 2g --cpus 2 -v "$HERE":/a:ro --entrypoint bash "$1" -c 'cp /home/workspace/judge/se-bmk-intern/*/lean-toolchain /tmp/ 2>/dev/null; cd /tmp && lean --version && cp /a/AuxStyle.lean . && lean AuxStyle.lean 2>&1 | sort'
