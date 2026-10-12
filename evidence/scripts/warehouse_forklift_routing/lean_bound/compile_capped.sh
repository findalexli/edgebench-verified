#!/bin/bash
# Compile the warehouse Lean files under the heavy-job lock, inside a --memory 4g container,
# using the host toolchain and Mathlib oleans read-only (no lake/git inside the container).
set -u
P=$(cd "$(dirname "$0")/../../../formal/lean/ebv" && pwd); OUT=${OUT:-$(mktemp -d)}; mkdir -p $OUT/olean/Ebv
export PATH=$HOME/.elan/bin:$PATH
LP="$OUT/olean:$(cd $P && lake env printenv LEAN_PATH)"; LEAN=$(cd $P && lake env which lean)
exec 9>/tmp/ebv-heavy.lock && flock -w 7200 9
for f in WarehouseBound WarehouseCheck WarehouseData; do
  EXTRA=""; [ $f = WarehouseBound ] && EXTRA="-o $OUT/olean/Ebv/WarehouseBound.olean"
  timeout 1500 docker run --rm --network none --memory 4g --memory-swap 4g --cpus 2 \
    -v $HOME/.elan:$HOME/.elan:ro -v $P:$P:ro -v $OUT:$OUT -w $P -e LEAN_PATH="$LP" \
    --user $(id -u):$(id -g) python:3.11.14-slim $LEAN $EXTRA Ebv/$f.lean > $OUT/$f.out 2>&1
  echo "$f rc=$?"; cat $OUT/$f.out
done
