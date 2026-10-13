#!/bin/bash
# Paired v1/v2 evaluation for triangulation_coloring_optimization-v2 (E2B job; runs in /job).
# Job dir layout: run.sh, pkg/{Dockerfile,Dockerfile.work,files/}, solutions/*.py, n4_nonconvex.{txt,out}
set -u
O=/job/out; mkdir -p $O
J1=seededge/edgebench.judge.triangulation_coloring_optimization@sha256:beeea76373084ef4e1fe5324172cf4d5fbc166943daf4cd8b60306cd89dcf671
W1=seededge/edgebench.work.triangulation_coloring_optimization@sha256:618da32c3f4d3b8a79ba840ab7c5d3dc75b42e755ca61c575b784d3976c7cd1f
EVAL='cd /home/workspace/triangulation_coloring && python3 /tmp/eval_triangulation_coloring.py'
WD=/home/workspace/triangulation_coloring
docker pull -q $J1 > $O/pull.log 2>&1; docker pull -q $W1 >> $O/pull.log 2>&1
(cd /job/pkg && docker build -q -f Dockerfile -t ebv/tricol-judge:v2 . && docker build -q -f Dockerfile.work -t ebv/tricol-work:v2 .) > $O/build.log 2>&1
docker image inspect --format '{{.Id}} {{.RepoTags}}' ebv/tricol-judge:v2 ebv/tricol-work:v2 >> $O/build.log 2>&1
run() { # image name cmd
  timeout 1500 docker run --rm --network none --memory 4g --cpus 8 -v /job/solutions:/sub:ro -v /job:/jobro:ro "$1" bash -c "$3" > $O/$2.log 2>&1; echo "exit=$?" >> $O/$2.log; }
# 0) shipped-file integrity inside each image
for im in $J1 ebv/tricol-judge:v2; do docker run --rm --network none $im bash -c "cd $WD && sha256sum tools/src/*.py tools/bin/tester cases/* /tmp/eval_triangulation_coloring.py"; done > $O/hashes_judge.txt 2>&1
for im in $W1 ebv/tricol-work:v2; do docker run --rm --network none $im bash -c "cd $WD && sha256sum tools/src/*.py tools/bin/tester sample_data/*"; done > $O/hashes_work.txt 2>&1
# 1) full original eval_cmd, v1 vs v2 judge
for sol in donothing greedy nonconvex_flip wrong_count; do
  run $J1 judge_v1_$sol "cp /sub/$sol.py $WD/solution.py && $EVAL"
  run ebv/tricol-judge:v2 judge_v2_$sol "cp /sub/$sol.py $WD/solution.py && $EVAL"
done
# 2) solver-visible local loop (work image eval_sample_data.sh), v1 vs v2
for sol in donothing greedy nonconvex_flip; do
  run $W1 work_v1_$sol "cp /sub/$sol.py $WD/solution.py && cd $WD && ./eval_sample_data.sh; for f in sample_data/0*.txt; do python3 solution.py < \$f > /tmp/o; ./tools/bin/tester \$f /tmp/o; done"
  run ebv/tricol-work:v2 work_v2_$sol "cp /sub/$sol.py $WD/solution.py && cd $WD && ./eval_sample_data.sh; for f in sample_data/0*.txt; do python3 solution.py < \$f > /tmp/o; ./tools/bin/tester \$f /tmp/o; done"
done
# 3) rule isolation on identical inputs: N=4 reflex quad + v2 cases scored by the v1 vs v2 tester
for tag in v1:$J1 v2:ebv/tricol-judge:v2; do
  t=${tag%%:*}; im=${tag#*:}
  run $im rule_$t "cd $WD && ./tools/bin/tester /jobro/n4_nonconvex.txt /jobro/n4_nonconvex.out; for i in 0 1 2 3 4 5 6 7 8 9; do python3 /sub/nonconvex_flip.py < /jobro/pkg/files/cases/000\$i.txt > /tmp/o; echo case000\$i \$(sed -n 3p /tmp/o); ./tools/bin/tester /jobro/pkg/files/cases/000\$i.txt /tmp/o; done"
done
docker image rm ebv/tricol-judge:v2 ebv/tricol-work:v2 > /dev/null 2>&1
echo done > $O/DONE
