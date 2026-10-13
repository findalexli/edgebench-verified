#!/bin/bash
# CPU-quota measurement (4 vs 8 CPUs) for per-case wall-clock-limited game graders. Runs each task's ORIGINAL
# eval_cmd in its digest-pinned judge image, --network none --memory 4g, one arm at a time. The submitted
# solution.py is an EBV wrapper (bind-mounted read-only) that runs an honest control (/ebvsol/base.py, also
# bind-mounted) and then does a fixed amount of extra work (W CPU-seconds in total, or until a W-second wall
# deadline), then prints the control's valid answer. Each wrapper writes start/end wall time and CPU used to
# /ebvtiming/<pid>.txt (a per-arm host dir); this does not affect grading.
# /job/arms.txt lines: "<task> <label> <cpus> <wrapper file in /job/sol>".
set -uo pipefail
declare -A IMG WD EVAL WIMG
IMG[vib]=seededge/edgebench.judge.vibrating_path_graph_coloring@sha256:db8a9741831762040afb7e9819f997eb5f5293641fd5cd97d27fce3880ce084e
WD[vib]=/home/workspace/vibrating_path; EVAL[vib]='cd /home/workspace/vibrating_path && python3 /tmp/eval_vibrating_path.py'
IMG[tri]=seededge/edgebench.judge.triangulation_coloring_optimization@sha256:beeea76373084ef4e1fe5324172cf4d5fbc166943daf4cd8b60306cd89dcf671
WD[tri]=/home/workspace/triangulation_coloring; EVAL[tri]='cd /home/workspace/triangulation_coloring && python3 /tmp/eval_triangulation_coloring.py'
IMG[apple]=seededge/edgebench.judge.apple_incremental_game@sha256:d3af7b43331078bb3ef29fab70c502cbb72d0e08d52e59cf9bdb044105d63f39
WD[apple]=/home/workspace/apple_incremental_game; EVAL[apple]='cd /home/workspace/apple_incremental_game && python3 /tmp/eval_apple_incremental_game.py'
WIMG[apple]=seededge/edgebench.work.apple_incremental_game@sha256:1da3e03d8c2004326af535cb0603a56cb236c5fbfa5185ac65327b551f03237f
IMG[treant]=seededge/edgebench.judge.treant_forest@sha256:783e9ca24139ac6aa672ec0576b5f75648e8ad47c0d937988deeb41b639bf21a
WD[treant]=/home/workspace/treants_forest; EVAL[treant]='cd /home/workspace/treants_forest && python3 /tmp/eval_treants_forest.py'
WIMG[treant]=seededge/edgebench.work.treant_forest@sha256:dd1c9593f180b1acabdae7bd20cfe31d99e39a554de42861c37f8a4604d59e23
O=/job/out; mkdir -p $O/logs $O/timing $O/docs
{ nproc; free -m; lscpu | grep -E 'Model name|^CPU\(s\)|Thread'; docker version --format '{{.Server.Version}}'; } > $O/env.txt 2>&1
TASKS=$(awk '{print $1}' /job/arms.txt | sort -u)
for t in $TASKS; do
  docker pull -q ${IMG[$t]} >> $O/pull.log 2>&1 || { echo "pull-failed $t" | tee -a $O/summary.txt; exit 2; }
  docker image inspect ${IMG[$t]} --format "$t {{.Id}} {{.RepoDigests}}" >> $O/image.txt
  E=$(echo "${EVAL[$t]}" | grep -o '/tmp/eval_[a-z_]*\.py')
  docker run --rm --network none ${IMG[$t]} bash -c "sha256sum $E; grep -n 'TIME_LIMIT =\|max_workers\|float(.inf.)\|\"TLE\", ' $E; cd ${WD[$t]} && ls cases | wc -l && grep -niE 'second|time limit|timeout|cpu|core|thread|parallel|wall' README.md" > $O/docs/$t-judge.txt 2>&1
  if [ -n "${WIMG[$t]:-}" ]; then
    docker pull -q ${WIMG[$t]} >> $O/pull.log 2>&1
    docker run --rm --network none ${WIMG[$t]} bash -c "cd ${WD[$t]} && sha256sum README.md tools/README.md; grep -rniE 'second|time limit|timeout|cpu|core|thread|parallel|wall' --include='*.md' ." > $O/docs/$t-work.txt 2>&1
    docker image rm ${WIMG[$t]} > /dev/null 2>&1
  fi
done
sha256sum /job/sol/* /job/base/* > $O/solutions_sha.txt
while read -r task label cpus sol; do
  [ -z "$task" ] && continue
  T=$O/timing/$task-$label; mkdir -p $T; chmod 777 $T
  t0=$(date +%s.%N)
  timeout 1500 docker run --rm --network none --memory 4g --cpus $cpus \
    -v /job/sol/$sol:${WD[$task]}/solution.py:ro -v /job/base/$task.py:/ebvsol/base.py:ro -v $T:/ebvtiming \
    ${IMG[$task]} bash -c "${EVAL[$task]}" > $O/logs/$task-$label.log 2> $O/logs/$task-$label.err
  rc=$?; L=$O/logs/$task-$label.log
  echo "$task $label cpus=$cpus sol=$sol exit=$rc wall=$(python3 -c "print(round($(date +%s.%N)-$t0,1))" 2>/dev/null)s OK=$(grep -c ' OK ' $L) TLE=$(grep -c ' TLE ' $L) WA=$(grep -c ' WA ' $L) RE=$(grep -c ' RE ' $L) $(grep -E '^TOTAL_SCORE' $L)" | tee -a $O/summary.txt
done < /job/arms.txt
echo done >> $O/summary.txt
