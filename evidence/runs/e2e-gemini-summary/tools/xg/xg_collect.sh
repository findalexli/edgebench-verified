#!/bin/bash
# xg_collect.sh: loop. Grade every finished cross-grade job (exit=0) into derived.json; shard rounds it skipped
# for lack of time into follow-up jobs (-xN) sized by its slowest round, and launch them.
X=/home/alex/edgebench-verified/evidence/runs/e2e-gemini-summary/tools/xg
R=/home/alex/edgebench-verified; cd $R/evidence/runs
while [ ! -e $X/STOP ]; do
  for l in xg-e2e-gemini-s2h-*.launch.log; do
    j=${l%.launch.log}; [ -f $j/result/out/derived.json ] && continue; [ -e $j/.collect-failed ] && continue
    grep -q '"status"' $l || continue
    if ! grep -q '"status": "exit=0"' $j/result/worker.json 2>/dev/null; then echo "$j FAILED $(grep -o '"status": "[^"]*"' $l)"; touch $j/.collect-failed; continue; fi
    /home/alex/agentsmd-rl/.venv/bin/python $R/evidence/runs/qwen35-regrade-summary/grade.py $R $j/result/out/raw $j/result/out/derived.json > /dev/null 2>&1 || { echo "$j grade failed"; touch $j/.collect-failed; continue; }
    rm -rf $j/pkg $j/ebv $j/result/out.tar.gz
    sk=$(grep skipped-deadline $j/result/out/progress.txt | cut -d' ' -f1)
    echo "$j graded $(grep -c '"version"' $j/result/out/derived.json); skipped $(echo $sk | wc -w)"
    if [ -n "$sk" ]; then
      maxr=$(grep ' done ' $j/result/out/progress.txt | awk '{gsub("s","",$3); if ($3+0>m) m=$3+0} END{print m+0}')
      per=$(( 3000 * 10 / ((maxr>0?maxr:600) * 13) - 1 )); [ $per -lt 1 ] && per=1
      e2e=$(echo $j | sed -E 's/^xg-//; s/-x[0-9]+$//')
      n=$(ls -d xg-$e2e-x* 2>/dev/null | grep -v launch | wc -l)
      set -- $sk
      while [ $# -gt 0 ]; do
        n=$((n+1)); rs=""; for k in $(seq $per); do [ $# -gt 0 ] || break; rs="$rs${rs:+,}$1"; shift; done
        SHARD=-x$n ROUNDS=$rs python3 $X/gen_xg.py $e2e > /dev/null
        bash /home/alex/edgebench-verified/evidence/runs/e2e-gemini-summary/tools/wait_slot.sh 20; setsid nohup /home/alex/agentsmd-rl/.venv/bin/python $R/tools/e2b_run.py --job $R/evidence/runs/xg-$e2e-x$n --lifetime 3500 --budget 3150 > xg-$e2e-x$n.launch.log 2>&1 &
        echo "  launched xg-$e2e-x$n ($rs)"; sleep 20
      done
    fi
  done
  sleep 60
done
