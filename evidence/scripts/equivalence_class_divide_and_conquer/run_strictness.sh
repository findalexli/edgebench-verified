#!/usr/bin/env bash
# Side check: does the original checker reject statement-legal outputs (set-equal but differently written neighbourhoods)?
I=seededge/edgebench.judge.equivalence_class_divide_and_conquer@sha256:f793d805d7e2adcec68355343230db3ea15b1010a98678850d2fe89e9ba767e6
HERE=$(cd "$(dirname "$0")" && pwd)
timeout 300 docker run --rm --network none --memory 1g --cpus 1 -v "$HERE/strictness:/s:ro" $I bash -c '
P=/opt/p2_judge/prob; T=$P/P2/T3_P8204/data
g++ -std=c++17 -Ofast -pipe -I $P -I $T $T/checker.cpp -o /tmp/c
for o in s0 s1 s2; do /tmp/c /s/s.in /s/$o.out /s/s.ans; echo "$o exit=$?"; done' 2>&1
