#!/usr/bin/env bash
# pfr_formalization-v2 paired run, FIXED grader (v2). The package is rebuilt from scratch on the
# worker: materialize.sh (pull pinned images, extract, apply repair.patch, rebuild the judge build
# artifacts inside the original image, verify every sha256 and the regenerated listing), then
# `docker build` of the package Dockerfile, then the same submissions as the v1 job.
set -u; cd /job; OUT=/job/out; mkdir -p $OUT
JUDGE=seededge/edgebench.judge.pfr_formalization@sha256:07b51e8e10011654f0c0f79326bb66da05f1e6e2a88b35d0f1418af81d509cc4
WORK=seededge/edgebench.work.pfr_formalization@sha256:3be95d28524d9bad61f82306b6448fe3d0fc2dff66fd285d62bfa057bf047c86
date -u +%FT%TZ > $OUT/started
delblobs() { for B in $(find / -xdev -type d -path '*content.v1.content/blobs/sha256' 2>/dev/null); do find $B -type f -size +50M -delete; done; }
docker pull -q $JUDGE > $OUT/pull_judge.log 2>&1 || { echo PULL_FAILED; exit 2; }; delblobs; df -h / | tail -1
echo "=== materialize $(date -u +%T)"
# attempt 2 stopped here: the worker template has no GNU patch (needed by materialize.sh).
command -v patch >/dev/null || { (apt-get update -qq && apt-get install -y -qq patch) > $OUT/apt_patch.log 2>&1; }
patch --version | head -1
# Deviation (disk): the work image (~11 GB on disk) and the judge image (~12 GB) do not fit together
# on a 21 GB worker (attempt 1, result-attempt1-disk/). materialize.sh's only use of the work image is
# a CHECK that its starter WeakPFR.lean has the locked sha256; that was verified separately
# (pfr_formalization-v2-extract). Here a copy of materialize.sh with the work-image lines removed runs.
grep -v '^  "work|' pkg/materialize.sh > pkg/materialize.nowork.sh; chmod +x pkg/materialize.nowork.sh
diff pkg/materialize.sh pkg/materialize.nowork.sh > $OUT/materialize.nowork.diff
( cd pkg && EBV_HEAVY_LOCK=/tmp/ebv-heavy.lock ./materialize.nowork.sh ) > $OUT/materialize.log 2>&1; RC=$?; echo "materialize rc=$RC"; [ $RC = 0 ] || { tail -20 $OUT/materialize.log; exit 3; }
tail -5 $OUT/materialize.log
( cd pkg && find files orig -type f | sort | xargs sha256sum ) > $OUT/materialized.sha256
df -h / | tail -1
echo "=== docker build $(date -u +%T)"
( cd pkg && docker build -t ebv/pfr_formalization-judge:v2 . ) > $OUT/docker_build.log 2>&1; RC=$?; echo "docker build rc=$RC"; [ $RC = 0 ] || { tail -20 $OUT/docker_build.log; exit 4; }
tail -3 $OUT/docker_build.log
docker run --rm --network none --entrypoint bash ebv/pfr_formalization-judge:v2 -c 'cd /home/workspace/judge/se-bmk-intern/pfr && sha256sum PFR/WeakPFR.lean && lake build ListDeclAxiom 2>&1 | grep -c "Built\|Building\|Compiling"; lake build ListDeclAxiom 2>&1 | sed -E "s/^info: ListDeclAxiom\.lean:[0-9]+:[0-9]+: //" | grep -E "^(OK|BAD) |^SUMMARY|^HASH"' > $OUT/v2-image-listing.raw 2>&1
head -2 $OUT/v2-image-listing.raw; tail -n +3 $OUT/v2-image-listing.raw > $OUT/v2-image-listing.txt
cmp $OUT/v2-image-listing.txt pkg/paired/out/v2-listing.txt && echo "built image listing == saved v2 listing"
echo "=== grade $(date -u +%T)"
bash /job/grade_variants.sh ebv/pfr_formalization-judge:v2 v2 $OUT
date -u +%FT%TZ > $OUT/finished
