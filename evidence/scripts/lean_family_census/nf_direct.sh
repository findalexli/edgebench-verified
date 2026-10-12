#!/usr/bin/env bash
# new_foundations_consistency: `lake build ListDeclAxiom` fails offline in the shipped judge image (Lake sees
# doc-gen4 with no origin remote and HEAD 0ee5b43 != manifest 86d735ec, deletes it and tries to clone).
# Setup correction (one attempt): bypass Lake and run the SAME in-image helper with plain `lean` and a LEAN_PATH
# made of the already-built oleans. Then the same aux probe. Grader scoring itself is applied offline by classify.py.
set -uo pipefail
exec 9>/tmp/ebv-heavy.lock && flock -w 7200 9 || { echo "LOCK TIMEOUT"; exit 5; }
HERE="$(cd "$(dirname "$0")" && pwd)"; O=$HERE/out/new_foundations_consistency
IMG=seededge/edgebench.judge.new_foundations_consistency@sha256:c17cd5656a55f6797ea47703ebe05591b2e074fa321e4eb1dd6d52ec78e96cc4
timeout 5400 docker run --rm --network none --memory 4g --cpus 2 -v "$O":/out -v "$HERE":/ebv:ro --entrypoint bash "$IMG" -c '
set -uo pipefail
cd /home/workspace/judge/se-bmk-intern/con-nf
LP=$(pwd)/.lake/build/lib/lean; for p in .lake/packages/*; do LP=$LP:$(pwd)/$p/.lake/build/lib/lean; done
export LEAN_PATH=$LP
ls .lake/build/lib/lean | head; ls .lake/build/lib/lean/ListDeclAxiom* 2>&1 | head -3
echo "== direct listing $(date -u +%T)"
lean ListDeclAxiom.lean > /out/baseline-ListDeclAxiom.direct.out 2> /out/baseline-ListDeclAxiom.direct.err; echo "lean rc=$?"
tail -5 /out/baseline-ListDeclAxiom.direct.err
echo "BAD=$(grep -c "BAD " /out/baseline-ListDeclAxiom.direct.out) OK=$(grep -c "OK " /out/baseline-ListDeclAxiom.direct.out) HASH=$(grep -c "HASH " /out/baseline-ListDeclAxiom.direct.out)"
python3 /ebv/classify.py /out/baseline-ListDeclAxiom.direct.out -v > /out/classify.txt
grep -oE "^  AUX \S+" /out/classify.txt | awk "{print \$2}" > /out/aux_targets.txt
sed "s/@ROOT@/ConNF/" /ebv/AuxProbe.lean.tmpl > EbvAuxProbe.lean
echo "== probe $(date -u +%T)"; lean EbvAuxProbe.lean > /out/aux_probe.out 2>&1; echo "probe rc=$?"
echo "== done $(date -u +%T)"'
