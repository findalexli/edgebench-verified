#!/usr/bin/env bash
# new_foundations_consistency: verbatim eval_cmd on the unmodified starter WITH network (default bridge),
# as the maintained harness runs the judge container. One container, 4g/2cpu, timeout 3600.
set -uo pipefail
exec 9>/tmp/ebv-heavy.lock && flock -w 7200 9 || { echo "LOCK TIMEOUT"; exit 5; }
export DOCKER_CONFIG="${DOCKER_CONFIG_EMPTY:?}"
HERE="$(cd "$(dirname "$0")" && pwd)"; T=new_foundations_consistency; O=$HERE/out/$T/networked; mkdir -p $O
IMG=seededge/edgebench.judge.new_foundations_consistency@sha256:c17cd5656a55f6797ea47703ebe05591b2e074fa321e4eb1dd6d52ec78e96cc4
echo "free $(df --output=avail -BG / | tail -1)"
docker pull "$IMG" > $O/pull.log 2>&1 || { echo PULL_FAILED; exit 4; }
python3 -I -c "import json,sys;print(json.load(open(sys.argv[1]))['judge']['eval_cmd'])" $HERE/../../../tasks/$T.json > $O/eval_cmd.txt
timeout 3600 docker run --rm --memory 4g --cpus 2 -v "$O":/out --entrypoint bash "$IMG" -c '
EVAL=$(cat /out/eval_cmd.txt); SUB=/home/workspace/se-bmk-intern/con-nf; J=/home/workspace/judge/se-bmk-intern/con-nf
mkdir -p $SUB; ( cd $J && tar c --exclude=./.lake . ) | ( cd $SUB && tar x )
echo "start $(date -u +%T)"
bash -c "$EVAL" > /out/report.json 2> /out/build.err; echo "eval_cmd rc=$?"
echo "end $(date -u +%T)"
for d in $SUB $J; do echo "$d doc-gen4 HEAD=$(git -C $d/.lake/packages/doc-gen4 rev-parse HEAD 2>&1) url=$(git -C $d/.lake/packages/doc-gen4 remote get-url origin 2>&1)"; done
python3 -c "import json;d=json.load(open(\"$SUB/lake-manifest.json\"));print([ (p[\"name\"],p.get(\"rev\")) for p in d[\"packages\"] if \"doc\" in p[\"name\"]])"
cat $SUB/.lake/packages/doc-gen4/lean-toolchain 2>/dev/null
'
echo "run rc=$?"
docker rmi "$IMG" | tail -1
