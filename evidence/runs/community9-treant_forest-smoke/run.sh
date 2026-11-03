#!/bin/bash
# treant_forest: real runs at the turn cap; old vs linear rescale; tester without the cap as a measurement.
# Judge built from source: EdgeBench community @ 1187e2ca503d5ba3b4d23a50e7851f730a8126de.
set -uo pipefail
T=treant_forest; SHA=1187e2ca503d5ba3b4d23a50e7851f730a8126de; O=/job/out; mkdir -p $O/g; cd /job
START=$(date +%s); LIMIT=1000
{ nproc; free -m; df -h /; date -u; docker version --format '{{.Server.Version}}'; } >$O/env.txt 2>&1
( while true; do echo "$(date -u +%T) $(df -m / | tail -n 1)"; sleep 30; done ) >$O/df.log 2>&1 &
curl -LsSf https://astral.sh/uv/install.sh | sh >$O/uv.log 2>&1; export PATH=$HOME/.local/bin:$PATH
git clone -q --filter=blob:none --no-checkout -b community https://github.com/ByteDance-Seed/EdgeBench.git base >$O/clone.log 2>&1
( cd base && git sparse-checkout set --no-cone '/*.md' '/tools/' '/pyproject.toml' '/README*' '/LICENSE' '/sforge/' '/edgebench/benchmark.toml' '/edgebench/bases/' "/edgebench/tasks/$T/" && git checkout -q $SHA ) >>$O/clone.log 2>&1 || { echo clone-failed; exit 2; }
git -C base rev-parse HEAD >$O/head.txt
uv venv -q --python 3.12 v >>$O/uv.log 2>&1; uv pip install -q --python v/bin/python -e base >>$O/uv.log 2>&1 || { echo install-failed; exit 4; }
# judge_local.py copy: same grading, also keeps result.json fields and the full log.
sed -e 's/"result_found": bool(result), "log_tail": log\[-3000:\]}/"result_found": bool(result), "log_tail": log[-3000:], "result": result, "log": log[-400000:]}/' \
    -e 's/if k != "log_tail"}/if k not in ("log_tail", "log", "result")}/' base/tools/judge_local.py > /job/jl.py
grep -q '"log": log' /job/jl.py || { echo jl-patch-failed; exit 9; }
cat > /job/bj.py <<'PY'
import sys
from pathlib import Path
from sforge.harness.config import load_config
from sforge.harness.task_spec import load_task
from sforge.harness.docker_build import build_judge_image
spec = load_task(Path('edgebench/tasks/' + sys.argv[1])); print(build_judge_image(spec, load_config({})))
PY
bj(){ ( cd $1 && /job/v/bin/python /job/bj.py $T ) >$O/build-$1.log 2>&1 || { echo build-failed $1; tail -30 $O/build-$1.log; exit 5; }; }
tag(){ ( cd $1 && /job/v/bin/python -c "from pathlib import Path; from sforge.harness.task_spec import load_task; print(load_task(Path('edgebench/tasks/$T')).judge_image_key)" ); }
bj base; IMGOLD=$(tag base); TD=/job/base/edgebench/tasks/$T
echo "old $IMGOLD $(docker image inspect $IMGOLD --format '{{.Id}}')" >$O/tags.txt
sha256sum /job/subs/* >$O/subs.sha 2>/dev/null
echo "setup_s $(( $(date +%s)-START ))" >>$O/summary.txt
fits(){ local el=$(( $(date +%s)-START )); [ $(( el+$1 )) -le $LIMIT ] && return 0; echo "SKIP $2 est=$1 elapsed=$el" >>$O/summary.txt; return 1; }
grade(){ # label image task_dir archive|empty est_seconds
  local lb=$1 img=$2 td=$3 ar=$4 est=$5 a="--empty"
  fits $est $lb || return 0
  [ "$ar" != empty ] && a="--archive $ar"
  ( cd /job/base && /job/v/bin/python /job/jl.py --task-dir $td --image $img $a --out $O/g/$lb.json ) >$O/g/$lb.stdout 2>&1
  local rc=$?; echo "$lb rc=$rc t=$(( $(date +%s)-START )) $(cut -c1-200 $O/g/$lb.stdout | tail -n 1)" >>$O/summary.txt
}
source /job/arms.sh
wait_lanes(){ :; }
docker system df >>$O/env.txt; df -h / >>$O/env.txt; echo done >>$O/summary.txt
