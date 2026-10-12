#!/bin/bash
# Usage: run_direct.sh <dir containing original T2 data/ (interactive_lib.cpp, lib.h)> <scratch outdir>
set -euo pipefail
H=$(cd "$(dirname "$0")" && pwd); ORIG="$1"; OUT="$2"; mkdir -p "$OUT"
sha256sum "$ORIG/interactive_lib.cpp" "$ORIG/lib.h"
python3 -I "$H/patch_overlay.py" "$ORIG/interactive_lib.cpp" "$OUT/patched"
for v in orig patched; do
  D="$ORIG"; [ $v = patched ] && D="$OUT/patched"
  g++ -std=c++17 -Ofast -pipe -Dmain=lib_main -I"$D" -c "$D/interactive_lib.cpp" -o "$OUT/lib_$v.o"
  g++ -std=c++17 -Ofast -pipe -I"$D" "$H/alias_harness.cpp" "$OUT/lib_$v.o" -o "$OUT/h_$v"
  echo "=== $v library"; timeout 60 "$OUT/h_$v"
done
