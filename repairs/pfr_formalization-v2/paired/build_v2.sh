#!/usr/bin/env bash
# pfr_formalization-v2 build: inside the original judge image, (1) replay the v1 baseline listing,
# (2) install the fixed PFR/WeakPFR.lean, rebuild with the task's own tooling (`lake build
# ListDeclAxiom`, then `lake build`), record every file the rebuild rewrote and pack them,
# (3) run the type probe on the fixed baseline. Offline, --memory 6g.
set -u; cd /job; OUT=/job/out; mkdir -p $OUT
JUDGE=seededge/edgebench.judge.pfr_formalization@sha256:07b51e8e10011654f0c0f79326bb66da05f1e6e2a88b35d0f1418af81d509cc4
docker pull -q $JUDGE > $OUT/pull.log 2>&1 || { echo PULL_FAILED; exit 2; }
docker image inspect --format '{{.Id}} {{.RepoDigests}}' $JUDGE > $OUT/image_id.txt
sha256sum WeakPFR.v2.lean > $OUT/input_sha.txt
docker run --rm --network none --memory 6g --cpus 4 -v /job:/jobin:ro -v $OUT:/out --entrypoint bash $JUDGE -c '
set -u
J=/home/workspace/judge/se-bmk-intern/pfr; cd $J
lean --version > /out/lean-version.txt; git -C .lake/packages/mathlib rev-parse HEAD >> /out/lean-version.txt 2>&1
echo "=== v1 listing $(date -u +%T)"; ( lake build ListDeclAxiom ) > /out/v1-listing.raw 2>&1; echo "rc=$?"
grep -E "^(OK|BAD) |^SUMMARY|HASH" /out/v1-listing.raw > /out/v1-listing.txt
touch /tmp/marker; sleep 1
cp /jobin/WeakPFR.v2.lean PFR/WeakPFR.lean
echo "=== v2 ListDeclAxiom $(date -u +%T)"; ( lake build ListDeclAxiom ) > /out/v2-listing.raw 2>&1; echo "rc=$?"
grep -E "^(OK|BAD) |^SUMMARY|HASH" /out/v2-listing.raw > /out/v2-listing.txt
echo "=== v2 lake build $(date -u +%T)"; ( lake build ) > /out/v2-lakebuild.raw 2>&1; echo "rc=$?"
echo "=== v2 ListDeclAxiom replay $(date -u +%T)"; ( lake build ListDeclAxiom ) > /out/v2-listing-replay.raw 2>&1; echo "rc=$?"
grep -E "^(OK|BAD) |^SUMMARY|HASH" /out/v2-listing-replay.raw > /out/v2-listing-replay.txt
( cd / && find $J -path $J/.lake/packages -prune -o -type f -newer /tmp/marker -print | sed "s|^/||" | sort > /out/changed.txt )
( cd / && tar --numeric-owner -cf /out/v2-build-artifacts.tar -T /out/changed.txt )
( cd / && while read f; do sha256sum "$f"; done < /out/changed.txt ) > /out/changed.sha256
echo "=== probe $(date -u +%T)"
cp /jobin/names.txt /out/names.txt
cp /jobin/EbvProbe.lean /tmp/EbvProbe.lean
timeout 1800 lake env lean /tmp/EbvProbe.lean > /out/probe_v2.out 2>&1; echo "probe rc=$?"
grep EBV /out/probe_v2.out | grep -v "  pp=" | cut -c1-260
echo "=== done $(date -u +%T)"'
echo "container rc=$?"
ls -la $OUT
