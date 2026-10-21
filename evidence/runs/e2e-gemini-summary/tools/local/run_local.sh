#!/bin/bash
# run_local.sh JOB BUDGET: run one e2e job (evidence/runs/JOB, same run.sh as on E2B) in a local stand-in for
# the E2B worker: a Docker-in-Docker container with 8 CPUs and 8 GiB (the E2B worker's size), its own dockerd
# on the overlay2 store and its own volume, so the host's Docker keeps no images or settings from the run.
# One heavy local job at a time (the host has 15 GB). The Gemini key is mounted read-only at /run/ebv/gemini_key.
set -u
exec 9>/tmp/ebv-heavy.lock && flock 9
R=/home/alex/edgebench-verified; E=$(cd $(dirname $0)/.. && pwd)
J=$1; B=$2; D=$R/evidence/runs/$J; N=ebv-lw-${J#e2e-gemini-}; N=${N//_/-}
mkdir -p $D/result
ts() { date -u +%Y-%m-%dT%H:%M:%S+00:00; }
echo "{\"job\": \"$J\", \"backend\": \"local-dind\", \"container\": \"$N\", \"started\": \"$(ts)\"}" > $D/result/worker.json
docker rm -f $N >/dev/null 2>&1; docker volume rm $N >/dev/null 2>&1
docker run -d --privileged --name $N --cpus 8 --memory 8g --memory-swap 8g -e DOCKER_TLS_CERTDIR= \
  -v $N:/var/lib/docker -v $D:/job-src:ro -v /home/alex/edgebench-verified/.internal/gemini_key:/run/ebv/gemini_key:ro \
  ebv-local-worker:1 --storage-driver overlay2 --feature containerd-snapshotter=false >/dev/null || exit 1
for i in $(seq 60); do docker exec $N docker info >/dev/null 2>&1 && break; sleep 2; done
docker exec $N sh -c 'mkdir -p /job && cd /job-src && tar --exclude="./result*" -cf - . | tar -xf - -C /job && mkdir -p /job/out'
START=$(date +%s)
docker exec $N bash -c "cd /job && timeout $B bash run.sh > /job/out/run.log 2>&1; echo \$? > /job/out/exit_code"
RC=$(docker exec $N cat /job/out/exit_code 2>/dev/null || echo missing)
docker exec $N sh -c 'docker images --digests; df -h /var/lib/docker' > $D/result/local_after.txt 2>&1
docker cp $N:/job/out $D/result/out >/dev/null 2>&1 || RC="collect-failed($RC)"
python3 - $D/result/worker.json "$RC" $START <<'P'
import json, sys, time
p, rc, st = sys.argv[1], sys.argv[2], int(sys.argv[3]); w = json.load(open(p))
import pathlib
re_ = pathlib.Path(p).parent / 'out/run_exit.txt'
w.update(status=f'exit={rc}', run_exit=re_.read_text().strip() if re_.exists() else None, ended=time.strftime('%Y-%m-%dT%H:%M:%S+00:00', time.gmtime()), elapsed_s=int(time.time()) - st,
         limits={'cpus': 8, 'memory': '8g', 'storage_driver': 'overlay2'})
json.dump(w, open(p, 'w'), indent=1)
P
docker rm -f $N >/dev/null; docker volume rm $N >/dev/null
echo "$J exit=$RC"
