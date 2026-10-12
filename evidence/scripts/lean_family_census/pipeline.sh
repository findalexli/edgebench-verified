#!/usr/bin/env bash
# One task end-to-end (census -> classify -> aux probe). Image is NOT removed here (native test may follow).
# Usage: pipeline.sh <task_id> <image@digest> <project dir> <root module> [weights file name]
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"; T=$1; IMG=$2; P=$3; ROOT=$4; WF=${5:-}; O=$HERE/out/$T
$HERE/census.sh $T $IMG $P || { echo "census failed rc=$?"; exit 1; }
python3 -I $HERE/classify.py $O/baseline-ListDeclAxiom.out ${WF:+$O/$WF} -v > $O/classify.txt
$HERE/probe.sh $T $IMG $P $ROOT
python3 -I $HERE/probe_summary.py $O/aux_probe.out -v > $O/probe_summary.txt
echo PIPELINE_DONE
