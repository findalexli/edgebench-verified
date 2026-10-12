#!/bin/bash
# Paired v1/v2 evaluation for equivalence_class_divide_and_conquer-v2 (E2B worker, root, /job).
# Arms use the task's ORIGINAL evaluator (eval.py, same flags as eval_cmd), --network none.
set -uo pipefail
V1=seededge/edgebench.judge.equivalence_class_divide_and_conquer@sha256:f793d805d7e2adcec68355343230db3ea15b1010a98678850d2fe89e9ba767e6
V2=ebv/equivalence_class_divide_and_conquer:v2
O=/job/out; mkdir -p $O/logs /job/sub /job/crafted
P=/opt/p2_judge/prob; DT=$P/P2/T3_P8204/data
EVAL="cd /home/workspace/p2 && python3 $P/P2/eval.py --source-root /home/workspace/p2 --time-factor 1 --time-grace 0 --score-sum"
nproc > $O/env.txt; free -m >> $O/env.txt
docker pull $V1 > $O/pull.log 2>&1 || { echo pull-failed; exit 2; }
docker build -t $V2 /job/pkg > $O/build.log 2>&1 || { echo build-failed; exit 3; }
docker image inspect $V2 --format '{{.Id}}' > $O/v2_image_id.txt
for img in $V1 $V2; do docker run --rm --network none $img bash -c "sha256sum $DT/checker.cpp; ulimit -a | grep -E 'file size|stack'"; done > $O/checker_sha_and_limits.txt
docker run --rm --network none -v /job/sub:/sub -v /job/crafted:/crafted -v /job/tools:/tools:ro $V1 bash -c "
set -e; mkdir -p /sub/ref /sub/naive
for i in 1 2 3 4 5 6; do d=\$(ls -d $P/P2/T\${i}_*); cp \$d/std.cpp /sub/ref/T\$i.cpp; : > /sub/naive/T\$i.cpp; done
cp /tools/naive.cpp /sub/naive/T3.cpp
python3 -I /tools/gen_crafted.py /crafted >/dev/null
sha256sum /sub/*/T*.cpp /crafted/*" > $O/inputs_sha.txt 2>&1
mounts() { local M=""; for i in 1 2 3 4 5 6; do M="$M -v /job/sub/$1/T$i.cpp:/home/workspace/p2/T$i.cpp:ro"; done; echo "$M"; }
run() { # $1 label  $2 image  $3 docker-extra  $4 eval-extra
  local t0=$(date +%s)
  timeout 1000 docker run --rm --network none --memory 3g --cpus 3 $3 $2 bash -c "$EVAL $4" > $O/logs/$1.log 2>&1
  local rc=$?; echo "$1 exit=$rc wall=$(( $(date +%s) - t0 ))s $(grep -E '^TOTAL_SCORE' $O/logs/$1.log)" | tee -a $O/summary.txt
}
# 1. reference (all six std.cpp), full eval_cmd, v1 and v2 concurrently (3 CPUs each of 8)
run ref-v1 $V1 "$(mounts ref)" "" & run ref-v2 $V2 "$(mounts ref)" "" & wait
# 2. naive legal-but-over-budget T3 (others empty), full eval_cmd
run naive-v1 $V1 "$(mounts naive)" "-v"; run naive-v2 $V2 "$(mounts naive)" "-v"
# 3. crafted trigger through eval.py: the crafted input is mounted as extra T3 case 31; naive T3 submission
for c in A_at_limit B_over_by_n; do for v in v1 v2; do img=$V1; [ $v = v2 ] && img=$V2
  run crafted-$c-$v $img "$(mounts naive) -v /job/crafted/$c.in:$DT/31.in:ro -v /job/crafted/$c.ans:$DT/31.ans:ro" "--task T3 --case 31 -v"
done; done
# 4. checker-direct on all crafted outputs, compiled exactly as eval_common.compile_checker does
for v in v1 v2; do img=$V1; [ $v = v2 ] && img=$V2
  docker run --rm --network none --memory 2g -v /job/crafted:/c:ro $img bash -c "
  g++ -std=c++17 -Ofast -pipe -I $P -I $DT $DT/checker.cpp -o /tmp/chk
  for c in A_at_limit B_over_by_n C_over_by_2n D_over_by_n_trailer E_efficient; do /tmp/chk /c/\$c.in /c/\$c.out /c/\$c.ans 2>/tmp/e; echo \"$v \$c exit=\$? \$(tr '\n' ' ' </tmp/e)\"; done"
done | tee -a $O/checker_direct.txt
docker image rm $V2 >/dev/null 2>&1; echo done >> $O/summary.txt
