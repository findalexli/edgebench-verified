#!/usr/bin/env bash
# Usage: probe.sh <task_id> <image@digest> <project dir> <root module>
# Writes out/<task>/aux_targets.txt from classify.txt and runs AuxProbe in the judge baseline repo.
set -uo pipefail
# machine-wide heavy-job lock (BRIEF HARD RULE)
exec 9>/tmp/ebv-heavy.lock && flock -w 7200 9 || { echo "LOCK TIMEOUT"; exit 5; }
HERE="$(cd "$(dirname "$0")" && pwd)"; T=$1; IMG=$2; P=$3; ROOT=$4; O=$HERE/out/$T
grep -oE '^  AUX \S+' $O/classify.txt | awk '{print $2}' > $O/aux_targets.txt
sed "s/@ROOT@/$ROOT/" $HERE/AuxProbe.lean.tmpl > $O/AuxProbe.lean
timeout 3600 docker run --rm --network none --memory 4g --cpus 2 -v "$O":/out --entrypoint bash "$IMG" -c "
  cd /home/workspace/judge/se-bmk-intern/$P && cp /out/AuxProbe.lean ./EbvAuxProbe.lean && lake env lean EbvAuxProbe.lean" > $O/aux_probe.out 2>&1
echo "probe rc=$?"; grep -c AUXPROBE $O/aux_probe.out
