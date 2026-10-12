#!/bin/bash
# Good-faith control: ORIGINAL eval_treants_forest.py (WORK_DIR rewritten only) + ORIGINAL tester
# (orig/treant_tester, from treant-selected-source.tar.gz sha256 264e1699...) + shipped 50 cases
# + shipped baseline solution.py. Observed 2026-10-11: TOTAL_SCORE 3418, CASES_OK 50/50, <1 s.
# Usage: bash run_treant_baseline.sh <cases_dir> <shipped_solution.py> <orig_eval_treants_forest.py>
set -e
H=$(cd "$(dirname "$0")" && pwd); T=$(mktemp -d)
mkdir -p $T/w/tools/bin; cp -r "$1" $T/w/cases; cp $H/orig/treant_tester $T/w/tools/bin/tester
cp $H/orig/treant_gen $T/w/tools/bin/gen; chmod 755 $T/w/tools/bin/*; cp "$2" $T/w/solution.py
sed "s|^WORK_DIR = \"/home/workspace/treants_forest\"|WORK_DIR = \"$T/w\"|" "$3" > $T/eval.py
(cd $T/w && timeout 300 python3 $T/eval.py | grep -E "TOTAL_SCORE|CASES_OK|CASES_TOTAL")
rm -rf $T
