#!/usr/bin/env bash
# Score honest variants of Section_4_1 with the UNMODIFIED judge grader (eval_lean.py + in-image
# ListDeclAxiom.lean) in the pinned judge image. One container, no network, 4 GB, 2 CPUs, removed after.
# Deviation from eval_cmd (documented): the submission repo is a copy of the judge baseline repo
# (same sources/oleans, Mathlib packages symlinked) instead of `cp -r /home/workspace/baseline/.lake`,
# so `lake build` is incremental (only Section_4_1 and its dependents rebuild) instead of a full rebuild.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
IMG=seededge/edgebench.judge.lean_analysis_proofs@sha256:41ece9c40d197540af701c6a9bd592101126708c3f3c46e8f6b0da531597513b
VARIANTS="${VARIANTS:-orig T S}"
timeout 10800 docker run --rm --network none --memory 4g --cpus 2 -e VARIANTS="$VARIANTS" \
  -v "$HERE":/ebv:ro -v "$HERE/out":/out --entrypoint bash "$IMG" -lc '
set -euo pipefail
J=/home/workspace/judge/se-bmk-intern/analysis
SUB=/home/workspace/se-bmk-intern/analysis
mkdir -p $SUB/.lake
cd $J && for f in *; do cp -a "$f" $SUB/; done
cp -a $J/.lake/build $SUB/.lake/build
ln -s $J/.lake/packages $SUB/.lake/packages
sha256sum $J/ListDeclAxiom.lean $J/../eval_lean.py $J/Analysis/Section_4_1.lean | tee /out/hashes.txt
for v in $VARIANTS; do
  echo "=== variant $v $(date -u +%T)"
  if [ "$v" = orig ]; then cp $J/Analysis/Section_4_1.lean $SUB/Analysis/Section_4_1.lean; else cp /ebv/Section_4_1.$v.lean $SUB/Analysis/Section_4_1.lean; fi
  sha256sum $SUB/Analysis/Section_4_1.lean
  ( cd $SUB && lake build 2>&1 | grep -E "error|Built|Build completed|Section_4_1" | grep -v "declaration uses" | tail -15 )
  cp $J/ListDeclAxiom.lean $SUB/
  ( cd /home/workspace/judge/se-bmk-intern && python3 eval_lean.py --baseline-repo $J --current-repo $SUB > /out/report_$v.json 2>/out/report_$v.err ) || echo "eval rc=$?"
  ( cd $SUB && lake build ListDeclAxiom 2>/dev/null | grep -E "(OK|BAD) Section_4_1\." > /out/listdecl_S41_$v.txt ) || true
  wc -l /out/listdecl_S41_$v.txt
  echo "=== done $v $(date -u +%T)"
done'
