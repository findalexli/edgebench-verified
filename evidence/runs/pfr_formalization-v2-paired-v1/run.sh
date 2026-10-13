#!/usr/bin/env bash
# pfr_formalization-v2 paired run, ORIGINAL grader (v1): starter, T, D, BAD on the pinned judge image.
set -u; cd /job; OUT=/job/out; mkdir -p $OUT
JUDGE=seededge/edgebench.judge.pfr_formalization@sha256:07b51e8e10011654f0c0f79326bb66da05f1e6e2a88b35d0f1418af81d509cc4
date -u +%FT%TZ > $OUT/started
docker pull -q $JUDGE > $OUT/pull.log 2>&1 || { echo PULL_FAILED; exit 2; }
for B in $(find / -xdev -type d -path '*content.v1.content/blobs/sha256' 2>/dev/null); do find $B -type f -size +50M -delete; done
df -h / > $OUT/df.txt
bash /job/grade_variants.sh $JUDGE v1 $OUT
date -u +%FT%TZ > $OUT/finished
