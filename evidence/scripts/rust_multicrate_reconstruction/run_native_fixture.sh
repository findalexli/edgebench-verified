#!/usr/bin/env bash
# Original + corrected scorer component vs real Cargo, inside the pinned judge image.
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
IMG=seededge/edgebench.judge.rust_multicrate_reconstruction@sha256:d1d18aed02e81e5f09938de0272a76a72fab174a784613aefa3eb51443f6e408
SRC_TGZ=${SRC_TGZ:?path to rust_multicrate_reconstruction_nested-000.tar.gz}
PATCH=$HERE/../../../proposedrepairs/rust-known-failure-credit/repair.patch
OUT=$HERE/out; rm -rf "$OUT"; mkdir -p "$OUT/src"
tar -xzf "$SRC_TGZ" -C "$OUT/src" archive-contents/cas_rust_benchmark/judge/tools/score.py
cp "$OUT/src/archive-contents/cas_rust_benchmark/judge/tools/score.py" "$OUT/score_original.py"
mkdir -p "$OUT/p/judge/tools"; cp "$OUT/score_original.py" "$OUT/p/judge/tools/score.py"
(cd "$OUT/p" && patch -s -p1 < "$PATCH"); cp "$OUT/p/judge/tools/score.py" "$OUT/score_corrected.py"
sha256sum "$OUT/score_original.py" "$OUT/score_corrected.py" | tee "$OUT/identities.txt"
cp -r "$HERE/fixture" "$OUT/fixture"
timeout 900 docker run --rm --network none --memory 2g --cpus 2 -v "$OUT:/w" -v "$HERE/run_fixture_scenarios.py:/probe/run.py:ro" \
  -e OUT_JSON=/w/results.json -w /w "$IMG" \
  bash -c 'cargo --version; rustc --version; python3 -I -B /probe/run.py /w/score_original.py /w/score_corrected.py /w/fixture; rm -rf /w/fixture/target; chown -R '"$(id -u):$(id -g)"' /w' | tee "$OUT/run.log"
# do not leave copies of the task source behind
rm -rf "$OUT/src" "$OUT/p" "$OUT"/score_*.py "$OUT/fixture"
