#!/bin/bash
# Runs the four TLC configurations; output saved as tlc-<cfg>.out
cd "$(dirname "$0")"; J=../../../tools/tla2tools.jar
for c in alias_orig noalias_orig alias_patched noalias_patched; do
  echo "=== $c"; timeout 600 java -XX:+UseParallelGC -cp $J tlc2.TLC -workers 2 -deadlock -config $c.cfg -metadir /tmp/tlc-meta-$c DataMul.tla > tlc-$c.out 2>&1
  echo "exit=$?"; grep -E "Invariant|violated|No error|states generated|distinct states" tlc-$c.out | head -5
done
