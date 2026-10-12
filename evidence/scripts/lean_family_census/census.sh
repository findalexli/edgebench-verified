#!/usr/bin/env bash
# Host driver: one image at a time. Usage: census.sh <task_id> <image@digest> <project dir>
set -uo pipefail
# machine-wide heavy-job lock (BRIEF HARD RULE)
exec 9>/tmp/ebv-heavy.lock && flock -w 7200 9 || { echo "LOCK TIMEOUT"; exit 5; }
# public images: bypass the broken desktop.exe credential helper with an empty per-process docker config
export DOCKER_CONFIG="${DOCKER_CONFIG_EMPTY:?set DOCKER_CONFIG_EMPTY to a dir containing a {} config.json}"
HERE="$(cd "$(dirname "$0")" && pwd)"; T=$1; IMG=$2; P=$3; O=$HERE/out/$T; mkdir -p $O
AV=$(df --output=avail -BG / | tail -1 | tr -dc 0-9); echo "free ${AV}G" | tee $O/host.log
[ "$AV" -lt 80 ] && { echo "STOP: <80G free" | tee -a $O/host.log; exit 3; }
echo "pull start $(date -u +%T)" >> $O/host.log
docker pull "$IMG" >> $O/host.log 2>&1 || { echo "pull failed, retry once" >> $O/host.log; docker pull "$IMG" >> $O/host.log 2>&1 || { echo PULL_FAILED >> $O/host.log; exit 4; }; }
docker image inspect "$IMG" --format '{{.Size}} {{.Id}}' >> $O/host.log
echo "run start $(date -u +%T)" >> $O/host.log
timeout 10800 docker run --rm --network none --memory 4g --cpus 2 -v "$HERE":/ebv:ro -v "$O":/out --entrypoint bash "$IMG" /ebv/census_in.sh "$P" > $O/census.log 2>&1
echo "run rc=$? $(date -u +%T)" >> $O/host.log
