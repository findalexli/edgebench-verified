#!/bin/bash
# Repeat of the vibrating wall25 arm with tester-start logging. Paired original/fixed evaluation of the CPU-quota parallelism cap (E2B worker, root, /job).
# v1 = digest-pinned original judge image; v2 = built from /job/pkg/Dockerfile (fixed version);
# v2prev (triangulation only) = built from /job/pkgprev/Dockerfile (the package before the cap was added).
# Every arm runs the task's ORIGINAL eval_cmd, --network none --memory 4g --cpus <N>, one container at a time.
# The submitted solution.py is an EBV wrapper (bind-mounted read-only) that runs an honest control
# (/ebvsol/base.py) and then does a fixed amount of extra work (W CPU-seconds in total, or until a W-second
# wall-clock deadline) before printing the control's valid answer; it writes start/end wall time and CPU used to
# /ebvtiming/<pid>.txt (a per-arm host dir), which does not affect grading.
# /job/arms.txt lines: "<label> <cpus> <v1|v2|v2prev> <wrapper file in /job/sol>". /job/task.env sets TASK, V1, WD, EVALF.
set -uo pipefail
. /job/task.env
V2=ebv/$TASK:v2; V2P=ebv/$TASK:v2prev
# -c only: before grading, the container's own tools/bin/tester is renamed tester.real and replaced by a two-line
# shell wrapper that appends "<epoch> <case file>" to /ebvtiming/tester_starts.txt and then execs the real tester
# (same process, same arguments, same pipes). The tester only starts after the solution exited OK within 30 s, so a
# TLE case with a tester start line timed out in the tester (timeout=60), not in the solution. Ephemeral container
# change only; the evaluator is not modified.
EVAL="cd $WD && mv tools/bin/tester tools/bin/tester.real && printf '#!/bin/sh\necho \"\$(date +%%s.%%N) \$1\" >> /ebvtiming/tester_starts.txt\nexec $WD/tools/bin/tester.real \"\$@\"\n' > tools/bin/tester && chmod +x tools/bin/tester && python3 $EVALF"
O=/job/out; mkdir -p $O/logs $O/timing
{ nproc; free -m; lscpu | grep -E 'Model name|^CPU\(s\)|Thread'; docker version --format '{{.Server.Version}}'; date -u; } > $O/env.txt 2>&1
docker pull $V1 > $O/pull.log 2>&1 || { echo pull-failed | tee -a $O/summary.txt; exit 2; }
docker build -t $V2 /job/pkg > $O/build.log 2>&1 || { echo build-failed | tee -a $O/summary.txt; exit 3; }
IMGS="$V1 $V2"
if [ -d /job/pkgprev ]; then docker build -t $V2P /job/pkgprev >> $O/build.log 2>&1 || { echo build-prev-failed | tee -a $O/summary.txt; exit 3; }; IMGS="$IMGS $V2P"; fi
docker image inspect $V1 --format '{{.Id}} {{.RepoDigests}}' > $O/image.txt
for img in $V2 $V2P; do docker image inspect $img --format "$img {{.Id}}" 2>/dev/null; done > $O/v2_image_id.txt
for img in $IMGS; do echo "== $img"; docker run --rm --network none $img bash -c "sha256sum $EVALF; ls -l $EVALF; grep -n 'max_workers' $EVALF; cd $WD && sha256sum cases/* tools/src/*.py 2>/dev/null | sha256sum"; done > $O/eval_sha.txt 2>&1
for c in 1 2 3 4 8; do echo "cpus=$c $(docker run --rm --network none --cpus $c $V2 python3 -c "import sys; sys.path.insert(0, '$(dirname $EVALF)'); import $(basename $EVALF .py) as e; print(open('/sys/fs/cgroup/cpu.max').read().strip(), 'workers', e.cpu_quota_workers())" 2>&1)"; done > $O/v2_workers.txt
sha256sum /job/sol/* /job/base/* > $O/solutions_sha.txt
# optional: tester time per case on the honest control's output, one case at a time, 1 CPU, original image
if [ -f /job/tester_time.sh ]; then
  timeout 900 docker run --rm --network none --memory 2g --cpus 1 -v /job/base/base.py:$WD/solution.py:ro -v /job/tester_time.sh:/t.sh:ro $V1 bash /t.sh > $O/tester_time.out 2>&1
  echo "tester_time exit=$? cases=$(grep -c . $O/tester_time.out) max=$(tail -1 $O/tester_time.out)" | tee -a $O/summary.txt
fi
while read -r label cpus ver sol; do
  [ -z "$label" ] && continue
  case $ver in v1) IMG=$V1;; v2) IMG=$V2;; v2prev) IMG=$V2P;; esac
  T=$O/timing/$label; mkdir -p $T; chmod 777 $T
  t0=$(date +%s.%N)
  timeout 1500 docker run --rm --network none --memory 4g --cpus $cpus \
    -v /job/sol/$sol:$WD/solution.py:ro -v /job/base/base.py:/ebvsol/base.py:ro -v $T:/ebvtiming \
    $IMG bash -c "$EVAL" > $O/logs/$label.log 2> $O/logs/$label.err
  rc=$?; L=$O/logs/$label.log
  echo "$label cpus=$cpus ver=$ver sol=$sol exit=$rc wall=$(python3 -c "print(round($(date +%s.%N)-$t0,1))" 2>/dev/null)s OK=$(grep -c ' OK ' $L) TLE=$(grep -c ' TLE ' $L) WA=$(grep -c ' WA ' $L) RE=$(grep -c ' RE ' $L) $(grep -E '^TOTAL_SCORE' $L)" | tee -a $O/summary.txt
done < /job/arms.txt
python3 /job/timing.py $O/timing > $O/timing_summary.txt 2>&1
docker image rm $V2 $V2P >/dev/null 2>&1; echo done >> $O/summary.txt
