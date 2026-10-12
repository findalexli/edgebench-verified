#!/usr/bin/env bash
# On all 30 official T3 inputs: run the image's std.cpp and the naive strategy,
# then report the instrumented checker's true cost and the original verdict.
set -uo pipefail
I=seededge/edgebench.judge.equivalence_class_divide_and_conquer@sha256:f793d805d7e2adcec68355343230db3ea15b1010a98678850d2fe89e9ba767e6
HERE=$(cd "$(dirname "$0")" && pwd)
timeout 3000 docker run --rm --network none --memory 2g --cpus 2 -v "$HERE:/audit:ro" $I bash -c '
ulimit -s unlimited
P=/opt/p2_judge/prob; T=$P/P2/T3_P8204; DT=$T/data
g++ -std=c++17 -Ofast -pipe -I $P -I $DT $DT/checker.cpp -o /tmp/chk_orig
g++ -std=c++17 -Ofast -pipe -I $P -I $DT /audit/checker_true_cost.cpp -o /tmp/chk_true
g++ -std=c++17 -Ofast -pipe $T/std.cpp -o /tmp/std
g++ -std=c++17 -Ofast -pipe /audit/naive.cpp -o /tmp/naive
for k in $(ls $DT/*.in | sed "s|.*/||;s|\.in||" | sort -n); do
  f=$DT/$k; hdr=$(head -c 40 $f.in | head -1)
  for s in std naive; do
    t0=$(date +%s.%N); /tmp/$s < $f.in > /tmp/o 2>/dev/null; rs=$?; t1=$(date +%s.%N)
    /tmp/chk_orig $f.in /tmp/o $f.ans 2>/tmp/e1; r1=$?
    /tmp/chk_true $f.in /tmp/o $f.ans 2>/tmp/e2; r2=$?
    echo "case=$k nm=[$hdr] sol=$s run_rc=$rs time=$(echo "$t1 - $t0" | bc 2>/dev/null || python3 -c "print($t1-$t0)") bytes=$(stat -c %s /tmp/o) orig_rc=$r1 [$(tr "\n" " " </tmp/e1)] fixed_rc=$r2 [$(grep -o "TRUE_COST.*" /tmp/e2 | tr "\n" " ")]"
  done
done'
