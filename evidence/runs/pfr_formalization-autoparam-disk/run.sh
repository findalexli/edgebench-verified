#!/usr/bin/env bash
# Disk check for running the PFR eval_cmd on an E2B worker (the first job's eval ran out of space).
set -u; OUT=/job/out; mkdir -p $OUT
JUDGE=seededge/edgebench.judge.pfr_formalization@sha256:07b51e8e10011654f0c0f79326bb66da05f1e6e2a88b35d0f1418af81d509cc4
df -h > $OUT/df_before.txt; docker info 2>/dev/null | grep -iE 'storage|root dir|backing' > $OUT/docker_info.txt
docker pull -q $JUDGE > $OUT/pull.log 2>&1
df -h > $OUT/df_after_pull.txt; docker system df > $OUT/docker_df.txt
docker run --rm --network none --entrypoint bash $JUDGE -c 'du -sh /home/workspace/judge/se-bmk-intern/pfr/.lake /home/workspace/judge/se-bmk-intern/pfr/.lake/* /home/workspace/judge/se-bmk-intern/pfr/.lake/packages/* 2>&1; df -h / /tmp' > $OUT/du.txt 2>&1
lsblk > $OUT/lsblk.txt 2>&1; free -g > $OUT/free.txt
