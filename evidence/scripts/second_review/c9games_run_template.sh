#!/bin/bash
# EdgeBench community @ 1187e2ca503d5ba3b4d23a50e7851f730a8126de: build the judge(s) from source on this worker and grade with `sforge eval`.
# Arms are in arms.sh. /job/sides lists what to build (base, or base new); pr.patch is applied to the "new" tree only.
set -uo pipefail
T=__TASK__; SHA=1187e2ca503d5ba3b4d23a50e7851f730a8126de; O=/job/out; mkdir -p $O/g $O/s $O/sf $O/d; cd /job
START=$(date +%s); LIMIT=$(cat /job/limit)
SIDES=$(cat /job/sides)
nproc >$O/env.txt; free -m >>$O/env.txt; date -u >>$O/env.txt; docker version --format '{{.Server.Version}}' >>$O/env.txt; df -h / >>$O/env.txt
curl -LsSf https://astral.sh/uv/install.sh | sh >$O/uv.log 2>&1; export PATH=$HOME/.local/bin:$PATH
git clone -q --filter=blob:none --no-checkout -b community https://github.com/ByteDance-Seed/EdgeBench.git base >$O/clone.log 2>&1
( cd base && git sparse-checkout set --no-cone '/*.md' '/tools/' '/pyproject.toml' '/README*' '/LICENSE' '/sforge/' '/edgebench/benchmark.toml' '/edgebench/bases/' "/edgebench/tasks/$T/" && git checkout -q $SHA && git rev-parse HEAD ) >>$O/clone.log 2>&1 || { echo clone-failed; exit 2; }
cp -r base new; ( cd new && git apply /job/pr.patch ) || { echo patch-failed; exit 3; }
uv venv -q --python 3.12 v >>$O/uv.log 2>&1; uv pip install -q --python v/bin/python -e base >>$O/uv.log 2>&1 || { echo install-failed; exit 4; }
tag(){ ( cd $1 && /job/v/bin/python -c "from pathlib import Path; from sforge.harness.task_spec import load_task; print(load_task(Path('edgebench/tasks/$T')).judge_image_key)" ); }
for t in $SIDES; do ( cd $t && /job/v/bin/python -m sforge build --task $T ) >$O/build-$t.log 2>&1 || { echo build-failed $t; tail -30 $O/build-$t.log; exit 5; }; done
docker images --format '{{.Repository}}:{{.Tag}} {{.ID}} {{.Size}}' | grep -E 'edgebench\.(judge|work)' >$O/images.txt
IMGOLD=$(tag base); IMGNEW=$IMGOLD; case " $SIDES " in *" new "*) IMGNEW=$(tag new);; esac
echo "old $IMGOLD new $IMGNEW" >$O/tags.txt
docker image inspect $IMGOLD --format '{{.Id}}' >>$O/tags.txt; docker image inspect $IMGNEW --format '{{.Id}}' >>$O/tags.txt
for x in "old $IMGOLD" "new $IMGNEW"; do set -- $x; docker run --rm --network none --entrypoint sh $2 -c 'find /judge -type f | sort | xargs sha256sum' >$O/judge-$1.sha 2>&1; done
sha256sum /job/subs/* >$O/subs.sha
echo "setup_s $(( $(date +%s)-START ))" >>$O/summary.txt
fits(){ local el=$(( $(date +%s)-START )); [ $(( el+$1 )) -le $LIMIT ] && return 0; echo "SKIP $2 est=$1 elapsed=$el" >>$O/summary.txt; return 1; }
seval(){ # label side archive est_seconds: the official path, a fresh judge container with task.toml limits and SFORGE_CPUS
  local sd=$2 d; [ $sd = old ] && d=base || d=new
  fits $4 "$1-$sd" || return 0
  local t0=$(date +%s)
  ( cd $d && /job/v/bin/python -m sforge --silent --log-dir $O/sf eval --task $T --archive /job/subs/$3 --run-id $1-$sd --json ) >$O/s/$1-$sd.log 2>&1
  echo "sforge $1 $sd rc=$? wall=$(( $(date +%s)-t0 )) t=$(( $(date +%s)-START ))" >>$O/summary.txt
}
source /job/arms.sh
docker system df >>$O/env.txt; echo done >>$O/summary.txt
