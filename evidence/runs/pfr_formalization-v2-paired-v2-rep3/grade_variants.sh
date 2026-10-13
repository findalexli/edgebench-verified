#!/usr/bin/env bash
# grade_variants.sh IMAGE VERSION OUTDIR: run the task's judge.eval_cmd in IMAGE on the paired
# submissions starter, T, D, BAD (built by make_variant.py from the image's own starter
# PFR/WeakPFR.lean). One container, offline, --memory 6g --cpus 4. The submission tree is the
# judge repo's sources (identical to the work-image starter for every PFR/*.lean, checked by sha256)
# with .lake removed before each variant.
# Disk deviation (E2B workers have ~7 GB free after the 14.7 GB image): when less than 8.5 GB is
# free, only the eval_cmd's `cp -r <judge>/.lake .` is replaced by copying .lake/build and
# symlinking the read-only, already built .lake/packages. Every other eval_cmd step is verbatim.
set -u
IMAGE=$1; VERSION=$2; OUT=$3; HERE=$(cd "$(dirname "$0")" && pwd)
mkdir -p $OUT
python3 -c "import json;print(json.load(open('$HERE/task.json'))['judge']['eval_cmd'])" > $OUT/eval_cmd.txt
AV=$(df --output=avail -k / | tail -1)
if [ $AV -lt 8500000 ]; then
  echo "MODE=symlinked-packages avail_kb=$AV" > $OUT/mode.txt
  sed -i 's#cp -r /home/workspace/judge/se-bmk-intern/pfr/.lake \.#mkdir -p .lake \&\& cp -r /home/workspace/judge/se-bmk-intern/pfr/.lake/build .lake/ \&\& ln -s /home/workspace/judge/se-bmk-intern/pfr/.lake/packages .lake/packages#' $OUT/eval_cmd.txt
else echo "MODE=verbatim avail_kb=$AV" > $OUT/mode.txt; fi
docker image inspect --format '{{.Id}}' $IMAGE > $OUT/image_id.txt
docker run --rm --network none --memory 6g --cpus 4 -v $HERE:/jobin:ro -v $OUT:/out --entrypoint bash $IMAGE -c '
set -u
V='$VERSION'
EVAL=$(cat /out/eval_cmd.txt)
SUB=/home/workspace/se-bmk-intern/pfr; J=/home/workspace/judge/se-bmk-intern/pfr; F=PFR/WeakPFR.lean
sha256sum $J/$F /home/workspace/judge/se-bmk-intern/eval_lean.py $J/ListDeclAxiom.lean > /out/judge_files.sha256
mkdir -p $SUB; ( cd $J && tar c --exclude=./.lake . ) | ( cd $SUB && tar x )
for v in starter T D BAD; do
  echo "=== $V $v $(date -u +%T)"
  rm -rf $SUB/.lake; cp $J/$F $SUB/$F
  python3 /jobin/make_variant.py $V $v $SUB/$F
  cp $SUB/$F /out/WeakPFR_${V}_$v.lean.sub
  diff -u $J/$F $SUB/$F > /out/submission_${V}_$v.diff
  T0=$(date +%s)
  bash -c "$EVAL" > /out/report_${V}_$v.json 2> /out/build_${V}_$v.err; echo "eval_cmd rc=$? secs=$(( $(date +%s) - T0 ))"
  python3 - /out/report_${V}_$v.json <<PY
import json, sys
s = open(sys.argv[1]).read(); i = s.find(">>>>> Start"); j = s.find("{", i if i >= 0 else 0)
try:
    r = json.loads(s[j:s.rfind("}") + 1]); print("SCORE", "$V", "$v", r["score"], r["summary"])
except Exception as e:
    print("SCORE", "$V", "$v", "no-json", e)
PY
  ( cd $SUB && lake build ListDeclAxiom 2>/dev/null > /out/listdecl_${V}_$v.txt ) || echo "listdecl rc=$?"
  grep -E "^(OK|BAD) (ebv_|PFR_projection|torsion_free_doubling|torsion_dist_shrinking|app_ent_PFR)" /out/listdecl_${V}_$v.txt | sed -E "s/ : type=.*; (unexpected|axioms)=/ \1=/" | cut -c1-200
  grep -E "SUMMARY|HASH" /out/listdecl_${V}_$v.txt
done
echo "=== done $(date -u +%T)"'
echo "container rc=$?"
