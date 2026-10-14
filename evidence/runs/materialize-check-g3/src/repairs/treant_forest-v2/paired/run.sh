#!/bin/bash
# Paired evaluation for treant_forest v2 (anchors-only repair). Runs the ORIGINAL eval_cmd
# with --network none in (a) the original judge image (v1) and (b) the image built from the
# v2 Dockerfile (FROM-only, so it must give identical raw scores). Normalization under v1/v2
# anchors is done afterwards with sforge/harness/score_rescale.py (normalize.py).
set -x
J=seededge/edgebench.judge.treant_forest@sha256:783e9ca24139ac6aa672ec0576b5f75648e8ad47c0d937988deeb41b639bf21a
mkdir -p /job/out; nproc; free -m; date -u
docker pull -q $J
docker image inspect $J --format '{{.Id}} {{.Config.User}} {{.Config.WorkingDir}}' > /job/out/judge_image.txt
docker build -q -t treant_forest_v2 -f /job/Dockerfile /job/empty_ctx > /job/out/v2_build.txt 2>&1
docker image inspect treant_forest_v2 --format '{{.Id}}' >> /job/out/v2_build.txt
for IMG in v1 v2; do
  [ $IMG = v1 ] && I=$J || I=treant_forest_v2
  for S in baseline honest_greedy invalid_revealed; do
    docker rm -f jd 2>/dev/null
    docker create --name jd --network none --memory 4g --cpus 8 $I sleep 3600
    docker start jd
    docker cp /job/subs/$S/solution.py jd:/home/workspace/treants_forest/solution.py
    docker exec jd bash -c 'cd /home/workspace/treants_forest && sha256sum /tmp/eval_treants_forest.py tools/bin/tester solution.py && (cd cases && sha256sum * | sha256sum) && ls -la tools/bin' > /job/out/pins_${IMG}_${S}.txt 2>&1
    T0=$(date +%s)
    docker exec jd bash -c 'cd /home/workspace/treants_forest && python3 /tmp/eval_treants_forest.py' > /job/out/eval_${IMG}_${S}.txt 2>&1
    echo "exit=$? wall_s=$(( $(date +%s) - T0 ))" > /job/out/status_${IMG}_${S}.txt
    docker rm -f jd
  done
done
date -u
