#!/bin/bash
# Time the task's tester on each of the 50 grading cases (output of the baseline.py control), one at a time,
# inside the original judge image: docker run --rm --network none --memory 2g --cpus 1 -v <sol>:/home/workspace/molecules/solution.py:ro
#   -v tester_time.sh:/t.sh:ro seededge/edgebench.judge.molecular_self_assembly@sha256:8afd932de7e54bacee44bcc33ceb4dab1125ad563aa81c1141717f1fc25c6da5 bash /t.sh
cd /home/workspace/molecules
for c in cases/*; do python3 solution.py < $c > /tmp/o.txt; s=$(date +%s.%N); tools/bin/tester $c /tmp/o.txt >/dev/null 2>&1; e=$(date +%s.%N); echo "$c $(python3 -c "print(round($e-$s, 3))")"; done | sort -k2 -n
