#!/bin/bash
# Time the task's tester on each of the 50 grading cases (output of the baseline_good.py control), one at a time,
# inside the original judge image: docker run --rm --network none --memory 2g --cpus 1 -v <sol>:/home/workspace/grid_turing_robot/solution.py:ro
#   -v tester_time.sh:/t.sh:ro seededge/edgebench.judge.grid_turing_robot@sha256:f67864ad75a3a2af0f7904a05a30b888f66ce2ed5c1f3cac7d7482e578a296c3 bash /t.sh
cd /home/workspace/grid_turing_robot
for c in cases/*; do python3 solution.py < $c > /tmp/o.txt; s=$(date +%s.%N); tools/bin/tester $c /tmp/o.txt >/dev/null 2>&1; e=$(date +%s.%N); echo "$c $(python3 -c "print(round($e-$s, 3))")"; done | sort -k2 -n
