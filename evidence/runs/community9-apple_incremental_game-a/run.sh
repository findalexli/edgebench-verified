#!/bin/bash
# Old vs new case pool for apple_incremental_game on EdgeBench community @ 1187e2ca503d5ba3b4d23a50e7851f730a8126de: build both from source on this
# worker, grade the same real archives with `sforge eval` (it passes the task's cpus=4 as a Docker CPU quota and sets SFORGE_CPUS=4).
# cond hot4: only 4 vCPUs online, one judge at a time. cond q4: all 8 vCPUs online, one judge. cond x2/x3: 8 online, 2 or 3 judges at once.
set -uo pipefail
T=apple_incremental_game; SHA=1187e2ca503d5ba3b4d23a50e7851f730a8126de; O=/job/out; mkdir -p $O/s; cd /job
START=$(date +%s); LIMIT=3200
{ nproc; free -m; date -u; docker version --format '{{.Server.Version}}'; lscpu; id; stat -fc %T /sys/fs/cgroup; uname -a; grep . /sys/devices/system/cpu/cpu*/topology/thread_siblings_list; } >$O/env.txt 2>&1
curl -LsSf https://astral.sh/uv/install.sh | sh >$O/uv.log 2>&1; export PATH=$HOME/.local/bin:$PATH
git clone -q --filter=blob:none --no-checkout -b community https://github.com/ByteDance-Seed/EdgeBench.git base >$O/clone.log 2>&1
( cd base && git sparse-checkout set --no-cone '/*.md' '/tools/' '/pyproject.toml' '/README*' '/LICENSE' '/sforge/' '/edgebench/benchmark.toml' '/edgebench/bases/' "/edgebench/tasks/$T/" && git checkout -q $SHA ) >>$O/clone.log 2>&1 || { echo clone-failed; exit 2; }
cp -r base new; ( cd new && git apply /job/pr.patch ) || { echo patch-failed; exit 3; }
uv venv -q --python 3.12 v >>$O/uv.log 2>&1; uv pip install -q --python v/bin/python -e base >>$O/uv.log 2>&1 || { echo install-failed; exit 4; }
tag(){ ( cd $1 && /job/v/bin/python -c "from pathlib import Path; from sforge.harness.task_spec import load_task; print(load_task(Path('edgebench/tasks/$T')).judge_image_key)" ); }
for t in base new; do ( cd $t && /job/v/bin/python -m sforge build --task $T ) >$O/build-$t.log 2>&1 || { echo build-failed $t; tail -30 $O/build-$t.log; exit 5; }; done
IMGOLD=$(tag base); IMGNEW=$(tag new); echo "old $IMGOLD new $IMGNEW" >$O/tags.txt
[ "$IMGOLD" != "$IMGNEW" ] || { echo same-image; exit 6; }
for x in "old $IMGOLD" "new $IMGNEW"; do set -- $x; docker run --rm --network none --entrypoint sh $2 -c 'find /judge -type f -not -path "*/cases/*" | sort | xargs sha256sum; grep -n "^TIME_LIMIT\|max_workers" /judge/eval_apple_incremental_game.py' >$O/judge-$1.sha 2>&1; done
sha256sum /job/subs/* >$O/subs.sha
echo "setup_s $(( $(date +%s)-START ))" >>$O/summary.txt
SUDO=""; [ "$(id -u)" = 0 ] || SUDO=sudo
cpus(){ local n=$1 c i v; for c in /sys/devices/system/cpu/cpu[0-9]*; do i=${c##*cpu}; [ "$i" = 0 ] && continue; [ -e $c/online ] || continue; [ $i -lt $n ] && v=1 || v=0; echo $v | $SUDO tee $c/online >/dev/null 2>>$O/hotplug.err; done; echo "cpus $n online=$(cat /sys/devices/system/cpu/online) t=$(( $(date +%s)-START ))" >>$O/summary.txt; }
sampler(){ declare -A seen; while :; do
  local now=$(date +%s); echo "H $now $(cut -d' ' -f1-3 /proc/loadavg) $(cat /sys/devices/system/cpu/online) $(head -1 /proc/stat)" >>$O/sampler.txt
  for id in $(docker ps -q --no-trunc --filter name=sforge.judge 2>/dev/null); do
    if [ -z "${seen[$id]:-}" ]; then seen[$id]=$(docker inspect --format '{{.Name}}' $id 2>/dev/null | tr -d /)
      echo "I $now ${seen[$id]} $(docker inspect --format 'nano={{.HostConfig.NanoCpus}} cpuset={{.HostConfig.CpusetCpus}} mem={{.HostConfig.Memory}} env={{.Config.Env}}' $id 2>/dev/null | tr ' ' ',' ) inside=$(docker exec $id sh -c 'cat /sys/fs/cgroup/cpu.max 2>/dev/null; nproc' 2>/dev/null | tr '\n ' ',_')" >>$O/sampler.txt; fi
    for p in /sys/fs/cgroup/system.slice/docker-$id.scope /sys/fs/cgroup/docker/$id /sys/fs/cgroup/cpu,cpuacct/docker/$id; do
      [ -r $p/cpu.stat ] && { echo "C $now ${seen[$id]} $(tr '\n' ' ' <$p/cpu.stat)" >>$O/sampler.txt; break; }; done
  done; sleep 2; done; }
sampler & SAMP=$!; trap 'kill $SAMP 2>/dev/null' EXIT
calib(){ /job/v/bin/python - "$1" "$(cat /sys/devices/system/cpu/online)" >>$O/calib.txt <<'PY'
import multiprocessing as m, os, sys, time
def w(q):
    t = time.time(); c = 0
    while time.time() - t < 2:
        for _ in range(10000): c += 1
    q.put(c / 2)
n = os.cpu_count(); r = []
for k in (1, n):
    q = m.Queue(); P = [m.Process(target=w, args=(q,)) for _ in range(k)]; [p.start() for p in P]; v = [q.get() for _ in P]; [p.join() for p in P]; r.append((k, round(sum(v) / k / 1e6, 2)))
print(sys.argv[1], sys.argv[2], 'Mloops/s/proc', r, flush=True)
PY
}
fits(){ local el=$(( $(date +%s)-START )); [ $(( el+$1 )) -le $LIMIT ] && return 0; echo "SKIP $2 est=$1 elapsed=$el" >>$O/summary.txt; return 1; }
seval1(){ # label side alias   (real harness; --silent must precede the subcommand)
  local l=$1 sd=$2 d t0=$(date +%s) rc; [ $sd = old ] && d=base || d=new
  ( cd $d && /job/v/bin/python -m sforge --silent --log-dir /job/sl eval --task $T --archive /job/subs/$3.tar.gz --run-id $l --json ) >$O/s/$l.log 2>&1; rc=$?
  local r=/job/sl/runs/$l/$T/submissions/manual-1
  for f in report.json judge_output.txt run_instance.log; do [ -f $r/$f ] && cp $r/$f $O/s/$l.$f; done
  echo "arm $l side=$sd sub=$3 rc=$rc start=$t0 end=$(date +%s) online=$(cat /sys/devices/system/cpu/online)" >>$O/summary.txt
}
# ev <cond> <round> <side> <alias> <est_s>: one judge (hot4 or q4), or x2/x3: that many judges at once on the same archive
ev(){ local cond=$1 rd=$2 sd=$3 a=$4 est=$5 k i; fits $est "$cond-$a-$sd-r$rd" || return 0
  case $cond in hot4) cpus 4; k=1;; q4) cpus 8; k=1;; x2) cpus 8; k=2;; x3) cpus 8; k=3;; *) echo bad-cond; return 1;; esac
  if [ $k = 1 ]; then seval1 $cond-$a-$sd-r$rd $sd $a; else for i in $(seq 1 $k); do seval1 $cond-$a-$sd-r$rd-k$i $sd $a & P[$i]=$!; done; for i in $(seq 1 $k); do wait ${P[$i]}; done; fi
}
declare -a P
source /job/arms.sh
cpus 8; calib end; docker system df >>$O/env.txt; echo done >>$O/summary.txt
