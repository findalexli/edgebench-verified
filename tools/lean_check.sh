#!/bin/bash
# Compile one Lean file of the ebv project (evidence/formal/lean/ebv/Ebv/<Name>.lean) in a --memory 4g
# container, one compile at a time on this host (shared lock), and print the output.
# Usage: tools/lean_check.sh Ebv/<Name>.lean
set -u
ROOT=$(cd "$(dirname "$0")/.." && pwd); PROJ=$ROOT/evidence/formal/lean/ebv; ELAN=$HOME/.elan
export PATH=$ELAN/bin:$PATH
LP=$(cd $PROJ && lake env printenv LEAN_PATH); LEAN=$(cd $PROJ && lake env which lean)
OUT=$(mktemp -d); mkdir -p $OUT/olean/Ebv
exec 9>/tmp/ebv-heavy.lock; flock 9
timeout 1800 docker run --rm --network none --memory 4g --memory-swap 4g --cpus 2 \
  -v $ELAN:$ELAN:ro -v $PROJ:$PROJ:ro -v $OUT:$OUT -w $PROJ -e LEAN_PATH=$OUT/olean:$LP \
  --user $(id -u):$(id -g) python:3.11.14-slim $LEAN -o $OUT/olean/Ebv/$(basename "$1" .lean).olean "$1"
rc=$?; rm -rf $OUT; echo "lean exit=$rc"; exit $rc
