#!/bin/bash
# Old vs fixed judge for schemathesis_reporting_observability on EdgeBench community @ 1187e2ca503d5ba3b4d23a50e7851f730a8126de. Both are built from source
# on this worker. grade = tools/judge_local.py with the full log kept (then trimmed to test lines); seval = `sforge eval`.
set -uo pipefail
T=schemathesis_reporting_observability; SHA=1187e2ca503d5ba3b4d23a50e7851f730a8126de; O=/job/out; mkdir -p $O/g $O/s; cd /job
START=$(date +%s); LIMIT=1300
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
sed 's/log\[-3000:\]/log/' base/tools/judge_local.py > /job/jl.py
cat > /job/trim.py <<'P'
import json,re,sys
f=sys.argv[1]; d=json.load(open(f))
keep=[l[:220] for l in (d.get("log_tail") or "").splitlines() if re.search(r" PASSED| FAILED| ERROR|^Phase \d|TOTAL_SCORE|^E   |^CASE |GATE OK|gate failed|MT/s|BUILD |Tests run:",l)]
d["log_tail"]="\n".join(keep[-300:]); json.dump(d,open(f,"w"),indent=1)
P
[ -f /job/mk.py ] && /job/v/bin/python /job/mk.py $T /job/subs >$O/mk.log 2>&1
sha256sum /job/subs/* >$O/subs.sha
echo "setup_s $(( $(date +%s)-START ))" >>$O/summary.txt
fits(){ local el=$(( $(date +%s)-START )); [ $(( el+$1 )) -le $LIMIT ] && return 0; echo "SKIP $2 est=$1 elapsed=$el" >>$O/summary.txt; return 1; }
grade(){ # label side archive-or-empty est_seconds
  local sd=$2 img d; [ $sd = old ] && { img=$IMGOLD; d=base; } || { img=$IMGNEW; d=new; }
  fits $4 "$1-$sd" || return 0
  local a="--empty"; [ "$3" != empty ] && a="--archive /job/subs/$3"
  ( cd $d && /job/v/bin/python /job/jl.py --task-dir edgebench/tasks/$T --image $img $a --out $O/g/$1-$sd.json ) >>$O/g/stdout.jsonl 2>>$O/g/stderr.log
  local rc=$?; /job/v/bin/python /job/trim.py $O/g/$1-$sd.json
  echo "$1 $sd rc=$rc t=$(( $(date +%s)-START ))" >>$O/summary.txt
}
seval(){ # label side archive est_seconds: real harness path
  local sd=$2 d; [ $sd = old ] && d=base || d=new
  fits $4 "$1-$sd-sforge" || return 0
  ( cd $d && /job/v/bin/python -m sforge eval --task $T --archive /job/subs/$3 --run-id $1-$sd --silent --json ) >$O/s/$1-$sd.log 2>&1
  echo "sforge $1 $sd rc=$? t=$(( $(date +%s)-START ))" >>$O/summary.txt
  ( cd $d && find . -path "*runs/$1-$sd/*" \( -name 'test_output.txt' -o -name report.json \) | while read f; do cp "$f" "$O/s/$1-$sd.$(basename "$f")"; done )
}
source /job/arms.sh
docker system df >>$O/env.txt; echo done >>$O/summary.txt
