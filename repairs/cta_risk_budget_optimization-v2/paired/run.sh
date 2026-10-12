#!/bin/bash
# Paired v1/v2 evaluation for cta_risk_budget_optimization-v2 (E2B worker, root, /job), --network none.
set -uo pipefail
V1=seededge/edgebench.judge.cta_risk_budget_optimization@sha256:34258d854f41e9cd5fc179fadbc6348bb8ff4118506b1862273f2a2a6d941b32
V2=ebv/cta_risk_budget_optimization:v2
O=/job/out; mkdir -p $O/logs
nproc > $O/env.txt; free -m >> $O/env.txt
docker pull $V1 > $O/pull.log 2>&1 || { echo pull-failed; exit 2; }
docker build -t $V2 /job/pkg > $O/build.log 2>&1 || { echo build-failed; exit 3; }
docker image inspect $V2 --format '{{.Id}}' > $O/v2_image_id.txt
for v in v1 v2; do img=$V1; [ $v = v2 ] && img=$V2
  docker run --rm --network none --entrypoint bash $img -c 'sha256sum /home/workspace/scoring/eval_script.py; ls -l /home/workspace/scoring/eval_script.py' > $O/eval_sha-$v.txt
  # 1+2. mixed-currency trigger and same-currency / over-limit controls (installed evaluator, cross-border block)
  timeout 600 docker run --rm --network none --memory 2g --cpus 2 -v /job/tools:/s:ro --entrypoint python3 $img -I /s/repro_cross_border.py > $O/logs/fixtures-$v.log 2>&1; echo "fixtures $v exit=$?" | tee -a $O/summary.txt
  # 3. shipped reference positions through the installed cross-border block
  timeout 600 docker run --rm --network none --memory 2g --cpus 2 -v /job/tools:/s:ro --entrypoint python3 $img -I /s/reference_block.py > $O/logs/refblock-$v.log 2>&1; echo "refblock $v exit=$?" | tee -a $O/summary.txt
  # 4. full original eval_cmd on the complete shipped standard-answer submission
  timeout 900 docker run --rm --network none --memory 3g --cpus 2 --entrypoint bash $img -c 'cd /home/workspace && tar -xzf scoring/standard_answer_artifacts.tar.gz -C /home/workspace && cd /home/workspace && python3 scoring/score.py' > $O/logs/fullref-$v.log 2>&1
  echo "fullref $v exit=$? $(grep -E '^TOTAL_SCORE' $O/logs/fullref-$v.log | tr '\n' ' ')" | tee -a $O/summary.txt
done
docker image rm $V2 >/dev/null 2>&1; echo done >> $O/summary.txt
