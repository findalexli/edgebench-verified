#!/usr/bin/env bash
# Exact eval_cmd on the unmodified starter (judge sources without .lake) and on honest variants of ONE file.
# Usage: run_native.sh <task_id> <image@digest> <variant dir> <relative path of replaced file in project>
# The variant dir holds <stem>.<V>.lean files; VARIANTS env selects (default "A B").
# The eval command is read from tasks/<task_id>.json (judge.eval_cmd) and run verbatim.
set -uo pipefail
# machine-wide heavy-job lock (BRIEF HARD RULE)
exec 9>/tmp/ebv-heavy.lock && flock -w 7200 9 || { echo "LOCK TIMEOUT"; exit 5; }
HERE="$(cd "$(dirname "$0")" && pwd)"; T=$1; IMG=$2; VD=$(cd "$3" && pwd); REL=$4; O=$HERE/out/$T/native; mkdir -p $O
EVAL=$(python3 -I -c "import json,sys;print(json.load(open(sys.argv[1]))['judge']['eval_cmd'])" $HERE/../../../tasks/$T.json)
printf '%s\n' "$EVAL" > $O/eval_cmd.txt
STEM=$(basename "$REL" .lean); export VARIANTS="${VARIANTS-A B}"
timeout 14400 docker run --rm --network none --memory 4g --cpus 2 -e VARIANTS -e REL="$REL" -e STEM="$STEM" \
  -v "$VD":/var:ro -v "$O":/out -v "$O/eval_cmd.txt":/eval_cmd.txt:ro --entrypoint bash "$IMG" -c '
set -uo pipefail
EVAL=$(cat /eval_cmd.txt)
SUB=$(echo "$EVAL" | sed -E "s/^cd ([^ ]+) .*/\1/"); J=/home/workspace/judge/se-bmk-intern/$(basename $SUB)
echo "SUB=$SUB J=$J"; mkdir -p $SUB
( cd $J && tar c --exclude=./.lake . ) | ( cd $SUB && tar x )
sha256sum $SUB/$REL /var/*.lean
for v in orig $VARIANTS; do
  echo "=== variant $v $(date -u +%T)"
  if [ $v = orig ]; then cp $J/$REL $SUB/$REL; else cp /var/$STEM.$v.lean $SUB/$REL; fi
  sha256sum $SUB/$REL
  bash -c "$EVAL" > /out/report_$v.json 2> /out/build_$v.err; echo "eval_cmd rc=$?"
  grep -E "error" /out/report_$v.json /out/build_$v.err | grep -v "declaration uses" | head -10
  python3 -c "
import json,sys
s=open(\"/out/report_$v.json\").read(); i=s.find(\">>>>> Start\"); j=s.find(\"{\", i if i>=0 else 0)
try:
  r=json.loads(s[j:s.rfind(\"}\")+1]); print(\"SCORE\", \"$v\", r[\"score\"], r[\"summary\"])
except Exception as e: print(\"no json\", e)"
  ( cd $SUB && lake build ListDeclAxiom 2>/dev/null > /out/listdecl_$v.txt ) || true
  echo "=== done $v $(date -u +%T)"
done'
echo "rc=$?"
