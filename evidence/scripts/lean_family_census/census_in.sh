#!/usr/bin/env bash
# Runs INSIDE the pinned judge image (read-only mount /ebv, output /out). Args: <project dir name>
set -uo pipefail
P="$1"; JR=/home/workspace/judge/se-bmk-intern; J=$JR/$P
echo "== layout"; ls -la /home/workspace /home/workspace/judge/se-bmk-intern $J 2>&1 | head -80
ls -la /home/workspace/baseline 2>&1 | head; ls /home/workspace/se-bmk-intern 2>&1 | head
echo "== toolchain"; cat $J/lean-toolchain; (cd $J && lean --version) 2>&1
echo "== hashes"
sha256sum $JR/eval_lean.py $J/ListDeclAxiom.lean $J/lakefile.* $J/lake-manifest.json /home/workspace/baseline/lake-manifest.json $JR/task/*.json 2>/dev/null
find / -xdev -name 'ListDeclAxiom.lean' -not -path '*/proc/*' 2>/dev/null | xargs -r sha256sum
echo "== HASH lines in helper"; grep -n 'HASH\|modulePrefix\|startsWith\|hashTargets\|targets' $J/ListDeclAxiom.lean | head -30
cp $J/ListDeclAxiom.lean /out/ListDeclAxiom.effective.lean; cp $JR/eval_lean.py /out/eval_lean.effective.py
cp $JR/task/*.json /out/ 2>/dev/null || true
for c in sorry_state.json baseline_sorry.json ListDeclAxiom.out ListDeclAxiom.txt list_decl_axiom.out list_decl_axiom.txt bad_decls.txt; do [ -e $J/$c ] && echo "baseline candidate present: $c"; done
echo "== baseline listing $(date -u +%T)"
( cd $J && lake build ListDeclAxiom > /out/baseline-ListDeclAxiom.out 2> /out/baseline-ListDeclAxiom.err ); echo "listing rc=$?"
tail -25 /out/baseline-ListDeclAxiom.err
echo "== lines: BAD=$(grep -c 'BAD ' /out/baseline-ListDeclAxiom.out) OK=$(grep -c 'OK ' /out/baseline-ListDeclAxiom.out) HASH=$(grep -c 'HASH ' /out/baseline-ListDeclAxiom.out)"
grep 'HASH ' /out/baseline-ListDeclAxiom.out | head
echo "== control eval (unmodified baseline as current) $(date -u +%T)"
if [ "$P" = FltRegular ]; then
  ( cd $JR && timeout 3600 python3 eval_lean.py --current-repo $J --mode weighted --weights $JR/task/FltRegular_weight.json > /out/control_report.json 2>/out/control_report.err ); echo "eval rc=$?"
else
  ( cd $JR && timeout 3600 python3 eval_lean.py --baseline-repo $J --current-repo $J > /out/control_report.json 2>/out/control_report.err ); echo "eval rc=$?"
fi
python3 - <<'PY'
import json
try:
    s=open('/out/control_report.json').read(); i=s.find('{'); r=json.loads(s[i:s.rfind('}')+1])
    print('control score', r.get('score'), r.get('summary'))
except Exception as e: print('control parse failed', e)
PY
echo "== done $(date -u +%T)"
