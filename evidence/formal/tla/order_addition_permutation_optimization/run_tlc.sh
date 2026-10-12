#!/bin/bash
# Runs the TLC configurations; output saved as tlc-<cfg>.out
cd "$(dirname "$0")"; J=/tmp/tla2tools.jar; [ -f $J ] || J=../../../../.internal/tools/tla2tools.jar
for c in claims k1_orig_best_valid k2_fixed_eq_scorefirst k3_rate_as_score; do
  echo "=== $c"; timeout 600 java -XX:+UseParallelGC -cp $J tlc2.TLC -workers 2 -deadlock -config $c.cfg -metadir /tmp/tlc-meta-order-$c OrderSelection.tla > tlc-$c.out 2>&1
  echo "exit=$?"; grep -E "Invariant|violated|No error|states generated|distinct states" tlc-$c.out | head -5
done
