#!/bin/bash
# Old vs new judge for arc_compiler_runtime (current judge only) on EdgeBench community @ 1187e2ca503d5ba3b4d23a50e7851f730a8126de: build both from
# source on this worker, grade the same submissions with tools/judge_local.py and/or `sforge eval`.
set -uo pipefail
T=arc_compiler_runtime; SHA=1187e2ca503d5ba3b4d23a50e7851f730a8126de; O=/job/out; mkdir -p $O/g $O/s; cd /job
START=$(date +%s); LIMIT=3240
nproc >$O/env.txt; free -m >>$O/env.txt; date -u >>$O/env.txt; docker version --format '{{.Server.Version}}' >>$O/env.txt
curl -LsSf https://astral.sh/uv/install.sh | sh >$O/uv.log 2>&1; export PATH=$HOME/.local/bin:$PATH
git clone -q --filter=blob:none --no-checkout -b community https://github.com/ByteDance-Seed/EdgeBench.git base >$O/clone.log 2>&1
( cd base && git sparse-checkout set --no-cone '/*.md' '/tools/' '/pyproject.toml' '/README*' '/LICENSE' '/sforge/' '/edgebench/benchmark.toml' '/edgebench/bases/' "/edgebench/tasks/$T/" && git checkout -q $SHA ) >>$O/clone.log 2>&1 || { echo clone-failed; exit 2; }
cp -r base new; ( cd new && git apply /job/pr.patch ) || { echo patch-failed; exit 3; }
uv venv -q --python 3.12 v >>$O/uv.log 2>&1; uv pip install -q --python v/bin/python -e base >>$O/uv.log 2>&1 || { echo install-failed; exit 4; }
tag(){ ( cd $1 && /job/v/bin/python -c "from pathlib import Path; from sforge.harness.task_spec import load_task; print(load_task(Path('edgebench/tasks/$T')).judge_image_key)" ); }
for t in base new; do ( cd $t && /job/v/bin/python -m sforge build --task $T ) >$O/build-$t.log 2>&1 || { echo build-failed $t; tail -30 $O/build-$t.log; exit 5; }; done
docker images --format '{{.Repository}}:{{.Tag}} {{.ID}}' | grep -E 'edgebench\.(judge|work)' >$O/images.txt
IMGOLD=$(tag base); IMGNEW=$(tag new); echo "old $IMGOLD new $IMGNEW" >$O/tags.txt
docker image inspect $IMGOLD --format '{{.Id}}' >>$O/tags.txt; docker image inspect $IMGNEW --format '{{.Id}}' >>$O/tags.txt
for x in "old $IMGOLD" "new $IMGNEW"; do set -- $x; docker run --rm --network none --entrypoint sh $2 -c 'find /judge -type f | sort | xargs sha256sum; grep -n "^TIME_LIMIT\|max_workers" /judge/eval_warehouse_manager.py' >$O/judge-$1.sha 2>&1; done
sha256sum /job/subs/* >$O/subs.sha
echo "setup_s $(( $(date +%s)-START ))" >>$O/summary.txt
fits(){ local el=$(( $(date +%s)-START )); [ $(( el+$1 )) -le $LIMIT ] && return 0; echo "SKIP $2 est=$1 elapsed=$el" >>$O/summary.txt; return 1; }
grade(){ # label side archive-or-empty est_seconds [judge_local]
  local sd=$2 img d; [ $sd = old ] && { img=$IMGOLD; d=base; } || { img=$IMGNEW; d=new; }
  fits $4 "$1-$sd" || return 0
  local a="--empty"; [ "$3" != empty ] && a="--archive /job/subs/$3"
  ( cd $d && /job/v/bin/python tools/judge_local.py --task-dir edgebench/tasks/$T --image $img $a --out $O/g/$1-$sd.json ) >>$O/g/stdout.jsonl 2>>$O/g/stderr.log
  echo "$1 $sd rc=$? t=$(( $(date +%s)-START ))" >>$O/summary.txt
}
seval(){ # label side archive est_seconds [real harness path]
  local sd=$2 d; [ $sd = old ] && d=base || d=new
  fits $4 "$1-$sd-sforge" || return 0
  ( cd $d && /job/v/bin/python -m sforge eval --task $T --archive /job/subs/$3 --run-id $1-$sd --silent --json ) >$O/s/$1-$sd.log 2>&1
  echo "sforge $1 $sd rc=$? t=$(( $(date +%s)-START ))" >>$O/summary.txt
  ( cd $d && find . -path "*runs/$1-$sd/*" -name 'test_output.txt' -exec cp {} $O/s/$1-$sd.test_output.txt \; )
}
source /job/arms.sh
docker system df >>$O/env.txt; echo done >>$O/summary.txt
