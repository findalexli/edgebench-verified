#!/bin/bash
# Paired run for triangulation_coloring_optimization-v2 package v2.2 (issue #57: convex-hull coverage).
# Three graders on the same submissions, original eval_cmd, --network none --memory 4g, one container at a time:
#   v1  = original judge/work images, pulled by digest;
#   v21 = previous fixed version (package v2.1, judge tag convex-flip-v2.1), built from /job/pkgprev;
#   v22 = new fixed version (package v2.2, judge tag convex-flip-v2.2), built from /job/pkg.
# Sections (outputs under /job/out):
#   geom/   exact hull_check.py on the cases and samples inside every image;
#   A/      flip-rule controls (do nothing, greedy, nonconvex_flip, wrong_count), full judge, --cpus 8 and 4;
#   X/      the same controls with the v2.2 cases bind-mounted over cases/ in the v1 and v21 graders (new inputs,
#           same grader code) and the v2.1 cases over cases/ in the v22 grader;
#   B/      CPU-quota arms (honest control + fixed work), --cpus 4 and 8, all three graders;
#   W/      solver-visible loop (work image eval_sample_data.sh + tester);
#   R/      rule isolation: N=4 reflex quadrilateral + one non-convex flip on each v2.2 case, each grader's tester.
# "donothing" runs the image's own shipped solution.py (no copy).
set -uo pipefail
. /job/task.env
J1=$V1
W1=seededge/edgebench.work.triangulation_coloring_optimization@sha256:618da32c3f4d3b8a79ba840ab7c5d3dc75b42e755ca61c575b784d3976c7cd1f
V21=ebv/tricol-judge:v21; V22=ebv/tricol-judge:v22; W21=ebv/tricol-work:v21; W22=ebv/tricol-work:v22
EVAL="cd $WD && python3 $EVALF"
O=/job/out; mkdir -p $O/geom $O/A $O/X $O/B/logs $O/B/timing $O/W $O/R
{ nproc; free -m; lscpu | grep -E 'Model name|^CPU\(s\)'; docker version --format '{{.Server.Version}}'; date -u; } > $O/env.txt 2>&1
pull() { for k in 1 2 3 4 5; do docker pull -q "$1" >> $O/pull.log 2>&1 && return 0; echo "retry $k" >> $O/pull.log; sleep 10; done; return 1; }
pull $J1 && pull $W1 || { echo pull-failed > $O/FAILED; exit 2; }
( cd /job/pkg && docker build -q -f Dockerfile -t $V22 . && docker build -q -f Dockerfile.work -t $W22 . ) > $O/build.log 2>&1 || { echo build-failed > $O/FAILED; exit 3; }
( cd /job/pkgprev && docker build -q -f Dockerfile -t $V21 . && docker build -q -f Dockerfile.work -t $W21 . ) >> $O/build.log 2>&1 || { echo build-prev-failed > $O/FAILED; exit 3; }
for im in $J1 $W1 $V21 $W21 $V22 $W22; do echo "$im $(docker image inspect --format '{{.Id}}' $im)"; done > $O/image_ids.txt
for im in $J1 $V21 $V22; do echo "== $im"; docker run --rm --network none $im bash -c "cd $WD && sha256sum tools/src/*.py tools/bin/tester cases/* $EVALF"; done > $O/hashes_judge.txt 2>&1
for im in $W1 $W21 $W22; do echo "== $im"; docker run --rm --network none $im bash -c "cd $WD && sha256sum tools/src/*.py tools/bin/tester sample_data/*"; done > $O/hashes_work.txt 2>&1

# geom: exact convex-hull coverage / overlap census inside each image (image python, scripts mounted read-only)
for t in v1:$J1:cases v21:$V21:cases v22:$V22:cases w1:$W1:sample_data w21:$W21:sample_data w22:$W22:sample_data; do
  IFS=: read -r tag im dir <<<"$t"
  timeout 900 docker run --rm --network none --memory 2g -v /job/geom:/geom:ro $im bash -c "cd $WD && python3 -I /geom/v2/hull_check.py $dir/*.txt" > $O/geom/$tag.jsonl 2> $O/geom/$tag.err
  echo "$tag exit=$?" >> $O/geom/status.txt
done

run() { # cpus image label cmd [extra docker args...]
  local c=$1 im=$2 lab=$3 cmd=$4; shift 4
  timeout 1500 docker run --rm --network none --memory 4g --cpus $c -v /job/solutions:/sub:ro -v /job:/jobro:ro "$@" "$im" bash -c "$cmd" > $lab.log 2>&1
  echo "exit=$?" >> $lab.log; }
put() { [ "$1" = donothing ] && echo "true" || echo "cp /sub/$1.py $WD/solution.py"; }

# A: flip-rule controls, full judge
for c in 8 4; do for sol in donothing greedy nonconvex_flip wrong_count; do
  for g in v1:$J1 v21:$V21 v22:$V22; do
    run $c ${g#*:} $O/A/c${c}_${g%%:*}_$sol "$(put $sol) && $EVAL"
  done; done; done
# X: same graders, swapped inputs (cases bind-mounted read-only; materialized files in /job/pkg*/files)
for sol in donothing greedy nonconvex_flip wrong_count; do
  run 8 $J1  $O/X/v1_on_v22cases_$sol  "$(put $sol) && $EVAL" -v /job/pkg/files/cases:$WD/cases:ro
  run 8 $V21 $O/X/v21_on_v22cases_$sol "$(put $sol) && $EVAL" -v /job/pkg/files/cases:$WD/cases:ro
  run 8 $V22 $O/X/v22_on_v21cases_$sol "$(put $sol) && $EVAL" -v /job/pkgprev/files/cases:$WD/cases:ro
done
# W: solver-visible loop
for sol in donothing greedy nonconvex_flip; do
  for g in v1:$W1 v21:$W21 v22:$W22; do
    run 8 ${g#*:} $O/W/${g%%:*}_$sol "$(put $sol) && cd $WD && ./eval_sample_data.sh; for f in sample_data/0*.txt; do python3 solution.py < \$f > /tmp/o; ./tools/bin/tester \$f /tmp/o; done"
  done; done
# R: rule isolation on identical inputs (N=4 + v2.2 cases, one non-convex flip each)
for g in v1:$J1 v21:$V21 v22:$V22; do
  run 8 ${g#*:} $O/R/rule_${g%%:*} "cd $WD && ./tools/bin/tester /jobro/n4_nonconvex.txt /jobro/n4_nonconvex.out; for i in 0 1 2 3 4 5 6 7 8 9; do python3 /sub/nonconvex_flip.py < /jobro/pkg/files/cases/000\$i.txt > /tmp/o; echo case000\$i \$(sed -n 3p /tmp/o); ./tools/bin/tester /jobro/pkg/files/cases/000\$i.txt /tmp/o; done"
done
# B: CPU-quota arms
sha256sum /job/sol/* /job/base/* > $O/B/solutions_sha.txt
for spec in "4 cpu20" "4 cpu28" "4 wall25" "4 spin40" "4 cpu0" "8 cpu20"; do
  set -- $spec; c=$1; s=$2; lab0=c$c-$s; [ $s = cpu0 ] && lab0=c$c-base
  for g in v1:$J1 v21:$V21 v22:$V22; do
    label=$lab0-${g%%:*}; IMG=${g#*:}
    T=$O/B/timing/$label; mkdir -p $T; chmod 777 $T
    t0=$(date +%s.%N)
    timeout 1500 docker run --rm --network none --memory 4g --cpus $c \
      -v /job/sol/$s.py:$WD/solution.py:ro -v /job/base/base.py:/ebvsol/base.py:ro -v $T:/ebvtiming \
      $IMG bash -c "$EVAL" > $O/B/logs/$label.log 2> $O/B/logs/$label.err
    rc=$?; L=$O/B/logs/$label.log
    echo "$label cpus=$c ver=${g%%:*} sol=$s.py exit=$rc wall=$(python3 -c "print(round($(date +%s.%N)-$t0,1))")s OK=$(grep -c ' OK ' $L) TLE=$(grep -c ' TLE ' $L) WA=$(grep -c ' WA ' $L) RE=$(grep -c ' RE ' $L) $(grep -E '^TOTAL_SCORE' $L)" >> $O/B/summary.txt
  done
done
python3 /job/timing.py $O/B/timing > $O/B/timing_summary.txt 2>&1
# one-line summary of A/X
for f in $O/A/*.log $O/X/*.log; do echo "$(basename $f .log) $(grep -E '^CASES_OK' $f | head -1) $(grep -E '^TOTAL_SCORE' $f | head -1) WA=$(grep -c ' WA ' $f) $(grep -E '^exit=' $f)"; done > $O/summary_AX.txt
docker image rm $V21 $V22 $W21 $W22 > /dev/null 2>&1
echo done > $O/DONE
