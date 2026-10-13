#!/bin/bash
# collect.sh JOB: grade raw captures to derived.json, then move raw captures out of the repo into .internal/
set -eu
R=/home/alex/edgebench-verified; J=$R/evidence/runs/opus55-regrade2-$1; O=$J/result/out
grep -q '"status": "exit=0"' $J/result/worker.json || { echo "$1 NOT exit=0"; cat $J/result/worker.json; exit 1; }
[ -d $O/raw ] || { echo "$1 no raw"; exit 1; }
/home/alex/agentsmd-rl/.venv/bin/python <scratchpad>/grade_rg2.py $R $O/raw $O/derived.json
I=$R/.internal/opus55-regrade2/$1; mkdir -p $I
mv $O/raw $I/raw; mv $J/result/out.tar.gz $I/ 2>/dev/null || true
rm -rf $J/pkg
echo "$1 collected: $(grep -c '"version"' $O/derived.json) gradings; $(grep -c skipped $O/progress.txt || true) skipped; $(grep -c missing $O/progress.txt || true) missing"
