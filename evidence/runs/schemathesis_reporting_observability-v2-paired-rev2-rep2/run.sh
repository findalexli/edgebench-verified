#!/bin/bash
# Paired evaluation (EdgeBench Verified), revision of 2026-10-12. Runs as root in /job on an E2B worker with Docker.
# Three graders on the same submissions:
#   v1     = original pinned judge image;
#   v2prev = first published fixed version, built from ./v2prev/Dockerfile (FROM the same digest);
#   v2     = revised fixed version, built from ./v2/Dockerfile (FROM the same digest).
# Every variant in ./variants/<name>/apply.sh is sourced inside a fresh --network none container,
# then the task's ORIGINAL judge.eval_cmd (./eval_cmd.sh, extracted verbatim from tasks/<task>.json) runs.
set -u
cd /job; . ./job.env   # IMAGE=..., PAR=...
ARMS="v1 v2prev v2"
mkdir -p out; exec 3>out/progress.log
log(){ echo "$(date -u +%FT%TZ) $*" | tee -a /dev/fd/3; }
log "pull $IMAGE"; docker pull -q "$IMAGE" >&3 2>&1 || { log "pull failed"; exit 2; }
docker tag "$IMAGE" ebv/v1:latest
for a in v2prev v2; do log "build $a"; docker build -q -t ebv/$a:latest ./$a >&3 2>&1 || { log "build $a failed"; exit 3; }; done
for i in $ARMS; do docker run --rm --network none --entrypoint sh ebv/$i:latest -c 'sha256sum /tests/*' > out/tests-$i.sha256; done
docker image inspect ebv/v1:latest ebv/v2prev:latest ebv/v2:latest --format '{{.Id}} {{.RepoTags}}' > out/image-ids.txt
run_one(){ # $1 variant $2 image
  local v=$1 i=$2 o=/job/out/runs/$1.$2; mkdir -p $o
  local t0=$(date +%s)
  timeout 1000 docker run --rm --network none --memory 3g --cpus 2 -v /job:/job:ro -v $o:/out ebv/$i:latest \
    bash -c '. /job/variants/'$v'/apply.sh > /out/apply.log 2>&1 && bash /job/eval_cmd.sh > /out/eval_stdout.log 2>&1; echo $? > /out/eval_exit; cp /tmp/test_full.log /tmp/structured_result.log /out/ 2>/dev/null; cp -r /logs/verifier /out/verifier 2>/dev/null; true'
  echo $? > $o/docker_exit; echo $(( $(date +%s) - t0 )) > $o/seconds
  log "done $v $i exit=$(cat $o/docker_exit) $(cat $o/seconds)s"
}
export -f run_one log
JOBS=(); for v in $(ls variants); do for i in $ARMS; do JOBS+=("$v $i"); done; done
printf '%s\n' "${JOBS[@]}" | xargs -P "${PAR:-2}" -L1 bash -c 'exec 3>>/job/out/progress.log; run_one $0 $1'
python3 ./summarize.py out/runs > out/summary.md 2>out/summarize.err
log "finished"
