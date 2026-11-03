#!/bin/bash
# Launches the community9 pool jobs named in the file $1 (one "<task>-<suffix>" per line), at most 3 of them at once.
# A job counts as running until its result/worker.json exists (the done-marker e2b_run.py writes last).
cd /home/alex/edgebench-verified
PY=/home/alex/agentsmd-rl/.venv/bin/python; R=evidence/runs; declare -a L
while read -r x; do [ -n "$x" ] || continue
  while :; do n=0; for j in "${L[@]:-}"; do [ -n "$j" ] && [ ! -f "$R/$j/result/worker.json" ] && n=$((n+1)); done; [ $n -lt 3 ] && break; sleep 30; done
  j=community9-$x; setsid nohup $PY tools/e2b_run.py --job $R/$j --lifetime 3600 --budget 3300 > $R/$j.launch.log 2>&1 &
  L+=("$j"); echo "launched $j $(date -u +%H:%M:%S)"; sleep 20
done < "$1"
for j in "${L[@]}"; do until [ -f "$R/$j/result/worker.json" ]; do sleep 30; done; echo "finished $j $(date -u +%H:%M:%S)"; done
echo ALLDONE
