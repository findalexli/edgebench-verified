#!/usr/bin/env bash
# Paired v1/v2 evaluation for lean_analysis_proofs-v2, run LOCALLY in ONE container of the pinned
# judge image (already local; nothing pulled). --network none, 4 GB, 2 CPUs, removed afterwards.
#
# Inside the container:
#   1. V1 = relocated copy of the untouched judge baseline repo (sources + .lake/build, Mathlib
#      packages symlinked) plus the untouched eval_lean.py.  Its ListDeclAxiom listing = v1 targets.
#   2. The v2 change (files/judge/...) is applied IN PLACE at the original judge path and
#      `lake build ListDeclAxiom` regenerates the baseline listing with the task's own tooling.
#      Every build artifact this rewrites is exported as out/v2-build-artifacts.tar (the Dockerfile
#      COPYs exactly these files).
#   3. EbvV2Proofs.lean: corrected statements typecheck and are proved (axioms printed).
#   4. Grader runs: each variant is overlaid on the version's own starter in a submission repo at
#      the eval_cmd path; `lake build`; copy ListDeclAxiom.lean; `python3 eval_lean.py
#      --baseline-repo <judge repo> --current-repo <submission>` (eval_cmd steps).
# Documented deviation from eval_cmd: the submission repo starts from the judge repo's prebuilt
# .lake/build (incremental build, judge-repo Mathlib 491a409) instead of `cp -r
# /home/workspace/baseline/.lake` (Mathlib 3203991, full rebuild).  v1 runs use the relocated V1
# copy as --baseline-repo.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
PKG="$(cd "$HERE/.." && pwd)"
IMG=seededge/edgebench.judge.lean_analysis_proofs@sha256:41ece9c40d197540af701c6a9bd592101126708c3f3c46e8f6b0da531597513b
CASES="${CASES:-v1:orig v2:orig v1:A v2:A v1:BAD v2:BAD v1:T v2:T v1:S v2:S v1:W v2:W}"
mkdir -p "$HERE/out"
# Machine-wide heavy-job lock (BRIEF HARD RULE).
exec 9>/tmp/ebv-heavy.lock && flock -w 7200 9
RESUME="${RESUME:-0}"
timeout 14400 docker run --rm --network none --memory 4g --cpus 2 -e CASES="$CASES" -e RESUME="$RESUME" \
  -v "$PKG/files":/v2files:ro -v "$HERE/variants":/variants:ro -v "$HERE/lean":/lean:ro \
  -v "$HERE/out":/out --entrypoint bash "$IMG" -lc '
set -euo pipefail
JE=/home/workspace/judge/se-bmk-intern; J=$JE/analysis
V1E=/home/workspace/v1judge/se-bmk-intern; V1=$V1E/analysis
SUBP=/home/workspace/se-bmk-intern; SUB=$SUBP/analysis
ts() { date -u +%T; }
( cd $J && lean --version && cat lean-toolchain ) | tee /out/lean-version.txt
# ---- 1. v1 copy
mkdir -p $V1/.lake
( cd $J && for f in *; do cp -a "$f" $V1/; done )
cp -a $J/.lake/build $V1/.lake/build; ln -s $J/.lake/packages $V1/.lake/packages
cp -a $JE/eval_lean.py $V1E/eval_lean.py
echo "[$(ts)] v1 listing"
( cd $V1 && lake build ListDeclAxiom ) > /out/v1-listing.raw 2>&1
grep -E "^(OK|BAD) |^SUMMARY" /out/v1-listing.raw > /out/v1-listing.txt || true
tail -2 /out/v1-listing.raw
if [ "$RESUME" = 1 ]; then
  # Resume after host OOM restart: install v2 exactly as the Dockerfile does (eval_lean.py +
  # ADD of the saved artifact tar) and check that Lake treats it as up to date.
  cp /v2files/judge/eval_lean.py $JE/eval_lean.py
  tar -xf /v2files/judge/v2-build-artifacts.tar -C /
  echo "[$(ts)] resume: listing from installed v2 artifacts"
  ( cd $J && lake build ListDeclAxiom ) > /tmp/v2r.raw 2>&1
  grep -E "^(OK|BAD) |^SUMMARY" /tmp/v2r.raw > /out/v2-listing.resume.txt || true
  echo "rebuilt modules on resume: $(grep -cE "Built Analysis|Built ListDeclAxiom" /tmp/v2r.raw || true)"
  cmp /out/v2-listing.txt /out/v2-listing.resume.txt && echo "resume listing identical to regenerated v2 listing"
else
# ---- 2. apply v2 in place and regenerate
sha256sum $J/Analysis/Section_11_2.lean $J/Analysis/Section_11_3.lean $JE/eval_lean.py $J/ListDeclAxiom.lean > /out/hashes-v1-inimage.txt
touch /tmp/marker; sleep 1
cp /v2files/judge/analysis/Analysis/Section_11_2.lean /v2files/judge/analysis/Analysis/Section_11_3.lean $J/Analysis/
cp /v2files/judge/eval_lean.py $JE/eval_lean.py
sha256sum $J/Analysis/Section_11_2.lean $J/Analysis/Section_11_3.lean $JE/eval_lean.py > /out/hashes-v2-applied.txt
echo "[$(ts)] v2 rebuild + listing"
( cd $J && lake build ListDeclAxiom ) > /out/v2-listing.raw 2>&1
grep -E "^(OK|BAD) |^SUMMARY" /out/v2-listing.raw > /out/v2-listing.txt || true
grep -E "^. \[|Built|Build completed" /out/v2-listing.raw | grep -v Replayed | tail -30 || true
( cd $J && lake build ) > /out/v2-lakebuild-default.raw 2>&1; tail -1 /out/v2-lakebuild-default.raw
echo "[$(ts)] export rebuilt artifacts"
( cd / && find $J -path $J/.lake/packages -prune -o -type f -newer /tmp/marker -print | sed "s|^/||" | sort > /out/v2-changed-files.txt )
find $J/.lake/packages -type f -newer /tmp/marker | head > /out/v2-changed-in-packages.txt || true
( cd / && tar --numeric-owner -cf /out/v2-build-artifacts.tar -T /out/v2-changed-files.txt )
wc -l /out/v2-changed-files.txt
# ---- 3. typecheck / prove corrected statements in the v2 repo
cp /lean/EbvV2Proofs.lean $J/EbvV2Proofs.lean
( cd $J && lake env lean EbvV2Proofs.lean ) > /out/v2-proofs.out 2>&1 || echo "proof rc=$?" >> /out/v2-proofs.out
rm -f $J/EbvV2Proofs.lean
cat /out/v2-proofs.out
fi
# ---- 4. grader runs
mk_sub() { rm -rf $SUBP; mkdir -p $SUB/.lake
  ( cd $1 && for f in *; do cp -a "$f" $SUB/; done )
  cp -a $1/.lake/build $SUB/.lake/build; ln -s $J/.lake/packages $SUB/.lake/packages; }
for c in $CASES; do
  ver=${c%%:*}; var=${c#*:}
  if [ $ver = v1 ]; then BASE=$V1; EDIR=$V1E; else BASE=$J; EDIR=$JE; fi
  echo "=== [$(ts)] case $ver $var"
  mk_sub $BASE
  for f in /variants/*.$var.lean; do [ -e "$f" ] || continue
    m=$(basename $f .$var.lean); cp $f $SUB/Analysis/$m.lean; sha256sum $f; done
  set +e; ( cd $SUB && lake build ) > /out/build_${ver}_${var}.log 2>&1; brc=$?; set -e
  echo "lake build rc=$brc"; grep -E "error" /out/build_${ver}_${var}.log | grep -v "declaration uses" | head -5 || true
  if [ $brc -ne 0 ]; then echo "{\"case\":\"$c\",\"lake_build_rc\":$brc,\"eval\":\"not reached (eval_cmd uses &&)\"}" > /out/report_${ver}_${var}.json; continue; fi
  cp $BASE/ListDeclAxiom.lean $SUB/
  set +e; ( cd $EDIR && python3 eval_lean.py --baseline-repo $BASE --current-repo $SUB ) > /out/report_${ver}_${var}.json 2>/out/report_${ver}_${var}.err; erc=$?; set -e
  echo "eval rc=$erc"; grep -m1 "\"summary\"" /out/report_${ver}_${var}.json || true
done
echo "[$(ts)] all done"'
gzip -f "$HERE"/out/report_*.json "$HERE"/out/*.raw 2>/dev/null || true
