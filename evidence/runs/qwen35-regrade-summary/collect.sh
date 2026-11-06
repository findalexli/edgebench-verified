#!/bin/bash
# collect.sh JOBDIR: require status exit=0, grade raw captures to derived.json with sforge's grade_output,
# then move raw captures (third-party submission outputs) out of the repository into .internal/.
set -eu
R=/home/alex/edgebench-verified; J=$(cd "$1" && pwd); O=$J/result/out; N=$(basename $J)
grep -qE "\"status\": \"exit=(0${ALLOW_124:+|124})\"" $J/result/worker.json || { echo "$N NOT exit=0: $(grep status $J/result/worker.json)"; exit 1; }
[ -d $O/raw ] || { echo "$N no raw"; exit 1; }
/home/alex/agentsmd-rl/.venv/bin/python $R/evidence/runs/qwen35-regrade-summary/grade.py $R $O/raw $O/derived.json
I=$R/.internal/qwen35-regrade/$N; mkdir -p $I
mv $O/raw $I/raw; mv $J/result/out.tar.gz $I/ 2>/dev/null || true
rm -rf $J/pkg $J/ebv
echo "$N collected: $(grep -c '"version"' $O/derived.json) gradings; $(grep -c skipped $O/progress.txt || true) skipped; $(grep -c missing $O/progress.txt || true) missing"
