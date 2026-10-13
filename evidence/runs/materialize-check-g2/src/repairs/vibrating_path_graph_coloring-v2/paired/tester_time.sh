#!/bin/bash
# Time the task's tester on each of the 50 grading cases (output of the honest control, mounted as solution.py), one at a
# time, inside the original judge image at --cpus 1. Prints "<case> <control s> <tester s>", sorted by tester time.
cd /home/workspace/vibrating_path
for c in cases/*; do a=$(date +%s.%N); python3 solution.py < $c > /tmp/o.txt; s=$(date +%s.%N); tools/bin/tester $c /tmp/o.txt >/dev/null 2>&1; e=$(date +%s.%N); echo "$c $(python3 -c "print(round($s-$a, 3), round($e-$s, 3))")"; done | sort -k3 -n
