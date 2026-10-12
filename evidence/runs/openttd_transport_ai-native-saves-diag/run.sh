#!/bin/bash
set -x
J=seededge/edgebench.judge.openttd_transport_ai@sha256:27167956fd001115b0f6bb3e39e2e220ecd84e053dc3624d2fc3bc07bc9fc09c
WI=seededge/edgebench.work.openttd_transport_ai@sha256:8c1921e643eda26524123b772dd3b6c637566f39f4dddb99ccea6db3e68627e0
nproc; date -u
docker pull -q $J; docker pull -q $WI
docker create --name wk $WI true; mkdir -p /job/sub; docker cp wk:/home/workspace/openttd_ai/my_ai /job/sub/; docker rm wk
docker create --name jd --network none --memory 6g -v /job/out:/out -v /job/diag1.py:/diag1.py:ro $J sleep 7200
docker start jd
docker exec jd rm -rf /home/workspace/openttd_ai/my_ai; docker cp /job/sub/my_ai jd:/home/workspace/openttd_ai/my_ai
X="docker exec -w /home/workspace/openttd_ai jd"
$X cat /usr/local/lib/python3.10/site-packages/openttdlab.py > /job/out/openttdlab.py
$X sha256sum /usr/local/lib/python3.10/site-packages/openttdlab.py > /job/out/openttdlab.sha256
$X timeout 900 python3 /diag1.py > /job/out/diag1.txt 2>&1
echo "exit=$?" >> /job/out/diag1.txt
docker rm -f jd
date -u
