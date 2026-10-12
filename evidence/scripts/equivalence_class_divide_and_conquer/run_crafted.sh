#!/usr/bin/env bash
# Compile the image's own T3 checker exactly as eval_common.compile_checker does
# (g++ -std=c++17 -Ofast -pipe -I prob -I data) and run it on crafted cases.
set -uo pipefail
I=seededge/edgebench.judge.equivalence_class_divide_and_conquer@sha256:f793d805d7e2adcec68355343230db3ea15b1010a98678850d2fe89e9ba767e6
HERE=$(cd "$(dirname "$0")" && pwd)
timeout 900 docker run --rm --network none --memory 2g --cpus 2 \
  -v "$HERE:/audit:ro" $I bash -c '
set -u
P=/opt/p2_judge/prob; T=$P/P2/T3_P8204/data
sha256sum $T/checker.cpp $P/testlib.h
g++ -std=c++17 -Ofast -pipe -I $P -I $T $T/checker.cpp -o /tmp/chk_orig
g++ -std=c++17 -Ofast -pipe -I $P -I $T /audit/checker_true_cost.cpp -o /tmp/chk_true
for c in A_at_limit B_over_by_n C_over_by_2n D_over_by_n_trailer E_efficient; do
  f=/audit/crafted/$c
  /tmp/chk_orig $f.in $f.out $f.ans 2>/tmp/o.err; ro=$?
  /tmp/chk_true $f.in $f.out $f.ans 2>/tmp/t.err; rt=$?
  echo "$c | ORIGINAL exit=$ro: $(tr "\n" " " </tmp/o.err) | INSTRUMENTED exit=$rt: $(tr "\n" " " </tmp/t.err)"
done'
